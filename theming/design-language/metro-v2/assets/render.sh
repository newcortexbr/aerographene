#!/usr/bin/env bash
# exporta dark.png e light.png (1599x872) com Chromium headless local, sem rede. rodar build.py antes.
set -euo pipefail
cd "$(dirname "$0")/.."
CH="${CHROME:-$HOME/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
for n in dark light; do
  "$CH" --no-sandbox --hide-scrollbars --force-device-scale-factor=1 --disable-background-networking \
    --user-data-dir="$TMP/p" --window-size=1599,872 --screenshot="$PWD/$n.png" "file://$PWD/$n.html" >/dev/null 2>&1
done
