#!/bin/bash
# aerographene: prepara uma árvore Chromium (já com ungoogled + série aplicadas) para o
# cross-compile Linux -> Windows x64 (fatia D3a do docs/PLANO-V0.3.md, docs/wiki/windows.md).
# Repõe o que o tarball do ungoogled/portablelinux não traz (hooks do DEPS que não rodaram,
# binários podados), sempre conferindo hash, e extrai o toolchain VS+SDK com
# build/vs_toolchain.py. Idempotente: item presente com hash certo é pulado.
#
# A árvore pode ser cópia por hardlink (cp -al) da árvore do CI: nada é escrito através de um
# link. Arquivo novo entra por arquivo temporário + mv (troca a entrada do diretório);
# arquivo com mtime no futuro tem o link quebrado (cópia) antes do touch.
#
# Uso: prepare.sh <raiz-do-src> [dir-de-saída, padrão out/Win]
# Env:
#   AERO_WIN_TOOLCHAIN_DIR   diretório com o zip do toolchain (<hash>.zip, gerado com
#                            package_from_installed.py). Obrigatório. Licenciado: fora do git.
#   AERO_WIN_TOOLCHAIN_HASH  hash (nome do zip sem .zip). Padrão: o único *.zip do diretório.
#   AERO_WIN_CACHE           downloads e libfuse2 local. Padrão: <pai do src>/win-cache.
# Depois: export LD_LIBRARY_PATH impresso no fim (ciopfs) e `gn gen <saída>`.
set -euo pipefail

src="$(cd "${1:?uso: $0 <raiz-do-src> [dir-de-saída]}" && pwd)"
out_rel="${2:-out/Win}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cache="${AERO_WIN_CACHE:-$(dirname "$src")/win-cache}"
tc_dir="${AERO_WIN_TOOLCHAIN_DIR:?defina AERO_WIN_TOOLCHAIN_DIR (diretório com <hash>.zip)}"

[ -f "$src/DEPS" ] && [ -f "$src/build/vs_toolchain.py" ] || { echo "erro: $src não parece um src do Chromium" >&2; exit 1; }
for bin in curl python3 sha1sum sha256sum tar dpkg-deb apt-get fusermount; do
    command -v "$bin" >/dev/null || { echo "erro: '$bin' não encontrado" >&2; exit 1; }
done
mkdir -p "$cache/dl"

# hash esperado: algoritmo (sha1|sha256), valor, arquivo
check_hash() {
    [ "$("${1}sum" "$3" | cut -d' ' -f1)" = "$2" ]
}

# baixa $1 para o cache ($2 = nome), confere ($3 algoritmo, $4 hash); imprime o caminho
fetch() {
    local url="$1" f="$cache/dl/$2" algo="$3" want="$4"
    if [ ! -f "$f" ] || ! check_hash "$algo" "$want" "$f"; then
        echo "   baixando $url" >&2
        curl -fsSL --retry 3 -o "$f.part" "$url"
        check_hash "$algo" "$want" "$f.part" || { echo "erro: $algo de $url não confere ($want)" >&2; rm -f "$f.part"; exit 1; }
        mv -f "$f.part" "$f"
    fi
    echo "$f"
}

# instala $1 em $2 (relativo a src) como arquivo novo, modo $3; não escreve através de hardlink
place() {
    local from="$1" dest="$src/$2" mode="$3"
    mkdir -p "$(dirname "$dest")"
    cp "$from" "$dest.aero-new"
    chmod "$mode" "$dest.aero-new"
    mv -f "$dest.aero-new" "$dest"
}

# arquivo regular (não symlink) com o hash pedido?
have() { [ -f "$src/$3" ] && [ ! -L "$src/$3" ] && check_hash "$1" "$2" "$src/$3"; }

echo "== 1. ciopfs (hook ciopfs_linux do DEPS)"
h="$(tr -d '[:space:]' < "$src/build/ciopfs.sha1")"
if have sha1 "$h" build/ciopfs; then echo "   ok"; else
    place "$(fetch "https://storage.googleapis.com/chromium-browser-clang/ciopfs/$h" "ciopfs-$h" sha1 "$h")" build/ciopfs 755
fi

echo "== 1b. libfuse2 local para o ciopfs (sem sudo; apt confere a assinatura do pacote)"
fuse_lib="$cache/root/lib/x86_64-linux-gnu"
if [ -e "$fuse_lib/libfuse.so.2" ]; then echo "   ok"; else
    pkg=libfuse2t64; apt-cache show "$pkg" >/dev/null 2>&1 || pkg=libfuse2
    (cd "$cache/dl" && apt-get download "$pkg")
    dpkg-deb -x "$(ls -t "$cache/dl/${pkg}"_*.deb | head -1)" "$cache/root"
    [ -e "$fuse_lib/libfuse.so.2" ] || { echo "erro: libfuse.so.2 não veio em $pkg" >&2; exit 1; }
