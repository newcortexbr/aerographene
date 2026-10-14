#!/bin/bash
# aerographene: roda dentro do container (aerographene-builder).
# /work = workdir persistente; /aero = repo aerographene (ro).
set -euo pipefail

. /aero/build/config.sh
. /work/portablelinux/scripts/shared.sh   # funções oficiais do portablelinux

setup_paths   # _root=/work/portablelinux, _src_dir=$_root/build/src, _out_dir=$_src_dir/out/Default
# alvo de CPU (config.sh): saída em out/${AERO_OUT} (Default = avx2, preservado; Avx1 = avx1)
_out_dir="${_src_dir}/out/${AERO_OUT}"
AERO_PATCHES=/aero/patches

AERO_STATE="${_src_dir}/.aero-applied"          # cópia da série aplicada + BUILD.gn pré-march
DOMSUB_CACHE="${_root}/build/domsub-cache.tar.gz"  # originais da domain substitution (permite revert)
MTIME_SNAP="${_root}/build/aero-mtimes.tsv"
GNFILE_REL=build/config/compiler/BUILD.gn
# helium-onboarding (deps.ini do Helium, sha256 fixado); a versão entra no hash da série porque
# build/branding_strings.py reescreve o .grdp dele (Helium -> aerographene, traduções pt-BR)
ob_ver=202609160835
ob_sha=35ce782dc9534b5bff59af7937f22c90179ca9610883acb2e0d698cc6f799366
# NeverDecaf/chromium-web-store (MIT), release fixada por versão + sha256 do .crx (fatia F4)
cws_ver=1.5.5.4
cws_sha=63c075b4a25b11af2c536dad191946e8d9547f92d5b6c257b2ce4138d2996f32

_memmon=""
_ccache_on=0
on_exit() {  # monitor de memória morre mesmo se o ninja falhar (set -e)
    if [ -n "${_memmon}" ]; then kill "${_memmon}" 2>/dev/null || true; fi
    if [ "${_ccache_on}" = 1 ]; then echo "== ccache -s"; ccache -s || true; fi
}
trap on_exit EXIT

series_list() {  # $1 = dir com series; imprime os patches em ordem
    grep -v '^\s*#' "$1/series" | sed '/^\s*$/d' | while read -r p _; do echo "$p"; done
}

# hash da série própria: se mudar, a árvore é re-patcheada (incremental ou recriada; out/ é preservado)
patch_hash() {
    {
        cat "${AERO_PATCHES}/series"
        series_list "${AERO_PATCHES}" | while read -r p; do cat "${AERO_PATCHES}/${p}"; done
        echo "march=${MARCH}"
        cat /aero/build/branding_strings.py /aero/build/strings_ptbr_extra.json
        echo "onboarding=${ob_ver}"
        echo "chromium-web-store=${cws_ver}"
    } | sha256sum | cut -d' ' -f1
}

patch_files() {  # arquivos tocados pelos patches da série em $1 (relativos a src)
    series_list "$1" | while read -r p; do
        sed -nE 's#^(\+\+\+|---) (a/|b/)?([^\t ]+).*#\3#p' "$1/$p"
    done | grep -v '^/dev/null$' || true
}

full_recreate() {
    echo "== recriando a árvore (preservando out/)"
    if [ -d "${_src_dir}/out" ]; then mv "${_src_dir}/out" "${_root}/build/out.keep"; fi
    rm -rf "${_src_dir}"
    rm -f "${DOMSUB_CACHE}" "${MTIME_SNAP}"
}

# Inverso exato de fix_tool_downloading (portablelinux), que reescreve com sed arquivos já domain-substituídos:
# o revert do ungoogled confere o CRC32 do estado pós-substituição e aborta se o sed já rodou.
unfix_tool_downloading() {
    local t="${_src_dir}/tools"
    sed -i 's/commondatastorage\.googleapis\.com/commondatastorage.9oo91eapis.qjz9zk/g' \
        "${_src_dir}/build/linux/sysroot_scripts/sysroots.json" "$t/clang/scripts/update.py" "$t/clang/scripts/build.py"
    sed -i 's/chromium\.googlesource\.com/chromium.9oo91esource.qjz9zk/g' \
        "$t/clang/scripts/build.py" "$t/rust/build_rust.py" "$t/rust/build_bindgen.py"
    sed -i 's/chrome-infra-packages\.appspot\.com/chrome-infra-packages.8pp2p8t.qjz9zk/g' "$t/rust/build_rust.py"
}

