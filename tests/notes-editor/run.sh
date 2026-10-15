#!/usr/bin/env bash
# Verifica a página chrome://notes (notes.js + editor.js) num Chrome headless
# com um backend simulado em memória no lugar de chrome.send (mock.js).
# Uso: tests/notes-editor/run.sh <dir com notes.html,notes.js,editor.js,markdown.js,notes.css> <chrome>
# O dir vem da árvore com a série aplicada (chrome/browser/resources/aero_notes).
# index-f2.html: rolagem por painel e elementos novos, janela 1000x600.
# index-f2b.html: lateral com modos, abas, contagens, status bar, tags, backlinks, recentes.
# Não prova Trusted Types/CSP do WebUI real nem o handler C++.
set -euo pipefail
res="${1:?dir dos recursos aero_notes}"; chrome="${2:?binário do chrome/aerographene}"
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"; trap 'pkill -P "${srv:-0}" 2>/dev/null || true; kill "${srv:-0}" 2>/dev/null || true' EXIT
cp "$res"/{notes.js,editor.js,markdown.js,notes.css} "$tmp"/
cp "$here"/{mock.js,test.js,test-q.js,test-f2.js,test-f2b.js} "$tmp"/
mk() { sed "s#<script type=\"module\" src=\"notes.js\"></script>#<script src=\"mock.js\"></script>\n<script type=\"module\" src=\"notes.js\"></script>\n<script type=\"module\" src=\"$1\"></script>#" "$res/notes.html" > "$tmp/$2"; }
mk test.js index.html; mk test-q.js index-q.html; mk test-f2.js index-f2.html; mk test-f2b.js index-f2b.html
(cd "$tmp" && python3 -m http.server 8123 --bind 127.0.0.1 >/dev/null 2>&1) & srv=$!
sleep 1
ok=0
for page in index.html "index-q.html?q=forte" index-f2.html index-f2b.html; do
  HOME="$tmp/h" timeout 100 "$chrome" --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage \
    --disable-crash-reporter --disable-breakpad --no-first-run --user-data-dir="$tmp/prof" \
    --window-size=1000,600 --virtual-time-budget=10000 --dump-dom "http://127.0.0.1:8123/$page" 2>/dev/null > "$tmp/dom.html" || true
  sed -n '/<pre id="results">/,/<\/pre>/p' "$tmp/dom.html" | sed 's/<[^>]*>//g'
  grep -q -E '^(FAIL|ERRO)' <(sed 's/<[^>]*>//g' "$tmp/dom.html") && ok=1
  grep -q '^PASS' <(sed 's/<[^>]*>//g' "$tmp/dom.html") || ok=1
done
exit $ok
