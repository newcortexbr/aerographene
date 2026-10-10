#!/bin/bash
# renderiza branding/png/* a partir dos SVGs (rsvg-convert + ImageMagick)
set -euo pipefail
cd "$(dirname "$0")"
python3 make.py
mkdir -p png
for n in 16 22 24 32 48 64 128 256; do
    rsvg-convert -w "$n" -h "$n" aerographene-icon.svg -o "png/aerographene-icon-$n.png"
    for c in black white; do
        rsvg-convert -w "$n" -h "$n" -a "aerographene-mark-$c.svg" -o "/tmp/.mark-$$.png"
        magick "/tmp/.mark-$$.png" -background none -gravity center -extent "${n}x${n}" "PNG32:png/aerographene-mark-$c-$n.png"
    done
done
rm -f "/tmp/.mark-$$.png"
magick png/aerographene-icon-{16,24,32,48,64,128,256}.png png/aerographene-icon.ico

# logotipo (símbolo + texto, raster provisório em src/) como product_logo_name_22: 97x22 (1x) e 194x44 (2x)
for c in black white; do
    for s in 1 2; do
        magick "src/logo-$c.png" -background none -resize "$((97*s))x$((22*s))" -gravity center -extent "$((97*s))x$((22*s))" \
            "PNG32:png/logo-name-22-$c-${s}x.png"
    done
done
# logotipo com nome de chrome://version (IDR_PRODUCT_LOGO[_WHITE], components/resources): 171x32 (1x) e 342x64 (2x)
for c in black white; do
    for s in 1 2; do
        magick "src/logo-$c.png" -background none -resize "$((171*s))x$((32*s))" -gravity center -extent "$((171*s))x$((32*s))" \
            "PNG32:png/logo-name-32-$c-${s}x.png"
    done
done