# Reverte a série anterior (gravada em $AERO_STATE) em ordem inversa; ungoogled/portablelinux ficam.
# Antes: mtime+sha dos arquivos afetados; no fim, restore_mtimes devolve o mtime de quem não mudou.
# Retorna !=0 se não for possível (sem registro, sem cache de domsub, patch -R falhou): recriar.
incremental_repatch() {
    [ -f "${AERO_STATE}/series" ] && [ -f "${AERO_STATE}/BUILD.gn.orig" ] || { echo "sem registro da série aplicada"; return 1; }
    [ -f "${_src_dir}/.patched.stamp" ] || return 1
    if [ -f "${_src_dir}/.domsub.stamp" ] && [ ! -f "${DOMSUB_CACHE}" ]; then
        echo "domain substitution sem cache: revert impossível"; return 1
    fi
    {
        patch_files "${AERO_STATE}"; patch_files "${AERO_PATCHES}"; echo "${GNFILE_REL}"
        # arquivos de strings reescritos por build/branding_strings.py
        if [ -d "${AERO_STATE}/strings-orig" ]; then (cd "${AERO_STATE}/strings-orig" && find . -type f | sed 's#^\./##'); fi
        echo build/linux/sysroot_scripts/sysroots.json; echo tools/clang/scripts/update.py
        echo tools/clang/scripts/build.py; echo tools/rust/build_rust.py; echo tools/rust/build_bindgen.py
        if [ -f "${_src_dir}/.domsub.stamp" ]; then cat "${_main_repo}/domain_substitution.list"; fi
    } | sort -u > "${MTIME_SNAP}.list" || return 1
    python3 - "${_src_dir}" "${MTIME_SNAP}.list" "${MTIME_SNAP}" <<'PY' || return 1
import sys, os, hashlib
src, lst, out = sys.argv[1:]
with open(lst) as f, open(out + '.part', 'w') as o, open(out + '.exec', 'w') as ex:
    for rel in f.read().split('\n'):
        p = os.path.join(src, rel)
        if rel and os.path.isfile(p) and not os.path.islink(p):
            h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
            o.write(f"{os.stat(p).st_mtime_ns}\t{h}\t{rel}\n")
            if os.access(p, os.X_OK):
                ex.write(rel + "\n")
os.replace(out + '.part', out)
PY
    rm -f "${MTIME_SNAP}.list"
    rm -f "${_src_dir}/.aero-patches.hash"   # daqui em diante a árvore está parcial
    if [ -f "${_src_dir}/.domsub.stamp" ]; then
        echo "== revert da domain substitution"
        unfix_tool_downloading   # após o snapshot de mtimes/sha; fix_tool_downloading reaplica depois
        "${_main_repo}/utils/domain_substitution.py" revert -c "${DOMSUB_CACHE}" "${_src_dir}" || return 1
        rm -f "${DOMSUB_CACHE}" "${_src_dir}/.domsub.stamp"
    fi
    cp -p "${AERO_STATE}/BUILD.gn.orig" "${_src_dir}/${GNFILE_REL}" || return 1   # desfaz -march
    if [ -d "${AERO_STATE}/strings-orig" ]; then
        echo "== restaura .grd/.grdp/.xtb anteriores à troca de branding"
        cp -a "${AERO_STATE}/strings-orig/." "${_src_dir}/" || return 1
    fi
    echo "== patch -R da série anterior (ordem inversa)"
    local p
    while read -r p; do
        patch -R -p1 --ignore-whitespace --no-backup-if-mismatch -s -d "${_src_dir}" -i "${AERO_STATE}/${p}" </dev/null \
            || { echo "patch -R falhou: ${p}"; return 1; }
    done < <(series_list "${AERO_STATE}" | tac)
    rm -rf "${AERO_STATE}"
}

