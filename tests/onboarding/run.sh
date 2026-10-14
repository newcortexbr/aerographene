#!/usr/bin/env bash
# Verifica a página chrome://setup (setup.html/.js/.css) num Chrome headless
# com um backend simulado em memória no lugar de chrome.send (mock.js).
# Uso: tests/onboarding/run.sh <dir com setup.html, setup.js, setup.css, wordmark.svg> [chrome-headless-shell]
# O dir vem da árvore com a série aplicada (chrome/browser/resources/aero_setup).
# Sem o segundo argumento usa o chrome-headless-shell do Playwright.
# Roda 4 variações: fluxo completo, skip, complete que falha, sem permissão de
# navegador padrão. Não prova Trusted Types/CSP do WebUI real nem o SetupHandler
# em C++; a verificação estática de rede/recursos externos é feita aqui em grep.
set -euo pipefail
res="${1:?dir dos recursos aero_setup}"
chrome="${2:-$(ls "$HOME"/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell | tail -1)}"
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"; trap 'kill "${srv:-0}" 2>/dev/null || true' EXIT
cp "$res"/{setup.js,setup.css,wordmark.svg} "$tmp"/
cp "$here"/{mock.js,test.js} "$tmp"/
sed "s#<script type=\"module\" src=\"setup.js\"></script>#<script src=\"mock.js\"></script>\n<script type=\"module\" src=\"setup.js\"></script>\n<script type=\"module\" src=\"test.js\"></script>#" "$res/setup.html" > "$tmp/index.html"

ok=0
echo "== estático: nada de URL externa nos recursos"
# o xmlns do SVG é um identificador, não uma requisição
if grep -n -E 'https?://|url\(|@import|@font-face|fetch\(|XMLHttpRequest|WebSocket|innerHTML|insertAdjacentHTML' \
    "$res"/setup.html "$res"/setup.js "$res"/setup.css | grep -v -E 'chrome://|^\S+:[0-9]+:\s*(//|\*|/\*)'; then
  echo "FAIL recurso externo ou API insegura"; ok=1
else echo "PASS sem http(s), url(), fetch, innerHTML"; fi
if grep -o -E 'https?://[^"]+' "$res/wordmark.svg" | grep -v -x 'http://www.w3.org/2000/svg'; then
  echo "FAIL wordmark com referência externa"; ok=1
else echo "PASS wordmark só com o xmlns"; fi

port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
(cd "$tmp" && exec python3 -m http.server "$port" --bind 127.0.0.1 >/dev/null 2>&1) & srv=$!
sleep 1
for page in "index.html?t=flow" "index.html?t=skip" "index.html?t=failcomplete&failcomplete=1" "index.html?t=nodefault&nodefault=1"; do
  HOME="$tmp/h" timeout 100 "$chrome" --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage \
    --disable-crash-reporter --disable-breakpad --no-first-run --user-data-dir="$tmp/prof" \
    --window-size=1280,900 --virtual-time-budget=10000 --dump-dom "http://127.0.0.1:$port/$page" 2>/dev/null > "$tmp/dom.html" || true
  echo "== $page"
  sed -n '/<pre id="results">/,/<\/pre>/p' "$tmp/dom.html" | sed 's/<[^>]*>//g'
  grep -q -E '^(FAIL|ERRO)' <(sed 's/<[^>]*>//g' "$tmp/dom.html") && ok=1
  grep -q '^PASS' <(sed 's/<[^>]*>//g' "$tmp/dom.html") || ok=1
done
exit $ok
