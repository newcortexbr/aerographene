#!/usr/bin/env bash
# aerographene: testa instalação e remoção dos pacotes nativos em containers de cada distro.
# uso: bash packaging/test-install.sh <dir com os pacotes de build-native.sh> <avx2|avx1> <X.Y.Z>
#   archlinux      pacman -U  .pkg.tar.zst
#   ubuntu:24.04   apt install ./.deb      (resolve as dependências do próprio .deb)
#   fedora         dnf install .rpm
# Em cada um: instala, confere arquivos/modo/ldd, roda `aerographene --version`, remove e
# confere que nada ficou. Requer docker e rede (repositórios das distros). Não compila nada.
set -euo pipefail

if [ "${1:-}" = "--inner" ]; then
    # --- dentro do container ---
    fail() { echo "FALHOU: $*" >&2; exit 1; }
    case "${2:?fase}" in
    installed)
        d=/opt/aerographene
        [ -x "$d/aerographene" ] || fail "$d/aerographene ausente"
        [ -x /usr/bin/aerographene ] || fail "wrapper /usr/bin/aerographene ausente"
        [ -f /usr/share/applications/aerographene.desktop ] || fail "desktop ausente"
        [ -f /usr/share/applications/aerographene-theme-import.desktop ] || fail "desktop de tema ausente"
        [ -f /usr/share/mime/packages/aerographene.xml ] || fail "MIME ausente"
        [ -f /usr/share/icons/hicolor/48x48/apps/aerographene.png ] || fail "ícone 48 ausente"
        [ -f /usr/share/licenses/aerographene/LICENSE ] || fail "LICENSE ausente"
        if [ -f "$d/chrome-sandbox" ]; then
            [ "$(stat -c '%a %U' "$d/chrome-sandbox")" = "4755 root" ] \
                || fail "chrome-sandbox com modo/dono errado: $(stat -c '%a %U' "$d/chrome-sandbox")"
            echo "chrome-sandbox: 4755 root"
        else
            echo "aviso: pacote sem chrome-sandbox"
        fi
        echo "== ldd chrome (faltas)"
        missing="$(ldd "$d/chrome" | grep 'not found' || true)"
        [ -z "$missing" ] || { echo "$missing"; fail "bibliotecas ausentes"; }
        echo "nenhuma"
        echo "== aerographene --version"
        HOME=/root timeout 60 aerographene --version
        echo "== headless (informativo)"
        if HOME=/root timeout 90 aerographene --headless --no-sandbox --disable-gpu --dump-dom about:blank 2>/dev/null | grep -q '<html'; then
            echo "headless: ok"
        else
            echo "headless: sem DOM (informativo, não reprova)"
        fi
        ;;
    removed)
        for p in /opt/aerographene /usr/bin/aerographene /usr/share/applications/aerographene.desktop \
                 /usr/share/applications/aerographene-theme-import.desktop /usr/share/mime/packages/aerographene.xml \
                 /usr/share/icons/hicolor/48x48/apps/aerographene.png /usr/share/licenses/aerographene; do
            [ ! -e "$p" ] || fail "sobrou depois da remoção: $p"
        done
        echo "remoção limpa"
        ;;
    *) fail "fase desconhecida" ;;
    esac
    exit 0
fi

dir="${1:?uso: test-install.sh <dir> <avx2|avx1> <X.Y.Z>}"
cpu="${2:?cpu}"
ver="${3:?versão}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dir="$(cd "$dir" && pwd)"
base="aerographene-v${ver}-${cpu}-linux"
rc=0

run() {  # $1 = rótulo, $2 = imagem, $3 = pacote, $4 = comando de instalação, $5 = comando de remoção
    local label="$1" image="$2" pkg="$3" inst="$4" rem="$5" t="bash /t/test-install.sh --inner"
    echo "=================== $label ($image)"
    if docker run --rm -v "$dir:/pkg:ro" -v "$here:/t:ro" "$image" bash -euo pipefail -c \
        "$inst && $t installed && $rem && $t removed"; then
        echo "RESULTADO $label: OK"
    else
        echo "RESULTADO $label: FALHOU" >&2
        rc=1
    fi
}

run arch archlinux "${base}.pkg.tar.zst" \
    "pacman -Sy --noconfirm >/dev/null && pacman -U --noconfirm /pkg/${base}.pkg.tar.zst" \
    "pacman -R --noconfirm aerographene"
run ubuntu ubuntu:24.04 "${base}.deb" \
    "apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq /pkg/${base}.deb" \
    "DEBIAN_FRONTEND=noninteractive apt-get remove -y -qq aerographene"
run fedora fedora:latest "${base}.rpm" \
    "dnf install -y -q /pkg/${base}.rpm" \
    "dnf remove -y -q aerographene"
exit "$rc"
