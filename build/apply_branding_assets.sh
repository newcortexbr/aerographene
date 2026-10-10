#!/bin/bash
# aerographene: sobrescreve os ícones do Chromium (branding "chromium") pelos de branding/png.
# Roda de build/inner.sh depois dos patches e antes do gn gen. Idempotente: só copia se o
# conteúdo mudou (preserva mtime e evita recompilar recursos). Falha se um destino sumiu ou
# não tem o tamanho esperado do upstream 154.0.8037.97 (sinal de que o mapa precisa de revisão).
# Uso: apply_branding_assets.sh <raiz-do-src> [dir-branding]
set -euo pipefail

src="${1:?uso: $0 <raiz-do-src> [dir-branding]}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
br="${2:-${here}/../branding}/png"

T=chrome/app/theme
C=components/resources
# destino (relativo ao src) | origem (em branding/png) | tamanho esperado do original
MAP=(
    # ícones do app: linux/ (pacote .deb/.rpm, product_logo_48.png do tarball, IDR_PRODUCT_LOGO_64/128/256)
    "$T/chromium/linux/product_logo_24.png|aerographene-icon-24.png|24x24"
    "$T/chromium/linux/product_logo_48.png|aerographene-icon-48.png|48x48"
    "$T/chromium/linux/product_logo_64.png|aerographene-icon-64.png|64x64"
    "$T/chromium/linux/product_logo_128.png|aerographene-icon-128.png|128x128"
    "$T/chromium/linux/product_logo_256.png|aerographene-icon-256.png|256x256"
    # raiz chromium/ (usada fora do Linux e pelos *_SHORTCUTS; mantida coerente)
    "$T/chromium/product_logo_16.png|aerographene-icon-16.png|16x16"
    "$T/chromium/product_logo_24.png|aerographene-icon-24.png|24x24"
    "$T/chromium/product_logo_48.png|aerographene-icon-48.png|48x48"
    "$T/chromium/product_logo_64.png|aerographene-icon-64.png|64x64"
    "$T/chromium/product_logo_128.png|aerographene-icon-128.png|128x128"
    "$T/chromium/product_logo_256.png|aerographene-icon-256.png|256x256"
    # bandeja do sistema (IDR_STATUS_TRAY_ICON, monocromático): símbolo branco
    "$T/chromium/product_logo_22_mono.png|aerographene-mark-white-22.png|22x22"
    # escalonados 1x/2x (IDR_PRODUCT_LOGO_16/32, chrome_scaled_image)
    "$T/default_100_percent/chromium/linux/product_logo_16.png|aerographene-icon-16.png|16x16"
    "$T/default_100_percent/chromium/linux/product_logo_32.png|aerographene-icon-32.png|32x32"
    "$T/default_100_percent/chromium/product_logo_16.png|aerographene-icon-16.png|16x16"
    "$T/default_100_percent/chromium/product_logo_32.png|aerographene-icon-32.png|32x32"
    "$T/default_200_percent/chromium/product_logo_16.png|aerographene-icon-32.png|32x32"
    "$T/default_200_percent/chromium/product_logo_32.png|aerographene-icon-64.png|64x64"
    # logotipo com nome (IDR_PRODUCT_LOGO_NAME_22[_WHITE]): preto p/ fundo claro, branco p/ escuro
    "$T/default_100_percent/chromium/product_logo_name_22.png|logo-name-22-black-1x.png|97x22"
    "$T/default_100_percent/chromium/product_logo_name_22_white.png|logo-name-22-white-1x.png|97x22"
    "$T/default_200_percent/chromium/product_logo_name_22.png|logo-name-22-black-2x.png|194x44"
    "$T/default_200_percent/chromium/product_logo_name_22_white.png|logo-name-22-white-2x.png|194x44"
    # chrome://version (version_ui_scaled_resources.grdp: IDR_PRODUCT_LOGO[_WHITE], IDR_PRODUCT_FAVICON)
    "$C/default_100_percent/chromium/product_logo.png|logo-name-32-black-1x.png|171x32"
    "$C/default_100_percent/chromium/product_logo_white.png|logo-name-32-white-1x.png|171x32"
    "$C/default_200_percent/chromium/product_logo.png|logo-name-32-black-2x.png|342x64"
    "$C/default_200_percent/chromium/product_logo_white.png|logo-name-32-white-2x.png|342x64"
    "$C/default_100_percent/chromium/favicon_product.png|aerographene-icon-16.png|16x16"
    "$C/default_200_percent/chromium/favicon_product.png|aerographene-icon-32.png|32x32"
)

png_size() {  # largura x altura pelo IHDR (sem depender de ImageMagick no container)
    python3 -c 'import struct,sys
d=open(sys.argv[1],"rb").read(24)
assert d[:8]==b"\x89PNG\r\n\x1a\n", "não é PNG: "+sys.argv[1]
print("%dx%d"%struct.unpack(">II",d[16:24]))' "$1"
}

n=0; same=0
for entry in "${MAP[@]}"; do
    IFS='|' read -r dest from want <<<"$entry"
    d="${src}/${dest}"; s="${br}/${from}"
    [ -f "$d" ] || { echo "branding: destino ausente: ${dest}" >&2; exit 1; }
    [ -f "$s" ] || { echo "branding: origem ausente: ${s}" >&2; exit 1; }
    have_s="$(png_size "$s")"
    [ "$have_s" = "$want" ] || { echo "branding: ${from} tem ${have_s}, esperado ${want}" >&2; exit 1; }
    if cmp -s "$s" "$d"; then same=$((same+1)); continue; fi
    have_d="$(png_size "$d")"
    [ "$have_d" = "$want" ] || { echo "branding: ${dest} tem ${have_d}, esperado ${want}" >&2; exit 1; }
    cp -f "$s" "$d"; n=$((n+1))
done
# product_logo.svg (IDR_PRODUCT_LOGO_SVG, viewBox 256x256 no upstream): mesmo ícone do app
svg_d="${src}/${T}/chromium/product_logo.svg"; svg_s="${br}/../aerographene-icon.svg"
[ -f "$svg_d" ] && [ -f "$svg_s" ] || { echo "branding: product_logo.svg ou origem ausente" >&2; exit 1; }
if ! cmp -s "$svg_s" "$svg_d"; then cp -f "$svg_s" "$svg_d"; n=$((n+1)); fi
# logo do cr-toolbar no tema escuro (history, downloads, extensions...; <source> de
# cr_toolbar.html.ts, 24x24 por CSS): anel do Chrome branco -> símbolo branco.
# No tema claro o cr-toolbar usa chrome://theme/current-channel-logo = IDR_PRODUCT_LOGO_32 (acima).
svg_d="${src}/ui/webui/resources/images/chrome_logo_dark.svg"; svg_s="${br}/../aerographene-mark-white.svg"
[ -f "$svg_d" ] && [ -f "$svg_s" ] || { echo "branding: chrome_logo_dark.svg ou origem ausente" >&2; exit 1; }
if ! cmp -s "$svg_s" "$svg_d"; then cp -f "$svg_s" "$svg_d"; n=$((n+1)); fi

echo "branding: ${n} ícones sobrescritos, ${same} já aplicados (${#MAP[@]} no mapa)"
