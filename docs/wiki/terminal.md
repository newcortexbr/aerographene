# terminal

página interna `aerographene://terminal` (por baixo, `chrome://terminal`): um quadro com janelas de terminal arrastáveis, cada uma com um shell local real. Plano completo e regras de segurança em [`docs/PLANO-V0.3.md`](../PLANO-V0.3.md), seção C.

## estado atual (v0.3, em desenvolvimento)

ainda não é usável: as janelas do quadro são de mentira e o shell real existe só no código do browser, sem ligação com a página.

validado até aqui: os patches aplicam sem fuzz e os objetos compilam (Chromium 154, Cezanne); os testes unitários compilam, mas ainda não foram executados.

- feito (C1, `patches/aerographene/terminal-webui.patch`): quadro com grade de fundo e botão `+ terminal`; cada janela se arrasta pelo cabeçalho, redimensiona pelo canto, ganha foco ao clicar e fecha no `×`. O título da aba segue `t: N terminals`. Nenhum processo é criado.
- feito (C2, `patches/aerographene/terminal-pty.patch`): sessão de pseudo-terminal no processo do browser, com testes unitários. Ainda não exposta à página.
- falta: Mojo com binder restrito à página, xterm.js nas janelas, título por OSC, persistência do layout, limites e review de segurança dedicado (C3–C5).

## como funciona

- custo zero no startup: só a configuração da página é registrada; nada nasce até uma aba abrir `aerographene://terminal`.
- desabilitada em janelas anônimas e no perfil convidado.
- sem rede: CSP estrita (`default-src 'none'`, `connect-src 'none'`, sem script inline, Trusted Types).
- só Linux.

## a sessão pty (C2)

- abre o pty com `posix_openpt` (`O_CLOEXEC`), entrega só o lado escravo ao filho como stdin/stdout/stderr; nenhum outro descritor do navegador vaza.
- o filho vira líder de sessão e de grupo (`setsid` + `TIOCSCTTY`) e roda com ambiente limpo: `TERM=xterm-256color`, `COLORTERM`, `HOME`, `SHELL`, `PATH`, `USER`, `LOGNAME`, `LANG`, `LC_ALL`.
- o programa é sempre escolhido pelo navegador (shell do usuário por padrão), nunca pela página; diretório inicial = `HOME`.
- tamanho validado entre 1 e 1000 colunas/linhas.
- fechar manda `SIGHUP` ao grupo inteiro, espera até 1 s, depois `SIGKILL` no grupo e colhe o processo: nada fica órfão nem zumbi.

## arquivos

- `chrome/browser/ui/webui/aero_terminal/aero_terminal_ui.{h,cc}`: configuração e controlador.
- `chrome/browser/resources/aero_terminal/terminal.{html,css,js}`: quadro.
- `chrome/browser/ui/webui/aero_terminal/terminal_session.{h,cc}` e `terminal_session_unittest.cc`: pty e testes.

## resumo para agentes

- `chrome://terminal` = `AeroTerminalUI` (WebUIController puro, sem Mojo), `AeroTerminalUIConfig` em `chrome_web_ui_configs.cc` sob `BUILDFLAG(IS_LINUX)`; `IDR_AERO_TERMINAL_{HTML,CSS,JS}`; off-the-record desabilitado.
- `aerographene::TerminalSession` (`Start/Write/Resize/Terminate`, `master_fd()`), métodos bloqueantes; leitura do mestre fica para o host da C3 (`FileDescriptorWatcher`). Alvo `aero_terminal:session`, testes `aero_terminal:unit_tests` ligados a `chrome/test:unit_tests`.
- antes de expor por Mojo, cumprir a seção "segurança do terminal" do plano (binder só para `TerminalUI`, checar frame principal e origem, limites, `ReportBadMessage`, review opus).
- validação: ver `docs/PLANO-V0.3.md`, seção C (status). Não testado no navegador.