restore_mtimes() {  # só no caminho incremental
    [ -f "${MTIME_SNAP}" ] || return 0
    python3 - "${_src_dir}" "${MTIME_SNAP}" <<'PY'
import sys, os, hashlib
src, snap = sys.argv[1:]
n = 0
for line in open(snap):
    mt, h, rel = line.rstrip('\n').split('\t', 2)
    p = os.path.join(src, rel)
    if os.path.isfile(p) and not os.path.islink(p) and hashlib.sha256(open(p, 'rb').read()).hexdigest() == h:
        st = os.stat(p)
        if st.st_mtime_ns != int(mt):
            os.utime(p, ns=(st.st_atime_ns, int(mt))); n += 1
print(f"mtime restaurado em {n} arquivos sem mudança de conteúdo")
PY
    rm -f "${MTIME_SNAP}"
}

want_hash="$(patch_hash)"
have_hash="$(cat "${_src_dir}/.aero-patches.hash" 2>/dev/null || true)"
if [ -f "${_src_dir}/.downloaded.stamp" ]; then
    # árvore anterior a este registro: assume a tag atual
    [ -f "${_src_dir}/.aero-base" ] || [ -z "${have_hash}" ] || echo "${UC_TAG}" > "${_src_dir}/.aero-base"
    if [ "$(cat "${_src_dir}/.aero-base" 2>/dev/null || true)" != "${UC_TAG}" ]; then
        echo "== versão ungoogled/portablelinux mudou"; full_recreate
    elif [ -z "${have_hash}" ]; then
        # sem hash = aplicação anterior interrompida (árvore parcialmente patcheada)
        echo "== árvore parcial (sem hash)"; full_recreate
    elif [ "${want_hash}" != "${have_hash}" ]; then
        echo "== série de patches mudou: re-patch incremental"
        if ! incremental_repatch; then echo "== incremental falhou"; full_recreate; fi
    fi
fi
if [ ! -f "${_src_dir}/.downloaded.stamp" ] && [ -d "${_root}/build/out.keep" ] && [ ! -d "${_src_dir}/out" ]; then
    restore_out=1
fi

echo "== fetch (cache em ${_dl_cache})"
fetch_sources false false
[ -f "${_src_dir}/.aero-base" ] || echo "${UC_TAG}" > "${_src_dir}/.aero-base"
if [ -n "${restore_out:-}" ]; then mkdir -p "${_src_dir}"; mv "${_root}/build/out.keep" "${_src_dir}/out"; fi

echo "== pruning + patches ungoogled + portablelinux"
apply_patches

echo "== uBlock Origin (deps.ini do Helium [ublock_origin], sha256 fixado)"
# precisa existir antes dos patches: ublock-setup-sources altera manifest.json e assets/assets.json
ub_ver=1.75.0
ub_sha=49214674f7c6c474e60da647c05bd28463b1f7a55b2a2b0a53e9d297ef7bf3c6
ub_dir="${_src_dir}/third_party/ublock"
if [ ! -f "${_src_dir}/.aero-patches.hash" ] && [ ! -f "${_src_dir}/.aero-ublock-${ub_ver}" ]; then
    ub_zip="${_root}/build/ublock-origin-${ub_ver}.zip"
    [ -s "$ub_zip" ] || curl -fL --retry 3 -o "$ub_zip" \
        "https://github.com/imputnet/uBlock/releases/download/${ub_ver}/uBlock0_${ub_ver}.chromium.zip"
    echo "${ub_sha}  ${ub_zip}" | sha256sum -c -
    rm -rf "$ub_dir"; mkdir -p "$ub_dir"
    # strip_leading_dirs = uBlock0.chromium
    python3 - "$ub_zip" "$ub_dir" <<'PY'
