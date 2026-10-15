#!/bin/bash
# aerographene: build Windows x64 por cross-compile no host (ver docs/wiki/windows.md).
# Alvo de CPU como no Linux (build/config.sh, ADR 0009): avx2 = x86-64-v3, avx1 = ivybridge.
# Os dois alvos usam o mesmo out/Win em sequência (disco); trocar de alvo recompila tudo.
#
# Uso: build/win/build.sh <avx2|avx1> [all|gen|ninja|pack] [alvos ninja...]
#   all   (padrão) prepare + -march + gn gen + ninja chrome mini_installer + pack
#   gen   prepare + -march + gn gen
#   ninja só o ninja (alvos dados ou chrome mini_installer), no container
#   pack  zip portátil + mini_installer.exe em $AERO_WIN_DIST/<cpu>/
# Env:
#   AERO_WIN_SRC            árvore (padrão ~/aerographene-win/src4)
#   AERO_WIN_TOOLCHAIN_DIR  dir do zip do toolchain (padrão ~/win-toolchain); licenciado, fora do git
#   AERO_WIN_DIST           saída dos pacotes (padrão <pai do src>/dist), fora de out/
#   AERO_WIN_JOBS           -j do ninja (padrão 10)
#   AERO_WIN_FORCE=1        roda mesmo com build Linux em andamento (não recomendado)
#   MARCH                   sobrescreve o -march do alvo
set -euo pipefail

cpu="${1:?uso: $0 <avx2|avx1> [all|gen|ninja|pack] [alvos...]}"
step="${2:-all}"; shift $(( $# >= 2 ? 2 : 1 ))
case "$cpu" in
    avx2) MARCH="${MARCH:-x86-64-v3}" ;;
    avx1) MARCH="${MARCH:-ivybridge}" ;;
    *) echo "erro: cpu '$cpu' (avx2|avx1)" >&2; exit 1 ;;
