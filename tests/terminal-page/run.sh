#!/usr/bin/env bash
# Verifica a página chrome://terminal (terminal.js + banner.js + xterm.js) num
# Chrome headless com um TerminalHandler simulado (mock.js) no lugar de
# chrome.send. Uso: tests/terminal-page/run.sh <dir aero_terminal> <chrome>
# O dir vem da árvore com a série aplicada
# (chrome/browser/resources/aero_terminal). Não prova a CSP/Trusted Types do
# WebUI real, o handler C++ nem o pty; atalhos são eventos sintéticos.
set -euo pipefail
res="${1:?dir dos recursos aero_terminal}"; chrome="${2:?binário do chrome/aerographene}"
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"; trap 'kill "${srv:-0}" 2>/dev/null || true' EXIT
cp "$res"/{terminal.js,banner.js,terminal.css,xterm.mjs,xterm.css} "$tmp"/
cp "$here"/{mock.js,hook.js,test.js} "$tmp"/
sed "s#<script type=\"module\" src=\"terminal.js\"></script>#<script src=\"mock.js\"></script>\n<script type=\"module\" src=\"hook.js\"></script>\n<script type=\"module\" src=\"terminal.js\"></script>\n<script type=\"module\" src=\"test.js\"></script>#" "$res/terminal.html" > "$tmp/index.html"
port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
(cd "$tmp" && exec python3 -m http.server "$port" --bind 127.0.0.1 >/dev/null 2>&1) & srv=$!
sleep 1
ok=0
for page in "index.html?w=2" "index.html?new=1"; do
  HOME="$tmp/h" timeout 100 "$chrome" --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage \
    --disable-crash-reporter --disable-breakpad --no-first-run --user-data-dir="$tmp/prof" \
    --window-size=1280,800 --virtual-time-budget=10000 --dump-dom "http://127.0.0.1:$port/$page" 2>/dev/null > "$tmp/dom.html" || true
  echo "== $page"
  sed -n '/<pre id="results">/,/<\/pre>/p' "$tmp/dom.html" | sed 's/<[^>]*>//g'
  grep -q -E '^(FAIL|ERRO)' <(sed 's/<[^>]*>//g' "$tmp/dom.html") && ok=1
  grep -q '^PASS' <(sed 's/<[^>]*>//g' "$tmp/dom.html") || ok=1
done
exit $ok
