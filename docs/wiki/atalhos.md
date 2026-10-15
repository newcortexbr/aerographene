# atalhos

os atalhos que a série de patches muda em relação ao Chromium. Tudo o mais continua como no upstream. Estado: compilado na build avx2 verde (run 38671160082 sobre `82a7bf3`); nenhum deles foi usado no navegador.

## o que muda

- Ctrl+T: abre a command bar centrada na janela, não uma aba vazia. Enter abre o destino em aba nova; Esc ou clique fora fecham sem criar aba. Menu "Nova aba" e botão `+` seguem criando aba. Ver [command bar](command-bar.md). Patch `commandbar-f3`.
- Ctrl+Tab e Ctrl+Shift+Tab: abrem o seletor de abas por uso recente (MRU) com miniaturas; soltar Ctrl troca. Ctrl+PgDn e Ctrl+PgUp não mudam. Ver [tab switcher](tab-switcher.md). Patch `tab-switcher`.
- Ctrl+N: com a aba ativa em `aerographene://notes` (janela normal), cria nota nova; em qualquer outra aba abre nova janela, como antes. O item "Nova janela" do menu continua abrindo janela e perde o rótulo "Ctrl+N" (o atalho agora é de outro comando, `IDC_AERO_NEW_WINDOW_OR_NOTE`). Ver [notas](notas.md). Patch `notes-ctrl-n`.
- Ctrl+L e clique na URL: abrem a command bar com o endereço atual.

## o que saiu

- os extras de teclado do Helium (`helium/core/keyboard-shortcuts.patch`), a ordem MRU do Ctrl+Tab do Helium/Brave (`tab-cycling-mru`) e outros extras fora do escopo foram removidos da série (detalhes em `patches/README.md`). O Ctrl+Tab MRU atual é código novo, sem reaproveitar os removidos.

## limites

- o rótulo de atalho some do menu nos itens "Nova aba" e "Nova janela", porque o atalho passou a outro comando.
- no seletor de abas, se Ctrl já foi solto quando o comando chega, não há API portátil para ler o modificador: o caso só é mitigado (a primeira tecla sem Ctrl cancela).
- Wayland e Windows não verificados.

## resumo para agentes

- comandos novos em `chrome_command_ids.h`: `IDC_AERO_COMMAND_BAR` (34076, Ctrl+T) e `IDC_AERO_NEW_WINDOW_OR_NOTE` (34077, Ctrl+N); ambos trocados só em `accelerator_table.cc`, os menus mantêm `IDC_NEW_TAB` e `IDC_NEW_WINDOW`. A execução fica em `BrowserCommandController`; Ctrl+N está em `IsReservedCommandOrKey`.
- Ctrl+Tab reaproveita `IDC_CYCLE_TO_NEXT_TAB`/`IDC_CYCLE_TO_PREV_TAB` e chama `aerographene::ShowOrAdvanceTabSwitcher`; com 1 aba segue o caminho original.
- ao mudar um atalho: criar comando próprio no lugar do original só na tabela de aceleradores, conservar o comando original no menu, e documentar aqui e na página da função.
- ordem em `patches/series`: `commandbar-f3` → `notes-f2b` → `tab-switcher` → `notes-ctrl-n` (os dois últimos no fim da série).
- não testado no navegador.