import sys, zipfile, os
zpath, dest = sys.argv[1], sys.argv[2]
prefix = 'uBlock0.chromium/'
with zipfile.ZipFile(zpath) as z:
    for m in z.infolist():
        assert m.filename.startswith(prefix), m.filename
        rel = m.filename[len(prefix):]
        if not rel or '..' in rel.split('/'):
            continue
        out = os.path.join(dest, rel)
        if m.is_dir():
            os.makedirs(out, exist_ok=True)
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with z.open(m) as s, open(out, 'wb') as d:
            d.write(s.read())
PY
    touch "${_src_dir}/.aero-ublock-${ub_ver}"  # fora de ub_dir: generate_file_list empacota tudo lá
fi

echo "== chromium-web-store ${cws_ver} (release do GitHub, sha256 fixado)"
# como o uBlock: antes dos patches (defaults-f4 cria BUILD.gn/grit em third_party/chromium_web_store)
cws_dir="${_src_dir}/third_party/chromium_web_store"
if [ ! -f "${_src_dir}/.aero-patches.hash" ] && [ ! -f "${_src_dir}/.aero-cws-${cws_ver}" ]; then
    cws_crx="${_root}/build/chromium-web-store-${cws_ver}.crx"
    [ -s "$cws_crx" ] || curl -fL --retry 3 -o "$cws_crx" \
        "https://github.com/NeverDecaf/chromium-web-store/releases/download/v${cws_ver}/Chromium.Web.Store.crx"
    echo "${cws_sha}  ${cws_crx}" | sha256sum -c -
    rm -rf "$cws_dir"; mkdir -p "$cws_dir"
    # CRX3: "Cr24", versão (4 bytes), tamanho do cabeçalho (4 bytes), cabeçalho, depois o zip
    python3 - "$cws_crx" "$cws_dir" <<'PY'
import sys, io, struct, zipfile, os
crx, dest = sys.argv[1], sys.argv[2]
d = open(crx, 'rb').read()
assert d[:4] == b'Cr24' and struct.unpack('<I', d[4:8])[0] == 3
hlen = struct.unpack('<I', d[8:12])[0]
with zipfile.ZipFile(io.BytesIO(d[12 + hlen:])) as z:
    for m in z.infolist():
        if m.is_dir() or m.filename.startswith('/') or '..' in m.filename.split('/'):
            continue
        out = os.path.join(dest, m.filename)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with z.open(m) as s, open(out, 'wb') as f:
            f.write(s.read())
PY
    curl -fL --retry 3 -o "${cws_dir}/LICENSE" \
        "https://raw.githubusercontent.com/NeverDecaf/chromium-web-store/v${cws_ver}/LICENSE"
    touch "${_src_dir}/.aero-cws-${cws_ver}"
fi

echo "== helium-onboarding ${ob_ver} (deps.ini do Helium, sha256 fixado)"
# antes dos patches e do branding_strings.py: o .grdp dele é parte de generated_resources.grd.
# No re-patch incremental o backup de strings-orig já restaurou o .grdp original; se a versão
# mudou, o diretório é recriado aqui antes da troca.
ob_dir="${_src_dir}/components/helium_onboarding"
if [ ! -f "${ob_dir}/.aero-onboarding-${ob_ver}" ]; then
    ob_tgz="${_root}/build/helium-onboarding-${ob_ver}.tar.gz"
    [ -s "$ob_tgz" ] || curl -fL --retry 3 -o "$ob_tgz" \
        "https://github.com/imputnet/helium-onboarding/releases/download/${ob_ver}/helium-onboarding-${ob_ver}.tar.gz"
    echo "${ob_sha}  ${ob_tgz}" | sha256sum -c -
    rm -rf "$ob_dir"; mkdir -p "$ob_dir"
    tar -xzf "$ob_tgz" -C "$ob_dir"
    touch "${ob_dir}/.aero-onboarding-${ob_ver}"
fi

