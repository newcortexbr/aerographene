# seletor de abas (Ctrl+Tab)

Painel centrado na janela para trocar de aba por uso recente, no estilo do Arc. Mockup aprovado: `theming/mockups/tab-switcher/thumbs.png` (branch `wip-switcher`).

## como usar

- Ctrl+Tab abre o painel com a aba anterior (2ª no uso recente) já selecionada.
- com Ctrl segurado, cada Tab avança e Shift+Tab volta (dá a volta no fim e no começo).
- soltar Ctrl troca para a aba selecionada.
- Esc, clique fora do painel ou trocar de janela cancelam sem trocar.
- clique num card troca direto para aquela aba.
- Ctrl+PgDn e Ctrl+PgUp continuam como antes: próxima e anterior na ordem da barra, sem painel.
- com uma aba só, Ctrl+Tab mantém o comportamento original do Chromium.

## o que aparece

- todas as abas da janela (o space atual), fixadas abertas incluídas, em ordem de uso recente: a aba atual primeiro, as outras pela última ativação.
- grade de até 4 colunas e até 3 linhas visíveis; com mais abas a grade rola e mantém a selecionada visível. Janelas estreitas ou baixas reduzem colunas e linhas.
- cada card: miniatura da página, favicon, título e host; aba fixada leva o ícone de pin.
- cabeçalho "RECENT TABS" com o contador (`3 / 8`); rodapé com a legenda dos atalhos.
- cores e raio vêm do tema ativo (`ui::kColorSys*`, raio de controle do aerographene); sem o visual de bubble do Chromium.

## miniaturas e memória

- o painel só mostra miniaturas que o Chromium já guardou para o hover card (`ThumbnailTabHelper`). Não força captura nova.
- aba descartada, congelada, nunca vista na sessão ou sem miniatura mostra o favicon grande no lugar.
- nada é gravado em disco; ao fechar o painel as imagens são liberadas.
- observar uma miniatura existente pode fazer o Chromium atualizá-la em abas carregadas (mesmo mecanismo do hover card); o custo real não foi medido.

## limites conhecidos

- textos do painel em inglês, fixos no código (sem `IDS_*`/tradução).
- Esc é consumido por um `ui::EventHandler` pré-alvo na janela do browser: cancela só o seletor e não chega à página nem sai de tela cheia.
- se o Ctrl já foi solto quando o comando chega (o monitor só nasce depois), não há API portátil para ler o estado do modificador; a primeira tecla sem Ctrl cancela (não confirma).
- só a janela atual: abas de outros spaces (outra janela/perfil) não entram.
- qualquer aba aberta, fechada ou movida enquanto o painel está aberto cancela o painel.
- não testado no navegador; Wayland e Windows não verificados (ver resumo).

## resumo para agentes

- patch: `patches/aerographene/tab-switcher.patch` (fim da série). Arquivos novos `chrome/browser/ui/views/frame/aerographene_tab_switcher.{h,cc}`, listados em `chrome/browser/ui/BUILD.gn` ao lado de `aerographene_topbar_row`.
- entrada: `BrowserCommandController` nos casos `IDC_CYCLE_TO_NEXT_TAB` / `IDC_CYCLE_TO_PREV_TAB` (upstream já liga Ctrl+Tab a eles em `accelerator_table.cc` e os reserva contra páginas). Chama `aerographene::ShowOrAdvanceTabSwitcher(browser, forward)`; se devolver `false` (1 aba, sem `BrowserView`) segue o caminho original. `IDC_SELECT_NEXT/PREVIOUS_TAB` (PgDn/PgUp) intocados. Os patches `tab-cycling-mru` não estão na série e não devem voltar.
- estado: um `TabSwitcher` global por vez (`g_switcher`), dono de um `views::Widget` `TYPE_BUBBLE`, `CLIENT_OWNS_WIDGET`, `Activatable::kNo`, filho do widget do browser, centrado na janela. Fecha com `Finish(commit)` e `DeleteSoon`.
- MRU: aba ativa primeiro, demais por `WebContents::GetLastActiveTimeTicks()` (stable sort). Seleção inicial índice 1 (Ctrl+Tab) ou último (Ctrl+Shift+Tab).
- eventos: `views::EventMonitor::CreateWindowMonitor` na janela do browser (`kKeyPressed`, `kKeyReleased`, `kMousePressed`): soltar `VKEY_CONTROL` confirma; clique no browser cancela; Esc é tratado por `EscFilter` (pré-alvo, consome o evento); tecla sem `EF_CONTROL_DOWN` cancela (soltura perdida; tecla alheia nunca confirma). `WidgetObserver` no browser cancela em perda de ativação, ocultação ou destruição; na destruição da janela o widget do seletor é solto sem `Hide()`; `TabStripModelObserver` cancela em qualquer mudança que não seja só seleção.
- miniaturas: `ThumbnailTabHelper::thumbnail()`; só assina se `has_data()` e a aba não foi descartada (`SetSizeHint` + `RequestThumbnailImage`). O Helium não desliga a captura (`lazy-session-restore.patch` só impede recarregar aba restaurada pendente ao observar a miniatura).
- validação feita: série aplica com `-F0` numa cópia de `tree3` no Cezanne; compila e liga na build avx2 completa verde (run 38671160082 sobre `82a7bf3`, 15/10/2026), que substitui o `-fsyntax-only` que estava pendente. Não feito: smoke test do pacote, teste no navegador, Wayland, Windows, medição de memória. Limite conhecido: Ctrl solto antes de o painel existir só é mitigado (a primeira tecla sem Ctrl cancela, não confirma). Atalhos em conjunto: [atalhos](atalhos.md).
