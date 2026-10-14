# command bar

a command bar é o popup de sugestões da barra de URL (omnibox), desenhado como painel flutuante (`menus-command-bar.patch`, ícones por tipo em `command-bar-type-icons.patch`). Não existe um campo de texto dentro do painel: o texto digitado fica na própria barra de URL.

## como abrir

- clique na URL ou Ctrl+L: o painel de 600 px abre logo abaixo da barra; Enter navega na aba atual.
- Ctrl+T (v0.3, `commandbar-f3.patch`): a barra recebe o foco vazia e o painel abre com 640 px (limitado à janela - 16 px), centrado na horizontal da janela e a um quarto da altura. Mesmo sem sugestões ele aparece, com uma linha vazia. Enter abre o resultado numa aba nova; Esc ou clique fora fecham sem criar aba e devolvem a URL da aba atual à barra (Esc devolve o foco à página).
- menu "Nova aba" e botão `+` continuam criando a aba vazia, como antes.
- `t:`, `t: <comando>`, `o:` e `o: <termo>` funcionam igual nos dois modos (ver [terminal](terminal.md) e [notas](notas.md)).

## limites

- o texto que você digita aparece na barra de URL do topo/sidebar, não dentro do painel central.
- com uma sugestão escolhida pelas setas, o primeiro Esc só desfaz a escolha; o segundo fecha.
- o rótulo de atalho Ctrl+T sai do item "Nova aba" do menu, porque o atalho agora é de outro comando.

## resumo para agentes

- comando novo `IDC_AERO_COMMAND_BAR` (34076, `chrome_command_ids.h`), ligado ao Ctrl+T em `accelerator_table.cc` no lugar de `IDC_NEW_TAB`; executado em `BrowserCommandController` (foco na barra, `SetUserText("")`, flag, `UpdatePopupAppearance`). Sem barra de URL visível cai no `NewTab` antigo.
- estado: `LocationBar::aero_command_bar()` (flag simples em `location_bar.h`).
- `OmniboxPopupViewViews`: com o flag, o popup fica aberto mesmo sem resultado e `GetTargetBounds` centra o painel na janela.
- `OmniboxPopupCloser::CloseWithReason`: qualquer motivo exceto `kRevertAll` limpa o flag, fecha o popup e faz `RevertAll` (Esc foca a página). `kRevertAll` não limpa porque `OpenMatch` reverte antes de `OnAutocompleteAccept`.
- `ChromeOmniboxClient::OnAutocompleteAccept`: com o flag, `CURRENT_TAB` vira `NEW_FOREGROUND_TAB` e o flag é limpo.
- validação: objetos compilados no overlay do Cezanne; comportamento no navegador não testado (ver `patches/README.md`).