esac
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="$(cd "${AERO_WIN_SRC:-$HOME/aerographene-win/src4}" && pwd)"
win="$(dirname "$src")"
out="$src/out/Win"
dist="${AERO_WIN_DIST:-$win/dist}/$cpu"
jobs="${AERO_WIN_JOBS:-10}"
targets=("$@"); [ ${#targets[@]} -gt 0 ] || targets=(chrome mini_installer)
export AERO_WIN_TOOLCHAIN_DIR="${AERO_WIN_TOOLCHAIN_DIR:-$HOME/win-toolchain}"

# exclusão com a build Linux (grupo `build`): mesmo host, RAM e disco
linux_busy() {
    [ "${AERO_WIN_FORCE:-0}" = 1 ] && return 1
    command -v gh >/dev/null || { echo "aviso: gh ausente, não deu para conferir build Linux" >&2; return 1; }
    [ -n "$(gh run list -R newcortexbr/aerographene -s in_progress --json databaseId -q '.[].databaseId' 2>/dev/null)" ]
}

# -march na config compiler_cpu_abi, só para a toolchain Windows (host Linux fica como está).
# clang-cl recebe /clang:-march=; Rust -Ctarget-cpu. O link ThinLTO herda o target-cpu do bitcode.
# Escreve por temporário + mv (nunca através de hardlink da árvore do CI). Idempotente.
apply_march() {
    local f="$src/build/config/compiler/BUILD.gn"
    python3 - "$f" "$MARCH" <<'PY'
import os, re, sys
path, march = sys.argv[1], sys.argv[2]
s = open(path).read()
beg, end = '  # aerographene-win: -march (build/win/build.sh)\n', '  # /aerographene-win\n'
s = re.sub(re.escape(beg) + r'.*?' + re.escape(end), '', s, flags=re.S)
m = re.search(r'config\("compiler_cpu_abi"\) \{\n(?:.*\n)*?  ldflags \+?= cpu_abi_ldflags\n', s)
assert m, "bloco compiler_cpu_abi mudou"
add = (beg + '  if (current_cpu == "x64" && is_win) {\n'
       f'    cflags += [ "/clang:-march={march}" ]\n'
       f'    rustflags = [ "-Ctarget-cpu={march}" ]\n'
       '  }\n' + end)
s = s[:m.end()] + add + s[m.end():]
tmp = path + '.aero-new'
open(tmp, 'w').write(s)
os.replace(tmp, path)
PY
    echo "march=$MARCH ($cpu) em compiler_cpu_abi (is_win)"
    # /clang:-march global anula o /arch:AVX512 do skia (skcms_TransformSkx); repete /clang:-march=x86-64-v4 depois
    # dele (mesmo -march do ramo não-Windows do skia). Idempotente.
    python3 - "$src/skia/BUILD.gn" <<'PY'
import os, sys
path = sys.argv[1]
s = open(path).read()
old = '    cflags = [ "/arch:AVX512" ]\n'
new = '    cflags = [ "/arch:AVX512", "/clang:-march=x86-64-v4" ]\n'
if new not in s:
    assert s.count(old) == 1, "skia_avx512_flags mudou"
    open(path + '.aero-new', 'w').write(s.replace(old, new))
    os.replace(path + '.aero-new', path)
PY
}

do_gen() {
    bash "$here/prepare.sh" "$src" out/Win
    apply_march
    local h; h="$(sed -nE "s/^TOOLCHAIN_HASH = '([0-9a-f]+)'/\1/p" "$src/build/vs_toolchain.py")"
    local tc; tc="$(basename "$(ls "$AERO_WIN_TOOLCHAIN_DIR"/*.zip | head -1)" .zip)"
    (cd "$src" && env DEPOT_TOOLS_WIN_TOOLCHAIN=1 "GYP_MSVS_HASH_${h}=${tc}" "$win/bin/gn" gen out/Win)
    echo "$cpu $MARCH" > "$out/.aero-cpu"
}

do_ninja() {
    if linux_busy; then echo "erro: há run em andamento no GitHub (build Linux?); AERO_WIN_FORCE=1 para ignorar" >&2; exit 1; fi
    mountpoint -q "$src/third_party/depot_tools/win_toolchain/vs_files" \
        || { echo "erro: vs_files (ciopfs) não montado; rode '$0 $cpu gen'" >&2; exit 1; }
    grep -qx "$cpu $MARCH" "$out/.aero-cpu" 2>/dev/null \
        || { echo "erro: out/Win não foi gerado para $cpu ($MARCH); rode '$0 $cpu gen'" >&2; exit 1; }
    flock /tmp/aero-win-ninja.lock docker run --rm --init --user "$(id -u):$(id -g)" \
        --ulimit nofile=65536:65536 -v "$win:$win" -w "$src" aerographene-builder:v2 \
        nice -n 19 "$win/bin/ninja" -C out/Win -j "$jobs" "${targets[@]}"
}

do_pack() {
    local z7="$src/third_party/lzma_sdk/bin/host_platform/7za"
    grep -qx "$cpu $MARCH" "$out/.aero-cpu" 2>/dev/null || { echo "erro: out/Win não é do alvo $cpu" >&2; exit 1; }
    [ -f "$out/chrome.7z" ] && [ -f "$out/mini_installer.exe" ] || { echo "erro: falta chrome.7z/mini_installer.exe" >&2; exit 1; }
    local stage; stage="$(mktemp -d "$win/pack.XXXXXX")"
    trap 'rm -rf "$stage"' RETURN
    # chrome.7z (Chrome-bin/) é a lista oficial de arquivos do instalador (chrome.release)
    "$z7" x -y -bd -o"$stage" "$out/chrome.7z" >/dev/null
    mv "$stage/Chrome-bin" "$stage/aerographene"
    # fontes do tema (<exe>\fonts): chrome.release não as lista
    [ -d "$out/fonts" ] && cp -r "$out/fonts" "$stage/aerographene/"
    mkdir -p "$dist"
    rm -f "$dist/aerographene-win-$cpu.zip"
    (cd "$stage" && "$z7" a -tzip -mx=7 -bd "$dist/aerographene-win-$cpu.zip" aerographene >/dev/null)
    cp "$out/mini_installer.exe" "$dist/mini_installer-$cpu.exe.aero-new"
    mv -f "$dist/mini_installer-$cpu.exe.aero-new" "$dist/mini_installer-$cpu.exe"
    (cd "$dist" && sha256sum "aerographene-win-$cpu.zip" "mini_installer-$cpu.exe" > SHA256SUMS && ls -l --block-size=M .)
}

case "$step" in
    all) do_gen; do_ninja; do_pack ;;
    gen) do_gen ;;
    ninja) do_ninja ;;
    pack) do_pack ;;
    *) echo "erro: passo '$step'" >&2; exit 1 ;;
esac