fi
export LD_LIBRARY_PATH="$fuse_lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

echo "== 5. runtime clang Windows (o mesmo de tools/clang/scripts/update.py com target_os win)"
pv="$(python3 - "$src/tools/clang/scripts/update.py" <<'PY'
import re, sys
s = open(sys.argv[1]).read()
rev = re.search(r"^CLANG_REVISION = '([^']+)'", s, re.M).group(1)
sub = re.search(r"^CLANG_SUB_REVISION = (\d+)", s, re.M).group(1)
print(f"{rev}-{sub}")
PY
)"
# a árvore não traz hash deste pacote: sha256 fixado aqui na primeira verificação (13/10/2026);
# CLANG_REVISION novo exige conferir e fixar de novo.
declare -A crt_sha=(
    [llvmorg-24-init-3796-g20e97c4b-27]=51c15d0bc56eaf36b2c7b1eb6c2e9b70442201c6040abf438fb1c310e01882fe
)
[ -n "${crt_sha[$pv]:-}" ] || { echo "erro: sem sha256 fixado para clang-win-runtime-library-$pv" >&2; exit 1; }
llvm=third_party/llvm-build/Release+Asserts
crt_stamp="$src/$llvm/lib/clang/.aero-win-runtime-$pv"
if [ -f "$crt_stamp" ]; then echo "   ok"; else
    t="$(fetch "https://commondatastorage.googleapis.com/chromium-browser-clang/Win/clang-win-runtime-library-$pv.tar.xz" \
        "clang-win-runtime-library-$pv.tar.xz" sha256 "${crt_sha[$pv]}")"
    x="$cache/crt-$pv"; rm -rf "$x"; mkdir -p "$x"; tar -xJf "$t" -C "$x"
    (cd "$x" && find . -type f) | while read -r f; do place "$x/$f" "$llvm/${f#./}" "$(stat -c %a "$x/$f")"; done
    rm -rf "$x"
    touch "$crt_stamp"
fi

echo "== 6. clang-format linux64 (DEPS src/buildtools/linux64-format; o tarball tem symlink do container)"
read -r cf_obj cf_sha < <(python3 - "$src/DEPS" <<'PY'
import re, sys
s = open(sys.argv[1]).read()
blk = s[s.index("'src/buildtools/linux64-format'"):]
blk = blk[:blk.index("],")]
print(re.search(r"'object_name': '([0-9a-f]+)'", blk).group(1), re.search(r"'sha256sum': '([0-9a-f]+)'", blk).group(1))
PY
)
if have sha256 "$cf_sha" buildtools/linux64-format/clang-format; then echo "   ok"; else
    place "$(fetch "https://storage.googleapis.com/chromium-clang-format/$cf_obj" "clang-format-$cf_obj" sha256 "$cf_sha")" \
        buildtools/linux64-format/clang-format 755
fi

echo "== 7. rc linux64 (hook rc_linux do DEPS)"
h="$(tr -d '[:space:]' < "$src/build/toolchain/win/rc/linux64/rc.sha1")"
if have sha1 "$h" build/toolchain/win/rc/linux64/rc; then echo "   ok"; else
    place "$(fetch "https://storage.googleapis.com/chromium-browser-clang/rc/$h" "rc-$h" sha1 "$h")" build/toolchain/win/rc/linux64/rc 755
fi

