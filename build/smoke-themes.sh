#!/usr/bin/env bash
# prints reais da janela do navegador, um por tema embutido, sob Xvfb 1280x800.
# uso: bash build/smoke-themes.sh <aerographene-*.tar.zst> <dir-de-saida>
# tema = pref de perfil `aerographene.theme` escrita em <perfil>/Default/Preferences
# antes de abrir (o tema vale no início do processo). Perfil novo por tema;
# `aerographene.onboarding_completed` evita a página de primeira execução.
set -euo pipefail

tarball="${1:?uso: smoke-themes.sh <tarball .tar.zst> <dir-de-saida>}"
outdir="${2:?uso: smoke-themes.sh <tarball .tar.zst> <dir-de-saida>}"
themes=(default pixelized metro-v2 e-ink-gb graphite classical e-ink cli)
W=1280
H=800

mkdir -p "$outdir"
if [ -z "${AERO_SMOKE_IN_DOCKER:-}" ]; then
    tdir="$(cd "$(dirname "$tarball")" && pwd)"
    sdir="$(cd "$(dirname "$0")" && pwd)"
    odir="$(cd "$outdir" && pwd)"
    exec docker run --rm -u 0:0 -e AERO_SMOKE_IN_DOCKER=1 \
        -e "AERO_HOST_OWNER=$(id -u):$(id -g)" \
        -v "${tdir}:/art:ro" -v "${sdir}:/smoke:ro" -v "${odir}:/out" \
        aerographene-builder:v2 bash /smoke/smoke-themes.sh "/art/$(basename "$tarball")" /out
fi

echo "== dependências (Xvfb, ImageMagick, openbox, JetBrains Mono)"
export DEBIAN_FRONTEND=noninteractive
apt-get -y update >/dev/null
apt-get -y install --no-install-recommends xvfb imagemagick openbox x11-utils fonts-jetbrains-mono >/dev/null

tmp="$(mktemp -d)"
trap 'kill $(jobs -p) 2>/dev/null || true; chown -R "${AERO_HOST_OWNER:-0:0}" "$outdir" 2>/dev/null || true; rm -rf -- "$tmp"' EXIT
tar -C "$tmp" --use-compress-program=unzstd -xf "$tarball"
app="$(find "$tmp" -mindepth 1 -maxdepth 1 -type d | head -1)"
bin="${app}/aerographene"
[ -x "$bin" ] || { echo "smoke-themes: binário ausente em ${app}" >&2; exit 1; }

export DISPLAY=:99
Xvfb :99 -screen 0 ${W}x${H}x24 -nolisten tcp >"${tmp}/xvfb.log" 2>&1 &
for _ in $(seq 1 50); do xdpyinfo >/dev/null 2>&1 && break; sleep 0.2; done
xdpyinfo >/dev/null 2>&1 || { echo "smoke-themes: Xvfb não subiu" >&2; cat "${tmp}/xvfb.log" >&2; exit 1; }
openbox >"${tmp}/wm.log" 2>&1 &
sleep 1

# abre o navegador com o tema, espera, captura a tela inteira (= a janela) e fecha
shot() { # tema arquivo [url...]  (sem url = só o que o navegador abre sozinho; a 1ª aba fica ativa)
    local theme="$1" file="$2" prof="${tmp}/prof-$1" pid
    shift 2
    # perfil novo a cada captura: sem restauro de sessão da captura anterior
    rm -rf -- "$prof"
    mkdir -p "${prof}/Default"
    # "onboarding" = perfil novo sem prefs e sem --no-first-run: abre chrome://setup sozinho
    local extra=(--no-first-run)
    if [ "$theme" = onboarding ]; then
        extra=()
    else
        printf '{"aerographene":{"theme":"%s","onboarding_completed":true}}' "$theme" \
            >"${prof}/Default/Preferences"
    fi
    # --test-type suprime a infobar de flag não suportada (--no-sandbox, exigido como root no container)
    HOME="${tmp}/home" "$bin" --no-sandbox --test-type --disable-gpu --disable-dev-shm-usage \
        --disable-crash-reporter --disable-breakpad "${extra[@]}" --no-default-browser-check \
        --user-data-dir="$prof" --window-position=0,0 --window-size=${W},${H} \
        "$@" >>"${tmp}/chrome-${theme}.log" 2>&1 &
    pid=$!
    sleep "${AERO_SHOT_WAIT:-12}"
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "smoke-themes: navegador morreu (tema ${theme})" >&2
        tail -40 "${tmp}/chrome-${theme}.log" >&2
        return 1
    fi
    import -window root "png:${outdir}/${file}"
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    sleep 2
    pkill -f "user-data-dir=${prof}" 2>/dev/null || true
}

fail=0
for t in "${themes[@]}"; do
    echo "== tema ${t}"
    shot "$t" "${t}.png" chrome://newtab || fail=1
    shot "$t" "${t}-settings.png" chrome://settings/appearance || fail=1
    # várias abas (a 1ª, ativa, é as notas): a tabstrip e as superfícies mostram o tema
    shot "$t" "${t}-tabs.png" chrome://notes chrome://settings/appearance chrome://version \
        chrome://about chrome://newtab || fail=1
done

echo "== onboarding (perfil novo)"
shot onboarding "onboarding.png" || fail=1

ls -l "$outdir"
for t in "${themes[@]}"; do
    [ -s "${outdir}/${t}.png" ] || { echo "smoke-themes: falta ${t}.png" >&2; fail=1; }
done
exit "$fail"
