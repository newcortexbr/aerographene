#!/usr/bin/env bash
# regenera os assets do site (prints webp, fontes woff2, themes.json, themes.css) a partir de tools/themes.src.json
# e dos mockups em theming/design-language (override: DL=/caminho/design-language).
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 tools/build_gallery.py "$@"