echo "== 8. windows.0.52.0.lib do crate windows_x86_64_msvc (podado pelo ungoogled)"
vend=third_party/rust/chromium_crates_io/vendor/windows_x86_64_msvc-v0_52
ver="$(sed -nE 's/^version = "([^"]+)"/\1/p' "$src/$vend/Cargo.toml" | head -1)"
# o vendor do Chromium não guarda checksum (.cargo-checksum.json vazio, Cargo.lock sem
# checksum): confere contra o valor fixado e contra o índice do crates.io
declare -A crate_sha=(
    [0.52.6]=589f6da84c646204747d1270a2a5661ea66ed1cced2631d546fdfb155959f9ec
)
[ -n "${crate_sha[$ver]:-}" ] || { echo "erro: sem sha256 fixado para windows_x86_64_msvc $ver" >&2; exit 1; }
lib_rel="$vend/lib/windows.0.52.0.lib"
lib_stamp="$src/$vend/lib/.aero-crate-${crate_sha[$ver]}"
if [ -f "$lib_stamp" ] && [ -f "$src/$lib_rel" ]; then echo "   ok"; else
    idx="$(curl -fsSL --retry 3 https://index.crates.io/wi/nd/windows_x86_64_msvc | python3 -c '
import json, sys
v = sys.argv[1]
print(next(e["cksum"] for e in map(json.loads, sys.stdin) if e["vers"] == v))' "$ver")"
    [ "$idx" = "${crate_sha[$ver]}" ] || { echo "erro: índice do crates.io diz $idx para $ver" >&2; exit 1; }
    c="$(fetch "https://static.crates.io/crates/windows_x86_64_msvc/windows_x86_64_msvc-$ver.crate" \
        "windows_x86_64_msvc-$ver.crate" sha256 "${crate_sha[$ver]}")"
    x="$cache/crate-$ver"; rm -rf "$x"; mkdir -p "$x"; tar -xzf "$c" -C "$x" --strip-components=1
    # o resto do crate tem de ser igual ao vendorizado (mesma fonte)
    for f in build.rs src/lib.rs Cargo.toml.orig; do
        cmp -s "$x/$f" "$src/$vend/$f" || { echo "erro: $f do crate difere do vendorizado" >&2; exit 1; }
    done
    place "$x/lib/windows.0.52.0.lib" "$lib_rel" 644
    rm -rf "$x"
    touch "$lib_stamp"
fi

echo "== 3. toolchain VS+SDK (build/vs_toolchain.py update; monta vs_files com ciopfs)"
tc_hash="${AERO_WIN_TOOLCHAIN_HASH:-}"
if [ -z "$tc_hash" ]; then
    zips=("$tc_dir"/*.zip)
    [ "${#zips[@]}" = 1 ] && [ -f "${zips[0]}" ] || { echo "erro: defina AERO_WIN_TOOLCHAIN_HASH (0 ou vários .zip em $tc_dir)" >&2; exit 1; }
    tc_hash="$(basename "${zips[0]}" .zip)"
fi
[ -f "$tc_dir/$tc_hash.zip" ] || { echo "erro: $tc_dir/$tc_hash.zip não existe" >&2; exit 1; }
up_hash="$(sed -nE "s/^TOOLCHAIN_HASH = '([0-9a-f]+)'/\1/p" "$src/build/vs_toolchain.py")"
export DEPOT_TOOLS_WIN_TOOLCHAIN=1 DEPOT_TOOLS_WIN_TOOLCHAIN_BASE_URL="$tc_dir" "GYP_MSVS_HASH_${up_hash}=${tc_hash}"
(cd "$src" && python3 build/vs_toolchain.py update --force)
[ -f "$src/build/win_toolchain.json" ] || { echo "erro: build/win_toolchain.json não foi gerado" >&2; exit 1; }

echo "== 4. mtime no futuro (faz o ninja regenerar em laço)"
ref="$cache/.now"; touch -d '+1 minute' "$ref"
n=0
while IFS= read -r -d '' f; do
    if [ "$(stat -c %h "$f")" -gt 1 ]; then cp -p "$f" "$f.aero-new" && mv -f "$f.aero-new" "$f"; fi
    touch -d '2 minutes ago' "$f"; n=$((n + 1))
done < <(find "$src" -path "$src/out" -prune -o -path "$src/third_party/depot_tools/win_toolchain" -prune \
    -o -type f -newer "$ref" -print0)
echo "   $n arquivo(s) ajustado(s)"

echo "== 2. args (${out_rel}/args.gn; use_sysroot=false proibido)"
out="$src/$out_rel"
mkdir -p "$out"
[ -f "$out/args.gn" ] || cp "$here/args.gn" "$out/args.gn"
if grep -Eq '^\s*use_sysroot\s*=\s*false' "$out/args.gn"; then
    echo "erro: $out/args.gn tem use_sysroot=false (a toolchain host Linux passa a pedir glib do host)" >&2; exit 1
fi
[ -d "$src/build/linux/debian_bullseye_amd64-sysroot" ] || echo "aviso: sysroot Debian amd64 ausente na árvore"

echo "== 9. ativos Windows (.ico do app e JetBrains Mono; D3d)"
bash "$here/apply_assets.sh" "$src"

echo "== 10. saídas MIDL/mc pré-geradas (.tlb, .bin) de third_party/win_build_output e chrome/app/etw_events (podadas pelo ungoogled)"
# no Linux o midl.py/rc só copiam estes binários; sem eles as ações *_idl e eventlog falham.
# Fonte: chromium/src na tag da versão; cada blob é conferido pelo id git da listagem da árvore.
python3 - "$src" <<'PY'
import base64, hashlib, json, os, re, sys, time, urllib.error, urllib.request
src = sys.argv[1]
ver = ".".join(re.search(rf"^{k}=(\d+)", open(f"{src}/chrome/VERSION").read(), re.M).group(1)
               for k in ("MAJOR", "MINOR", "BUILD", "PATCH"))
base = f"https://chromium.googlesource.com/chromium/src/+/refs/tags/{ver}/"
wbo = "third_party/win_build_output"
need = {}
for root, _, files in (w for r in (wbo, "chrome/app/etw_events") for w in os.walk(f"{src}/{r}")):
    rel = os.path.relpath(root, src)
    if root.endswith("/x64"):
        for f in files:
            if f.endswith(".h"):
                need.setdefault(rel, set()).add(f[:-2] + ".tlb")
    for f in files:
        if f.endswith(".rc"):
            need.setdefault(rel, set()).update(re.findall(r"\w+\.bin", open(f"{root}/{f}", errors="replace").read(), re.I))
def get(url):
    for i in range(8):  # o gitiles devolve 429/503 em rajada
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503) or i == 7:
                raise
            time.sleep(2 ** i)
n = 0
for d, names in sorted(need.items()):
    missing = [x for x in sorted(names) if not os.path.isfile(f"{src}/{d}/{x}")]
    if not missing:
        continue
    tree = json.loads(get(base + d + "?format=JSON")[4:])  # remove o prefixo )]}'
    ids = {e["name"]: e["id"] for e in tree["entries"]}
    for x in missing:
        if x not in ids:
            continue  # .tlb que o upstream também não gera
        data = base64.b64decode(get(base + f"{d}/{x}?format=TEXT"))
        if hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() != ids[x]:
            sys.exit(f"erro: blob de {d}/{x} não confere")
        tmp = f"{src}/{d}/{x}.aero-new"
        open(tmp, "wb").write(data); os.replace(tmp, f"{src}/{d}/{x}"); n += 1
print(f"   {n} arquivo(s) reposto(s) (tag {ver})")
PY

echo "== 11. 7za linux-amd64 (CIPD de src/third_party/lzma_sdk/bin/host_platform; usado pelo mini_installer)"
z_ver="$(python3 - "$src/DEPS" <<'PY'
import re, sys
s = open(sys.argv[1]).read()
blk = s[s.index("'src/third_party/lzma_sdk/bin/host_platform'"):]
print(re.search(r"'version': '([^']+)'", blk).group(1))
PY
)"
# id da instância CIPD = sha256 do zip; fixado na primeira verificação (14/10/2026)
declare -A z_sha=(
    [version:3@26.03]=6b9e6cf8076f7f949abb9d986e5048af26f6cdcfa6cd1a14554d5dc4fcce322c
)
[ -n "${z_sha[$z_ver]:-}" ] || { echo "erro: sem sha256 fixado para 7z $z_ver" >&2; exit 1; }
z_rel=third_party/lzma_sdk/bin/host_platform/7za
if [ -x "$src/$z_rel" ] && [ -f "$src/$z_rel.aero-${z_sha[$z_ver]}" ]; then echo "   ok"; else
    z_url="$(curl -fsS -H 'Content-Type: application/json' -H 'Accept: application/json' \
        -d "{\"package\":\"infra/3pp/tools/7z/linux-amd64\",\"instance\":{\"hashAlgo\":\"SHA256\",\"hexDigest\":\"${z_sha[$z_ver]}\"}}" \
        https://chrome-infra-packages.appspot.com/prpc/cipd.Repository/GetInstanceURL \
        | tail -n +2 | python3 -c 'import json, sys; print(json.load(sys.stdin)["signedUrl"])')"
    z="$(fetch "$z_url" "7z-linux-amd64-${z_sha[$z_ver]}.zip" sha256 "${z_sha[$z_ver]}")"
    x="$cache/7z"; mkdir -p "$x"; python3 -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extract("7za", sys.argv[2])' "$z" "$x"
    place "$x/7za" "$z_rel" 755
    touch "$src/$z_rel.aero-${z_sha[$z_ver]}"
fi

echo "== pronto. Próximo:"
echo "   export LD_LIBRARY_PATH=$fuse_lib   # só para remontar o ciopfs (rode este script de novo após reboot)"
echo "   gn gen $out_rel && nice -n 19 ninja -C $out_rel -j8 chrome_elf"
