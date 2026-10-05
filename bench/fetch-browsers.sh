#!/usr/bin/env bash
# baixa e extrai os navegadores da linha de base em bench/browsers/ (fora do git).
# tarballs em vez de AppImage montado, para o mount FUSE não entrar no tempo de abertura.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p browsers && cd browsers

HELIUM_VER=0.18.3.1
UNGOOGLED_VER=154.0.8037.97-1
THORIUM_VER=154.0.8037.45

get() { [ -f "$2" ] || curl -fL --retry 3 -o "$2.part" "$1" && { [ -f "$2" ] || mv "$2.part" "$2"; }; }

get "https://github.com/imputnet/helium-linux/releases/download/${HELIUM_VER}/helium-${HELIUM_VER}-x86_64_linux.tar.xz" helium.tar.xz
get "https://github.com/ungoogled-software/ungoogled-chromium-portablelinux/releases/download/${UNGOOGLED_VER}/ungoogled-chromium-${UNGOOGLED_VER}-x86_64_linux.tar.xz" ungoogled.tar.xz
get "https://github.com/gz83/thorium/releases/download/M${THORIUM_VER}/Thorium_Browser_${THORIUM_VER}_AVX2.AppImage" thorium.AppImage

[ -d helium ] || { mkdir helium && tar -xf helium.tar.xz -C helium --strip-components=1; }
[ -d ungoogled ] || { mkdir ungoogled && tar -xf ungoogled.tar.xz -C ungoogled --strip-components=1; }
if [ ! -d thorium ]; then
  chmod +x thorium.AppImage
  ./thorium.AppImage --appimage-extract >/dev/null
  mv squashfs-root thorium
fi
printf '%s\n' "helium $HELIUM_VER" "ungoogled $UNGOOGLED_VER" "thorium $THORIUM_VER AVX2" > VERSIONS
echo ok