echo "== patches aerographene (${AERO_PATCHES}/series)"
if [ ! -f "${_src_dir}/.aero-patches.hash" ]; then
    if grep -qv '^\s*\(#.*\)\?$' "${AERO_PATCHES}/series" 2>/dev/null; then
        "${_main_repo}/utils/patches.py" apply "${_src_dir}" "${AERO_PATCHES}"
    else
        echo "série vazia"
    fi

    # -march: o GN do Chromium não tem arg para isso em x86; acrescenta à config
    # compiler_cpu_abi (vale para C/C++, asm, link LTO e Rust).
    gnfile="${_src_dir}/${GNFILE_REL}"
    # registro para o re-patch incremental: série aplicada + BUILD.gn antes do -march
    rm -rf "${AERO_STATE}"; mkdir -p "${AERO_STATE}"
    cp -p "${AERO_PATCHES}/series" "${AERO_STATE}/series"
    series_list "${AERO_PATCHES}" | while read -r p; do
        mkdir -p "${AERO_STATE}/$(dirname "$p")"; cp -p "${AERO_PATCHES}/${p}" "${AERO_STATE}/${p}"
    done
    cp -p "$gnfile" "${AERO_STATE}/BUILD.gn.orig"

    # strings da UI: Chrome/Chromium -> aerographene, com ids GRIT e .xtb reescritos (ver docs/BUILD.md)
    python3 /aero/build/branding_strings.py --src "${_src_dir}" --backup "${AERO_STATE}/strings-orig"
    python3 - "$gnfile" "$MARCH" <<'PY'
import sys
path, march = sys.argv[1], sys.argv[2]
src = open(path).read()
anchor = 'config("compiler_cpu_abi") {\n'
assert src.count(anchor) == 1, "âncora compiler_cpu_abi não encontrada"
add = (anchor + '  # aerographene: -march (ADR 0003)\n'
       '  if (current_cpu == "x64" && is_linux) {\n'
       f'    cflags = [ "-march={march}" ]\n'
       f'    ldflags = [ "-march={march}" ]\n'
       f'    rustflags = [ "-Ctarget-cpu={march}" ]\n'
       '  } else {\n    cflags = []\n    ldflags = []\n  }\n')
src = src.replace(anchor, add)
src = src.replace('  cflags = cpu_abi_cflags\n  ldflags = cpu_abi_ldflags\n',
                  '  cflags += cpu_abi_cflags\n  ldflags += cpu_abi_ldflags\n', 1)
assert 'cflags += cpu_abi_cflags' in src, "bloco cpu_abi mudou"
open(path, 'w').write(src)
PY
    echo "${want_hash}" > "${_src_dir}/.aero-patches.hash"
fi

# versão do produto: chrome/common/aero_version.h (branding-version.patch) deve coincidir com build/config.sh
# (sempre, mesmo sem re-patch: config.sh pode mudar sem a série mudar)
grep -q "kVersion = \"${AERO_VERSION}\";" "${_src_dir}/chrome/common/aero_version.h" \
    || { echo "erro: AERO_VERSION=${AERO_VERSION} (build/config.sh) != chrome/common/aero_version.h; atualize patches/aerographene/branding-version.patch" >&2; exit 1; }

echo "== domain substitution (com cache para revert)"
if [ ! -f "${_src_dir}/.domsub.stamp" ]; then
    rm -f "${DOMSUB_CACHE}"
    "${_main_repo}/utils/domain_substitution.py" apply -r "${_main_repo}/domain_regex.list" \
        -f "${_main_repo}/domain_substitution.list" -c "${DOMSUB_CACHE}" "${_src_dir}"
    touch "${_src_dir}/.domsub.stamp"
    # o revert da domsub regrava arquivos sem o bit de execução (ex.: tools/clang/scripts/update.py)
    if [ -f "${MTIME_SNAP}.exec" ]; then
        while read -r f; do [ -f "${_src_dir}/${f}" ] && chmod +x "${_src_dir}/${f}"; done < "${MTIME_SNAP}.exec"
        rm -f "${MTIME_SNAP}.exec"
    fi
fi
fix_tool_downloading
restore_mtimes

