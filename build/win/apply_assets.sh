#!/bin/bash
# aerographene: ativos binários da build Windows (D3d), copiados para a árvore depois dos patches.
#   - ícones do app/documentos (.ico) no lugar dos do Chromium (chrome_exe.rc os referencia);
#   - JetBrains Mono (SIL OFL 1.1) + OFL.txt em chrome/app/theme/aerographene/fonts/
#     (alvo copy("aerographene_fonts") de windows-branding.patch os leva para <out>/fonts/).
# Idempotente; escreve por temporário + mv (nunca através de hardlink do CI); falha se um
# destino do upstream sumiu (mapa a revisar). Linux não usa este script.
# Uso: build/win/apply_assets.sh <raiz-do-src> [dir-branding]
set -euo pipefail

src="${1:?uso: $0 <raiz-do-src> [dir-branding]}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
br="${2:-${here}/../../branding}"

W=chrome/app/theme/chromium/win
F=chrome/app/theme/aerographene/fonts
# destino (relativo ao src) | origem (relativa ao dir de branding) | destino precisa existir (1) ou é novo (0)
MAP=(
    "$W/chromium.ico|win/aerographene.ico|1"
    "$W/chromium_doc.ico|win/aerographene.ico|1"
    "$W/chromium_pdf.ico|win/aerographene.ico|1"
    "$W/app_list.ico|win/aerographene.ico|1"
    "$F/JetBrainsMono-Regular.ttf|fonts/jetbrains-mono/JetBrainsMono-Regular.ttf|0"
    "$F/JetBrainsMono-Bold.ttf|fonts/jetbrains-mono/JetBrainsMono-Bold.ttf|0"
    "$F/OFL.txt|fonts/jetbrains-mono/OFL.txt|0"
)

n=0; same=0
for entry in "${MAP[@]}"; do
    IFS='|' read -r dest from must <<<"$entry"
    d="${src}/${dest}"; s="${br}/${from}"
    [ -f "$s" ] || { echo "assets win: origem ausente: ${s}" >&2; exit 1; }
    if [ "$must" = 1 ] && [ ! -f "$d" ]; then
        echo "assets win: destino ausente: ${dest}" >&2; exit 1
    fi
    if [ -f "$d" ] && cmp -s "$s" "$d"; then same=$((same+1)); continue; fi
    mkdir -p "$(dirname "$d")"
    cp "$s" "${d}.aero-new" && mv -f "${d}.aero-new" "$d"
    n=$((n+1))
done
echo "assets win: ${n} copiados, ${same} já aplicados (${#MAP[@]} no mapa)"
