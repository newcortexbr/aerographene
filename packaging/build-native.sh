#!/usr/bin/env bash
# aerographene: pacotes nativos (.pkg.tar.zst, .deb, .rpm) a partir do tarball compilado.
# uso: bash packaging/build-native.sh <aerographene-*.tar.zst> <avx2|avx1> <X.Y.Z> [dir de saída]
# Requer docker. Não compila nada: só empacota.
#   1. makepkg (packaging/arch/PKGBUILD) num container archlinux:base-devel, usuário não-root
#   2. a árvore do .pkg.tar.zst é extraída e vira a lista de arquivos do nfpm
#      (deb e rpm saem com o mesmo conteúdo, modos e wrapper do pacote Arch)
# Saída: aerographene-vX.Y.Z-<cpu>-linux.{pkg.tar.zst,deb,rpm}, namcap.txt, SHA256SUMS.native
set -euo pipefail

ARCH_IMAGE="archlinux:base-devel"
NFPM_IMAGE="goreleaser/nfpm:v2.48.0@sha256:d57a1452e7a019896b355f7b1ec67262278f6c503631f652d4fce7aef9ac8df7"

tarball="${1:?uso: build-native.sh <tarball.tar.zst> <avx2|avx1> <X.Y.Z> [saída]}"
cpu="${2:?cpu: avx2 ou avx1}"
ver="${3:?versão X.Y.Z}"
out="${4:-./dist-native}"

case "$cpu" in avx2|avx1) ;; *) echo "erro: cpu inválida: $cpu" >&2; exit 1 ;; esac
[[ "$ver" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "erro: versão deve ser X.Y.Z (sem 'v')" >&2; exit 1; }
[ -f "$tarball" ] || { echo "erro: tarball não encontrado: $tarball" >&2; exit 1; }
command -v docker >/dev/null || { echo "erro: docker não encontrado" >&2; exit 1; }

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$out"
out="$(cd "$out" && pwd)"
tarball="$(cd "$(dirname "$tarball")" && pwd)/$(basename "$tarball")"
work="$out/.work-$cpu"
rm -rf -- "$work"
mkdir -p "$work"
base="aerographene-v${ver}-${cpu}-linux"
sha="$(sha256sum "$tarball" | cut -d' ' -f1)"

echo "== 1/3 makepkg ($ARCH_IMAGE)"
docker run --rm \
    -e AERO_PKGVER="$ver" -e AERO_TARBALL_SHA256="$sha" -e BASE="$base" \
    -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
    -v "$here/arch:/pkgsrc:ro" -v "$tarball:/in/tarball.tar.zst:ro" -v "$work:/out" \
    "$ARCH_IMAGE" bash -euo pipefail -c '
        pacman -Sy --noconfirm --needed namcap >/dev/null
        useradd -m builder
        b=/home/builder/build
        mkdir "$b"
        cp -a /pkgsrc/. "$b/"
        cp /in/tarball.tar.zst "$b/aerographene-${AERO_PKGVER}-x86_64_linux.tar.zst"
        chown -R builder "$b"
        # fontes locais; -d: as dependências de runtime não precisam estar instaladas para empacotar
        runuser -u builder -- env HOME=/home/builder bash -c "cd $b && makepkg -d --noconfirm"
        pkg="$(ls "$b"/*.pkg.tar.zst)"
        cp "$pkg" "/out/${BASE}.pkg.tar.zst"
        { echo "# namcap PKGBUILD"; namcap "$b/PKGBUILD" || true
          echo "# namcap pacote"; namcap "$pkg" || true; } > /out/namcap.txt 2>&1
        # árvore instalada (modos preservados com -p) e manifesto, antes do chown (que limpa o setuid)
        mkdir /out/stage
        bsdtar -xpf "$pkg" -C /out/stage
        rm -f /out/stage/.PKGINFO /out/stage/.BUILDINFO /out/stage/.MTREE /out/stage/.INSTALL
        (cd /out/stage && find . -mindepth 1 \( -type f -o -type l \) -printf "%y\t%m\t%P\t%l\n" | LC_ALL=C sort) > /out/manifest.tsv
        chown -R "$HOST_UID:$HOST_GID" /out
    '

echo "== 2/3 nfpm.yaml a partir do manifesto"
{
    cat "$here/nfpm.yaml"
    awk -F'\t' '
        $1 == "f" { printf "  - src: /out/stage/%s\n    dst: /%s\n    file_info:\n      mode: 0%s\n", $3, $3, $2; next }
        $1 == "l" { printf "  - src: %s\n    dst: /%s\n    type: symlink\n", $4, $3; next }
    ' "$work/manifest.tsv"
} > "$work/nfpm.run.yaml"
grep -q 'mode: 04755' "$work/nfpm.run.yaml" || echo "aviso: chrome-sandbox 4755 ausente no manifesto (tarball sem chrome-sandbox?)" >&2

echo "== 3/3 nfpm ($NFPM_IMAGE)"
for fmt in deb rpm; do
    docker run --rm --user "$(id -u):$(id -g)" -e VERSION="$ver" -v "$work:/out" "$NFPM_IMAGE" \
        package -f /out/nfpm.run.yaml -p "$fmt" -t "/out/${base}.${fmt}"
done

for ext in pkg.tar.zst deb rpm; do mv -- "$work/${base}.${ext}" "$out/"; done
mv -- "$work/namcap.txt" "$out/namcap-${cpu}.txt"
mv -- "$work/manifest.tsv" "$out/manifest-${cpu}.tsv"
rm -rf -- "$work"
(cd "$out" && sha256sum "${base}".{pkg.tar.zst,deb,rpm} > "SHA256SUMS.native-${cpu}")
ls -l "$out"