echo "== ccache"
cc_line=""
if [ "${AEROGRAPHENE_CCACHE:-1}" = 1 ] && command -v ccache >/dev/null; then
    export CCACHE_DIR=/ccache
    ccache --set-config "max_size=${AEROGRAPHENE_CCACHE_SIZE:-40G}"
    ccache --set-config "base_dir=${_src_dir}"
    ccache --set-config hash_dir=false
    # o 154 compila C++ com clang modules (-fmodules/-fmodule-file): sem `modules` + depend_mode
    # o ccache marca ~90% das chamadas como não cacheáveis (run 37546797390)
    ccache --set-config sloppiness=time_macros,include_file_mtime,include_file_ctime,pch_defines,modules
    ccache --set-config depend_mode=true
    ccache --set-config "compiler_check=%compiler% -v"   # clang re-baixado muda mtime, não a versão
    ccache -z >/dev/null
    cc_line='cc_wrapper="ccache"'
    _ccache_on=1   # ccache -s em on_exit
    echo "ccache $(ccache --version | head -1), dir=${CCACHE_DIR}, max_size=${AEROGRAPHENE_CCACHE_SIZE:-40G}"
else
    echo "ccache desligado ou ausente"
fi

echo "== args.gn"
mkdir -p "${_out_dir}"
pgo_lines="chrome_pgo_phase=0"
if [ "${AEROGRAPHENE_PGO:-1}" = 1 ]; then
    [ -s "${_src_dir}/chrome/build/linux.pgo.txt" ] \
        || { echo "erro: PGO pedido e chrome/build/linux.pgo.txt ausente; use pgo=0 para build sem PGO" >&2; exit 1; }
    prof="$(tr -d '[:space:]' < "${_src_dir}/chrome/build/linux.pgo.txt")"
    pdir="${_root}/build/pgo"; mkdir -p "$pdir"
    if [ -s "${pdir}/${prof}" ] || curl -fL --retry 3 -o "${pdir}/${prof}.part" \
        "https://storage.googleapis.com/chromium-optimization-profiles/pgo_profiles/${prof}"; then
        [ -f "${pdir}/${prof}.part" ] && mv "${pdir}/${prof}.part" "${pdir}/${prof}"
        pgo_lines="chrome_pgo_phase=2
pgo_data_path=\"${pdir}/${prof}\""
        echo "PGO: perfil oficial ${prof}"
    else
        echo "erro: PGO pedido (AEROGRAPHENE_PGO=1) e perfil ${prof:-?} indisponível; use pgo=0 para build sem PGO" >&2
        exit 1
    fi
fi
{
    cat "${_main_repo}/flags.gn" "${_root}/flags.linux.gn" /aero/build/flags.gn
    echo "${pgo_lines}"
    [ -n "${cc_line}" ] && echo "${cc_line}"
    [ -n "${GOOGLE_API_KEY:-}" ] && echo "google_api_key=\"${GOOGLE_API_KEY}\""
    [ -n "${GOOGLE_DEFAULT_CLIENT_ID:-}" ] && echo "google_default_client_id=\"${GOOGLE_DEFAULT_CLIENT_ID}\""
    [ -n "${GOOGLE_DEFAULT_CLIENT_SECRET:-}" ] && echo "google_default_client_secret=\"${GOOGLE_DEFAULT_CLIENT_SECRET}\""
    echo "target_cpu=\"x64\""
    echo "v8_target_cpu=\"x64\""
} | sed -e 's/#.*//' -e 's/^\s*//;s/\s*$//' -e '/^$/d' \
  | awk -F= '{k=$1; gsub(/ /,"",k); if(!(k in v)) o[++n]=k; v[k]=$0} END{for(i=1;i<=n;i++) print v[o[i]]}' \
  > "${_out_dir}/args.gn.new"
# não imprime as chaves no log
sed -E 's/^(google_[a-z_]+)=.*/\1=<omitido>/' "${_out_dir}/args.gn.new"
if ! cmp -s "${_out_dir}/args.gn.new" "${_out_dir}/args.gn"; then mv "${_out_dir}/args.gn.new" "${_out_dir}/args.gn"; else rm "${_out_dir}/args.gn.new"; fi

