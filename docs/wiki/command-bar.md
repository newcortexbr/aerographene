# command bar

a command bar é o popup de sugestões da barra de URL (omnibox), desenhado como painel flutuante (`menus-command-bar.patch`, ícones por tipo em `command-bar-type-icons.patch`, layout centralizado em `commandbar-centered.patch`). O painel tem 800 px, fica centrado na janela a um quarto da altura (em todos os modos), com uma linha de busca no topo (lupa e texto) e as sugestões abaixo. A linha de busca só espelha o texto: a edição continua na barra de URL, que mantém o foco.

## como abrir

- clique na URL ou Ctrl+L: o painel abre centrado na janela (mesmo layout do Ctrl+T); Enter navega na aba atual.
- Ctrl+T (v0.3, `commandbar-f3.patch`): a barra recebe o foco vazia e o painel abre com 640 px (limitado à janela - 16 px), centrado na horizontal da janela e a um quarto da altura. Mesmo sem sugestões ele aparece, com uma linha vazia. Enter abre o resultado numa aba nova; Esc ou clique fora fecham sem criar aba e devolvem a URL da aba atual à barra (Esc devolve o foco à página).
- menu "Nova aba" e botão `+` continuam criando a aba vazia, como antes.
- `t:`, `t: <comando>`, `o:` e `o: <termo>` funcionam igual nos dois modos (ver [terminal](terminal.md) e [notas](notas.md)).

## limites

- o campo dentro do painel é um espelho: sem cursor próprio, mostra o texto da barra (com autocompletar inline) e não acompanha o texto temporário das setas.
- o painel ainda não tem a ação "Switch to Tab" com botão à direita; as linhas mostram o rótulo do tipo ("aba aberta", "histórico"...).
- com uma sugestão escolhida pelas setas, o primeiro Esc só desfaz a escolha; o segundo fecha.
- o rótulo de atalho Ctrl+T sai do item "Nova aba" do menu, porque o atalho agora é de outro comando.

## cores e ícone

- `t:` e `o:` no começo do texto: o prefixo aparece na cor de destaque do tema (`ui::kColorSysPrimary`) e o resto na cor normal (`kColorOmniboxText`). Antes o prefixo usava `kColorOmniboxResultsUrl`, que o tema não sobrescreve e ficava azul Material; o texto lido como URL também ficava esmaecido.
- chip de páginas internas (`aerographene://notes` etc.): o ícone é o símbolo do aerographene, não mais o logo do Chromium.

## resumo para agentes

- comando novo `IDC_AERO_COMMAND_BAR` (34076, `chrome_command_ids.h`), ligado ao Ctrl+T em `accelerator_table.cc` no lugar de `IDC_NEW_TAB`; executado em `BrowserCommandController` (foco na barra, `SetUserText("")`, flag, `UpdatePopupAppearance`). Sem barra de URL visível cai no `NewTab` antigo.
- estado: `LocationBar::aero_command_bar()` (flag simples em `location_bar.h`).
- `OmniboxPopupViewViews`: com o flag, o popup fica aberto mesmo sem resultado; `GetTargetBounds` (ramo aerographene, `commandbar-centered.patch`) centra o painel de 800 px na janela e soma `RoundedOmniboxResultsFrame::kAeroHeaderHeight` (56) à altura. A linha de busca é criada no construtor do frame e atualizada por `PopupWidget::SetAeroHeaderText` em `UpdatePopupAppearance`.
- cor do prefixo em `OmniboxViewViews::AeroApplyCommandLook`; ícone do chip em `components/omnibox/browser/vector_icons/{chrome_product,product_chrome_refresh_old}.icon`.
- `OmniboxPopupCloser::CloseWithReason`: qualquer motivo exceto `kRevertAll` limpa o flag, fecha o popup e faz `RevertAll` (Esc foca a página). `kRevertAll` não limpa porque `OpenMatch` reverte antes de `OnAutocompleteAccept`.
- `ChromeOmniboxClient::OnAutocompleteAccept`: com o flag, `CURRENT_TAB` vira `NEW_FOREGROUND_TAB` e o flag é limpo.
- validação: `-fsyntax-only` dos 3 `.cc` de omnibox no overlay do Cezanne (ninja completo falha no esbuild do devtools); aparência e comportamento no navegador não testados (ver `patches/README.md`).
