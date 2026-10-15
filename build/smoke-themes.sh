#!/usr/bin/env bash
# prints reais da janela do navegador, um por tema embutido, sob Xvfb 1280x800.
# uso: bash build/smoke-themes.sh <aerographene-*.tar.zst> <dir-de-saida>
# tema = pref de perfil `aerographene.theme` escrita em <perfil>/Default/Preferences
# antes de abrir (o tema vale no início do processo). Perfil novo por tema;
# `aerographene.onboarding_completed` evita a página de primeira execução.
# páginas: URLs chrome:// na linha de comando são descartadas fora do headless
# (chrome/browser/ui/startup/url_util.cc), então elas vão em `session.startup_urls`
# (restore_on_startup 4); `helium.browser.layout` 2 = sidebar de abas, 0 = barra superior.
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

echo "== dependências (Xvfb, ImageMagick, openbox, fontconfig)"
export DEBIAN_FRONTEND=noninteractive
apt-get -y update >/dev/null
apt-get -y install --no-install-recommends xvfb imagemagick openbox x11-utils fontconfig >/dev/null

tmp="$(mktemp -d)"
trap 'kill $(jobs -p) 2>/dev/null || true; chown -R "${AERO_HOST_OWNER:-0:0}" "$outdir" 2>/dev/null || true; rm -rf -- "$tmp"' EXIT
tar -C "$tmp" --use-compress-program=unzstd -xf "$tarball"
app="$(find "$tmp" -mindepth 1 -maxdepth 1 -type d | head -1)"
bin="${app}/aerographene"
[ -x "$bin" ] || { echo "smoke-themes: binário ausente em ${app}" >&2; exit 1; }
# fontes dos temas que o pacote instala (tarball fonts/, como o PKGBUILD)
if [ -d "${app}/fonts" ]; then
    mkdir -p /usr/local/share/fonts/aerographene
    cp -r "${app}/fonts/." /usr/local/share/fonts/aerographene/
    fc-cache -f >/dev/null
    echo "== fontes: $(fc-list : family | grep -c -E 'Selawik|Doto|Pixelify Sans|Noto Serif|JetBrains Mono') faces dos temas"
else
    echo "smoke-themes: aviso: tarball sem fonts/; temas caem na família genérica" >&2
fi

export DISPLAY=:99
Xvfb :99 -screen 0 ${W}x${H}x24 -nolisten tcp >"${tmp}/xvfb.log" 2>&1 &
for _ in $(seq 1 50); do xdpyinfo >/dev/null 2>&1 && break; sleep 0.2; done
xdpyinfo >/dev/null 2>&1 || { echo "smoke-themes: Xvfb não subiu" >&2; cat "${tmp}/xvfb.log" >&2; exit 1; }
openbox >"${tmp}/wm.log" 2>&1 &
sleep 1

# abre o navegador com o tema, espera, captura a tela inteira (= a janela) e fecha
shot() { # tema arquivo layout [url...]  (sem url = só o que o navegador abre sozinho; a 1ª aba fica ativa)
    local theme="$1" file="$2" layout="$3" prof="${tmp}/prof-$1" pid urls="" u
    shift 3
    # perfil novo a cada captura: sem restauro de sessão da captura anterior
    rm -rf -- "$prof"
    mkdir -p "${prof}/Default"
    # "onboarding" = perfil novo sem prefs e sem --no-first-run: abre chrome://setup sozinho
    local extra=(--no-first-run)
    if [ "$theme" = onboarding ]; then
        extra=()
    else
        for u in "$@"; do urls="${urls:+${urls},}\"${u}\""; done
        printf '{"aerographene":{"theme":"%s","onboarding_completed":true},"helium":{"browser":{"layout":%d}},"session":{"restore_on_startup":%d,"startup_urls":[%s]}}' \
            "$theme" "$layout" "$([ -n "$urls" ] && echo 4 || echo 5)" "$urls" >"${prof}/Default/Preferences"
    fi
    # --test-type suprime a infobar de flag não suportada (--no-sandbox, exigido como root no container)
    HOME="${tmp}/home" "$bin" --no-sandbox --test-type --disable-gpu --disable-dev-shm-usage \
        --disable-crash-reporter --disable-breakpad "${extra[@]}" --no-default-browser-check \
        --user-data-dir="$prof" --window-position=0,0 --window-size=${W},${H} \
        >>"${tmp}/chrome-${theme}.log" 2>&1 &
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
    shot "$t" "${t}.png" 0 chrome://newtab || fail=1
    shot "$t" "${t}-settings.png" 0 chrome://settings/appearance || fail=1
    # várias abas (a 1ª, ativa, é as notas): a tabstrip e as superfícies mostram o tema
    shot "$t" "${t}-tabs.png" 0 chrome://notes chrome://settings/appearance chrome://version \
        chrome://history chrome://newtab || fail=1
    # sidebar de abas com as mesmas abas extras: marcador da aba ativa do tema
    shot "$t" "${t}-sidebar.png" 2 chrome://newtab chrome://settings/appearance chrome://notes \
        chrome://version chrome://history || fail=1
done

echo "== onboarding (perfil novo)"
shot onboarding "onboarding.png" 0 || fail=1

ls -l "$outdir"
for t in "${themes[@]}"; do
    for s in "" -settings -tabs -sidebar; do
        [ -s "${outdir}/${t}${s}.png" ] || { echo "smoke-themes: falta ${t}${s}.png" >&2; fail=1; }
    done
done
exit "$fail"