echo "== toolchain"
for f in tools/clang/scripts/update.py tools/clang/scripts/build.py tools/rust/build_rust.py tools/rust/build_bindgen.py; do
    [ -f "${_src_dir}/${f}" ] && chmod +x "${_src_dir}/${f}"
done
# setup_toolchain faz rm -rf esbuild/ (barra final segue o symlink de uma execução anterior e tenta apagar /usr/lib).
# Move a entrada (diretório, symlink ou symlink quebrado) para um backup exclusivo, sem seguir o link e sem rm.
_esb="${_src_dir}/third_party/devtools-frontend/src/node_modules/esbuild"
if [ -e "$_esb" ] || [ -L "$_esb" ]; then
    _esb_bak="$(mktemp -d "${_esb}.aero-bak.XXXXXX")"
    mv -T -- "$_esb" "${_esb_bak}/esbuild"
fi
setup_toolchain

echo "== ícones (branding/)"
bash /aero/build/apply_branding_assets.sh "${_src_dir}" /aero/branding

echo "== gn gen"
cd "${_src_dir}"
[ -x out/Default/gn ] || ./tools/gn/bootstrap/bootstrap.py -o out/Default/gn --skip-generate-buildfiles
# o gn é compartilhado: sempre em out/Default/gn (não depende do alvo)
./out/Default/gn gen "out/${AERO_OUT}" --fail-on-unused-args
if [ "${AEROGRAPHENE_PGO:-1}" = 1 ]; then  # valor efetivo (no merge a última definição vence)
    pgo_eff="$(./out/Default/gn args "out/${AERO_OUT}" --list=chrome_pgo_phase --short)"
    [ "${pgo_eff}" = "chrome_pgo_phase = 2" ] \
        || { echo "erro: PGO pedido mas o gn resolveu '${pgo_eff}'" >&2; exit 1; }
    echo "PGO: ${pgo_eff}"
fi

if [ -z "${JOBS:-}" ] || [ "${JOBS}" = auto ]; then JOBS="$(nproc)"; fi
case "${JOBS}" in ''|*[!0-9]*|0) echo "erro: JOBS inválido: ${JOBS}" >&2; exit 1;; esac
echo "== ninja -j ${JOBS} (nproc=$(nproc), MemAvailable=$(awk '/MemAvailable/{printf "%.1f GB", $2/1048576}' /proc/meminfo))"
# monitor de memória a cada 5 min (diagnóstico de OOM/swap em travamentos)
( while sleep 300; do
    awk '/MemAvailable|SwapFree|SwapTotal/{printf "%s %.1fG ", $1, $2/1048576} END{print ""}' /proc/meminfo |
        sed "s/^/== mem $(date +%H:%M) /"
  done ) &
_memmon=$!
export NINJA_STATUS="[%f/%t %es] "
target="${NINJA_TARGET:-chrome chrome_sandbox}"
# "chrome" sozinho é a build completa com pacote: inclui chrome_sandbox (não é dependência do chrome)
if [ "${target}" = chrome ]; then target="chrome chrome_sandbox"; fi
read -r -a targets <<<"${target}"   # aceita vários alvos separados por espaço
ninja -C "out/${AERO_OUT}" -j "${JOBS}" "${targets[@]}"
kill "${_memmon}" 2>/dev/null || true
_memmon=""

if [ "${target}" != "chrome chrome_sandbox" ]; then
    echo "== alvo parcial ${target} compilado; sem pacote"
    exit 0
