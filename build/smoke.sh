#!/usr/bin/env bash
# smoke test do pacote: extrai o tarball, confere libs e abre uma página em headless.
# uso: bash build/smoke.sh <aerographene-*.tar.zst>
set -euo pipefail

tarball="${1:?uso: smoke.sh <tarball .tar.zst>}"

# host do runner não tem zstd: reexecuta dentro da imagem do builder
if ! command -v unzstd >/dev/null 2>&1 && [ -z "${AERO_SMOKE_IN_DOCKER:-}" ]; then
    tdir="$(cd "$(dirname "$tarball")" && pwd)"
    sdir="$(cd "$(dirname "$0")" && pwd)"
    exec docker run --rm -e AERO_SMOKE_IN_DOCKER=1 \
        -v "${tdir}:/art:ro" -v "${sdir}:/smoke:ro" \
        aerographene-builder:v2 bash /smoke/smoke.sh "/art/$(basename "$tarball")"
fi
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT

tar -C "$tmp" --use-compress-program=unzstd -xf "$tarball"
app="$(find "$tmp" -mindepth 1 -maxdepth 1 -type d | head -1)"
bin="${app}/aerographene"
[ -x "$bin" ] || { echo "smoke: binário ausente em ${app}" >&2; exit 1; }

echo "== libs ausentes"
missing="$(ldd "${app}/chrome" | grep 'not found' || true)"
if [ -n "$missing" ]; then echo "$missing"; echo "smoke: falta biblioteca no host" >&2; exit 1; fi
echo "nenhuma"

echo "== versão"
timeout 60 "$bin" --version

echo "== headless: abrir página"
page='data:text/html,<title>aero</title><p id="m">aerographene-smoke-ok</p>'
out="$(timeout 120 "$bin" --headless=new --no-sandbox --disable-gpu \
    --user-data-dir="${tmp}/profile" --dump-dom "$page" 2>"${tmp}/stderr" || true)"
if grep -q 'aerographene-smoke-ok' <<<"$out"; then
    echo "smoke: ok (iniciou e renderizou a página)"
else
    echo "smoke: falhou; stderr:" >&2
    tail -40 "${tmp}/stderr" >&2
    exit 1
fi
