#!/usr/bin/env bash
# Verifica a página chrome://notes (notes.js + editor.js) num Chrome headless
# com um backend simulado em memória no lugar de chrome.send (mock.js).
# Uso: tests/notes-editor/run.sh <dir com notes.html,notes.js,editor.js,markdown.js,notes.css> <chrome>
# O dir vem da árvore com a série aplicada (chrome/browser/resources/aero_notes).
# Não prova Trusted Types/CSP do WebUI real nem o handler C++.
set -euo pipefail
res="${1:?dir dos recursos aero_notes}"; chrome="${2:?binário do chrome/aerographene}"
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"; trap 'kill "${srv:-0}" 2>/dev/null || true' EXIT
cp "$res"/{notes.js,editor.js,markdown.js,notes.css} "$tmp"/
cp "$here"/{mock.js,test.js} "$tmp"/
sed 's#<script type="module" src="notes.js"></script>#<script src="mock.js"></script>\n<script type="module" src="notes.js"></script>\n<script type="module" src="test.js"></script>#' "$res/notes.html" > "$tmp/index.html"
(cd "$tmp" && python3 -m http.server 8123 --bind 127.0.0.1 >/dev/null 2>&1) & srv=$!
sleep 1
HOME="$tmp/h" timeout 100 "$chrome" --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --disable-crash-reporter --disable-breakpad --no-first-run --user-data-dir="$tmp/prof" \
  --virtual-time-budget=10000 --dump-dom http://127.0.0.1:8123/index.html 2>/dev/null > "$tmp/dom.html" || true
sed -n '/<pre id="results">/,/<\/pre>/p' "$tmp/dom.html" | sed 's/<[^>]*>//g'
! grep -q -E '^(FAIL|ERRO)' <(sed 's/<[^>]*>//g' "$tmp/dom.html") && grep -q '^PASS' <(sed 's/<[^>]*>//g' "$tmp/dom.html")