fi
echo "== pacote"
name="aerographene-${AERO_VERSION}-${UC_TAG}-${AERO_SHA:-local}-${AERO_CPU}-x86_64_linux"
stage="/work/dist/${name}"
rm -rf "$stage"; mkdir -p "$stage"
for f in chrome chrome_100_percent.pak chrome_200_percent.pak chrome_crashpad_handler chrome-wrapper \
         icudtl.dat libEGL.so libGLESv2.so libqt5_shim.so libqt6_shim.so libvk_swiftshader.so \
         libvulkan.so.1 locales product_logo_48.png resources.pak v8_context_snapshot.bin \
         vk_swiftshader_icd.json xdg-mime xdg-settings; do
    [ -e "out/${AERO_OUT}/$f" ] && cp -r "out/${AERO_OUT}/$f" "$stage/"
done
# sandbox setuid: alvo GN sandbox/linux:chrome_sandbox, data_dep do chrome. O Chromium procura
# <dir do binário>/chrome-sandbox e só o usa se for root:root 4755 (o PKGBUILD instala assim);
# sem ele vale o sandbox de user namespaces do kernel. O portablelinux não empacota.
if [ -f "out/${AERO_OUT}/chrome_sandbox" ]; then
    cp "out/${AERO_OUT}/chrome_sandbox" "$stage/chrome-sandbox"
else
    echo "== aviso: out/${AERO_OUT}/chrome_sandbox ausente; pacote sem chrome-sandbox" >&2
fi
# ícones hicolor do tema do app (PKGBUILD instala em /usr/share/icons/hicolor/<n>x<n>/apps/aerographene.png)
for n in 16 24 32 48 64 128 256; do
    mkdir -p "$stage/icons/hicolor/${n}x${n}/apps"
    cp "/aero/branding/png/aerographene-icon-${n}.png" "$stage/icons/hicolor/${n}x${n}/apps/aerographene.png"
done
# uBlock: o Chromium lê o schema de storage.managed do disco, em resources/ublock/ ao lado do binário
# (sem isso o log traz "Failed to parse schema for extension blockjmkbacgjkknlgpkjjiijinjdanf").
if [ -f "${_src_dir}/third_party/ublock/managed_storage.json" ]; then
    mkdir -p "$stage/resources/ublock"
    cp "${_src_dir}/third_party/ublock/managed_storage.json" "$stage/resources/ublock/"
fi
# chromium-web-store: mesmo caso (manifest tem storage.managed_schema = managed_storage.json)
if [ -f "${_src_dir}/third_party/chromium_web_store/managed_storage.json" ]; then
    mkdir -p "$stage/resources/chromium_web_store"
    cp "${_src_dir}/third_party/chromium_web_store/managed_storage.json" "$stage/resources/chromium_web_store/"
fi
# tabela de símbolos fora do pacote (~234 MB no chrome; o Helium distribui sem).
# Não muda código executado: .symtab/.strtab não são carregadas em runtime.
strip_tool=""
for t in "${_src_dir}/third_party/llvm-build/Release+Asserts/bin/llvm-strip" \
         "${_src_dir}/third_party/llvm-build/Release+Asserts/bin/llvm-objcopy" \
         "$(command -v strip || true)"; do
    [ -n "$t" ] && [ -x "$t" ] && { strip_tool="$t"; break; }
done
if [ -n "$strip_tool" ]; then
    echo "== strip com $(basename "$strip_tool")"
    for f in "$stage"/chrome "$stage"/chrome_crashpad_handler "$stage"/chrome-sandbox; do
        [ -f "$f" ] && "$strip_tool" --strip-all "$f"
    done
    for f in "$stage"/*.so "$stage"/*.so.*; do
        [ -f "$f" ] && "$strip_tool" --strip-unneeded "$f"
    done
else
    echo "== aviso: nenhum strip disponível; pacote segue com símbolos"
fi
# binário principal com nome do produto; branding completo fica para depois
ln -sf chrome "$stage/aerographene"
# só remove o tarball do mesmo alvo (avx2 e avx1 convivem em dist/)
rm -f "/work/dist/aerographene-"*"-${AERO_CPU}-x86_64_linux.tar.zst"
tar -C /work/dist -cf - "$name" | zstd -T0 -19 -o "/work/dist/${name}.tar.zst"
rm -rf "$stage"
echo "ARTIFACT=/work/dist/${name}.tar.zst"
