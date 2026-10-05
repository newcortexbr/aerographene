#!/bin/bash
# aerographene: roda dentro do container (aerographene-builder).
# /work = workdir persistente; /aero = repo aerographene (ro).
set -euo pipefail

. /aero/build/config.sh
. /work/portablelinux/scripts/shared.sh   # funções oficiais do portablelinux

setup_paths   # _root=/work/portablelinux, _src_dir=$_root/build/src, _out_dir=$_src_dir/out/Default
AERO_PATCHES=/aero/patches

# hash da série própria: se mudar, a árvore é recriada (download fica em cache; out/ é preservado)
patch_hash() {
    {
        cat "${AERO_PATCHES}/series"
        grep -v '^\s*#' "${AERO_PATCHES}/series" | sed '/^\s*$/d' | while read -r p _; do
            cat "${AERO_PATCHES}/${p}"
        done
        echo "march=${MARCH}"
    } | sha256sum | cut -d' ' -f1
}

want_hash="$(patch_hash)"
have_hash="$(cat "${_src_dir}/.aero-patches.hash" 2>/dev/null || true)"
# sem hash = aplicação anterior interrompida (árvore parcialmente patcheada): recria também
if [ -f "${_src_dir}/.downloaded.stamp" ] && { [ ! -f "${_src_dir}/.aero-patches.hash" ] || [ "${want_hash}" != "${have_hash}" ]; }; then
    echo "== série de patches mudou: recriando a árvore (preservando out/)"
    if [ -d "${_src_dir}/out" ]; then mv "${_src_dir}/out" "${_root}/build/out.keep"; fi
    rm -rf "${_src_dir}"
fi
if [ ! -f "${_src_dir}/.downloaded.stamp" ] && [ -d "${_root}/build/out.keep" ] && [ ! -d "${_src_dir}/out" ]; then
    restore_out=1
fi

echo "== fetch (cache em ${_dl_cache})"
fetch_sources false false
if [ -n "${restore_out:-}" ]; then mkdir -p "${_src_dir}"; mv "${_root}/build/out.keep" "${_src_dir}/out"; fi

echo "== pruning + patches ungoogled + portablelinux"
apply_patches

echo "== patches aerographene (${AERO_PATCHES}/series)"
if [ ! -f "${_src_dir}/.aero-patches.hash" ]; then
    if grep -qv '^\s*\(#.*\)\?$' "${AERO_PATCHES}/series" 2>/dev/null; then
        "${_main_repo}/utils/patches.py" apply "${_src_dir}" "${AERO_PATCHES}"
    else
        echo "série vazia"
    fi

    # -march: o GN do Chromium não tem arg para isso em x86; acrescenta à config
    # compiler_cpu_abi (vale para C/C++, asm, link LTO e Rust).
    gnfile="${_src_dir}/build/config/compiler/BUILD.gn"
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

echo "== domain substitution"
apply_domsub
fix_tool_downloading

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
# setup_toolchain faz rm -rf esbuild/ (barra final segue o symlink de uma execução anterior e tenta apagar /usr/lib)
rm -f "${_src_dir}/third_party/devtools-frontend/src/node_modules/esbuild"
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

echo "== ninja -j ${JOBS}"
ninja -C out/Default -j "${JOBS}" chrome

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
