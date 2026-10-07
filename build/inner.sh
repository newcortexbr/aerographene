#!/bin/bash
# aerographene: roda dentro do container (aerographene-builder).
# /work = workdir persistente; /aero = repo aerographene (ro).
set -euo pipefail

. /aero/build/config.sh
. /work/portablelinux/scripts/shared.sh   # funções oficiais do portablelinux

setup_paths   # _root=/work/portablelinux, _src_dir=$_root/build/src, _out_dir=$_src_dir/out/Default
AERO_PATCHES=/aero/patches

AERO_STATE="${_src_dir}/.aero-applied"          # cópia da série aplicada + BUILD.gn pré-march
DOMSUB_CACHE="${_root}/build/domsub-cache.tar.gz"  # originais da domain substitution (permite revert)
MTIME_SNAP="${_root}/build/aero-mtimes.tsv"
GNFILE_REL=build/config/compiler/BUILD.gn

series_list() {  # $1 = dir com series; imprime os patches em ordem
    grep -v '^\s*#' "$1/series" | sed '/^\s*$/d' | while read -r p _; do echo "$p"; done
}

# hash da série própria: se mudar, a árvore é re-patcheada (incremental ou recriada; out/ é preservado)
patch_hash() {
    {
        cat "${AERO_PATCHES}/series"
        series_list "${AERO_PATCHES}" | while read -r p; do cat "${AERO_PATCHES}/${p}"; done
        echo "march=${MARCH}"
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
        echo build/linux/sysroot_scripts/sysroots.json; echo tools/clang/scripts/update.py
        echo tools/clang/scripts/build.py; echo tools/rust/build_rust.py; echo tools/rust/build_bindgen.py
        if [ -f "${_src_dir}/.domsub.stamp" ]; then cat "${_main_repo}/domain_substitution.list"; fi
    } | sort -u > "${MTIME_SNAP}.list" || return 1
    python3 - "${_src_dir}" "${MTIME_SNAP}.list" "${MTIME_SNAP}" <<'PY' || return 1
import sys, os, hashlib
src, lst, out = sys.argv[1:]
with open(lst) as f, open(out + '.part', 'w') as o:
    for rel in f.read().split('\n'):
        p = os.path.join(src, rel)
        if rel and os.path.isfile(p) and not os.path.islink(p):
            h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
            o.write(f"{os.stat(p).st_mtime_ns}\t{h}\t{rel}\n")
os.replace(out + '.part', out)
PY
    rm -f "${MTIME_SNAP}.list"
    rm -f "${_src_dir}/.aero-patches.hash"   # daqui em diante a árvore está parcial
    if [ -f "${_src_dir}/.domsub.stamp" ]; then
        echo "== revert da domain substitution"
        "${_main_repo}/utils/domain_substitution.py" revert -c "${DOMSUB_CACHE}" "${_src_dir}" || return 1
        rm -f "${DOMSUB_CACHE}" "${_src_dir}/.domsub.stamp"
    fi
    cp -p "${AERO_STATE}/BUILD.gn.orig" "${_src_dir}/${GNFILE_REL}" || return 1   # desfaz -march
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

echo "== domain substitution (com cache para revert)"
if [ ! -f "${_src_dir}/.domsub.stamp" ]; then
    rm -f "${DOMSUB_CACHE}"
    "${_main_repo}/utils/domain_substitution.py" apply -r "${_main_repo}/domain_regex.list" \
        -f "${_main_repo}/domain_substitution.list" -c "${DOMSUB_CACHE}" "${_src_dir}"
    touch "${_src_dir}/.domsub.stamp"
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
    ccache --set-config sloppiness=time_macros,include_file_mtime,include_file_ctime,pch_defines
    ccache --set-config "compiler_check=%compiler% -v"   # clang re-baixado muda mtime, não a versão
    ccache -z >/dev/null
    cc_line='cc_wrapper="ccache"'
    trap 'echo "== ccache -s"; ccache -s || true' EXIT
    echo "ccache $(ccache --version | head -1), dir=${CCACHE_DIR}, max_size=${AEROGRAPHENE_CCACHE_SIZE:-40G}"
else
    echo "ccache desligado ou ausente"
fi

echo "== args.gn"
mkdir -p "${_out_dir}"
pgo_lines="chrome_pgo_phase=0"
if [ "${AEROGRAPHENE_PGO:-1}" = 1 ]; then
    prof="$(tr -d '[:space:]' < "${_src_dir}/chrome/build/linux.pgo.txt")"
    pdir="${_root}/build/pgo"; mkdir -p "$pdir"
    if [ -s "${pdir}/${prof}" ] || curl -fL --retry 3 -o "${pdir}/${prof}.part" \
        "https://storage.googleapis.com/chromium-optimization-profiles/pgo_profiles/${prof}"; then
        [ -f "${pdir}/${prof}.part" ] && mv "${pdir}/${prof}.part" "${pdir}/${prof}"
        pgo_lines="chrome_pgo_phase=2
pgo_data_path=\"${pdir}/${prof}\""
        echo "PGO: perfil oficial ${prof}"
    else
        echo "PGO: perfil indisponível, chrome_pgo_phase=0"
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
# setup_toolchain faz rm -rf esbuild/ (barra final segue o symlink de uma execução anterior e tenta apagar /usr/lib).
# Move a entrada (diretório, symlink ou symlink quebrado) para um backup exclusivo, sem seguir o link e sem rm.
_esb="${_src_dir}/third_party/devtools-frontend/src/node_modules/esbuild"
if [ -e "$_esb" ] || [ -L "$_esb" ]; then
    _esb_bak="$(mktemp -d "${_esb}.aero-bak.XXXXXX")"
    mv -T -- "$_esb" "${_esb_bak}/esbuild"
fi
setup_toolchain

echo "== helium-onboarding (deps.ini do Helium, sha256 fixado)"
ob_ver=202609160835
ob_sha=35ce782dc9534b5bff59af7937f22c90179ca9610883acb2e0d698cc6f799366
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

echo "== gn gen"
cd "${_src_dir}"
[ -x out/Default/gn ] || ./tools/gn/bootstrap/bootstrap.py -o out/Default/gn --skip-generate-buildfiles
./out/Default/gn gen out/Default --fail-on-unused-args

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
ninja -C out/Default -j "${JOBS}" chrome
kill "${_memmon}" 2>/dev/null || true

echo "== pacote"
name="aerographene-${UC_TAG}-${AERO_SHA:-local}-x86_64_linux"
stage="/work/dist/${name}"
rm -rf "$stage"; mkdir -p "$stage"
for f in chrome chrome_100_percent.pak chrome_200_percent.pak chrome_crashpad_handler chrome-wrapper \
         icudtl.dat libEGL.so libGLESv2.so libqt5_shim.so libqt6_shim.so libvk_swiftshader.so \
         libvulkan.so.1 locales product_logo_48.png resources.pak v8_context_snapshot.bin \
         vk_swiftshader_icd.json xdg-mime xdg-settings; do
    [ -e "out/Default/$f" ] && cp -r "out/Default/$f" "$stage/"
done
# binário principal com nome do produto; branding completo fica para depois
ln -sf chrome "$stage/aerographene"
rm -f /work/dist/*.tar.zst
tar -C /work/dist -cf - "$name" | zstd -T0 -19 -o "/work/dist/${name}.tar.zst"
rm -rf "$stage"
echo "ARTIFACT=/work/dist/${name}.tar.zst"
