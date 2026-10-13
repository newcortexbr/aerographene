# terminal

página interna `aerographene://terminal` (por baixo, `chrome://terminal`): um quadro com janelas de terminal arrastáveis, cada uma com um shell local real. Plano completo e regras de segurança em [`docs/PLANO-V0.3.md`](../PLANO-V0.3.md), seção C.

## estado atual (v0.3, em desenvolvimento)

ligado no código, mas ainda não aberto no navegador: cada janela do quadro tem um xterm.js conectado a um shell real.

validado até aqui (Chromium 154, Cezanne, overlay): os patches aplicam sem fuzz, os objetos compilam e os testes passam: 8 da sessão pty e 8 do host (eco pelo shell e código de saída, resize, limite de 16 sessões por aba e 64 no processo, destruir o host mata o shell, colar 1 MiB num programa que não lê não trava, saída pausa sem ack). Não testado: a página no navegador (xterm sob a CSP real, vim, htop, Ctrl+C) e o teste negativo de acesso por página web ou extensão.

- feito (C1, `patches/aerographene/terminal-webui.patch`): quadro com grade de fundo e botão `+ terminal`; cada janela se arrasta pelo cabeçalho, redimensiona pelo canto, ganha foco ao clicar e fecha no `×`. O título da aba segue `t: N terminals`. Nenhum processo é criado.
- feito (C2, `patches/aerographene/terminal-pty.patch`): sessão de pseudo-terminal no processo do browser, com testes unitários.
- feito (C3, `patches/aerographene/terminal-xterm.patch` e `terminal-bridge.patch`): xterm.js 6.0.0 vendorizado (MIT) em cada janela, ligado ao shell; título da janela pelo OSC 0/2; recarregar ou fechar a página mata os shells.
- feito (correções do review de segurança de 13/10/2026): escrita no pty nunca bloqueia, controle de fluxo da saída e limite global de sessões (ver abaixo).
- falta: título da aba `t: <processo>`, persistência do layout, novo review e teste negativo (C4–C5), e a migração para Mojo (hoje usa mensagens WebUI).

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

## segurança da ligação (C3)

- só a página `chrome://terminal` fala com o shell: o handler é adicionado apenas pelo controlador dela, e cada mensagem confere que veio do frame principal com origem `chrome://terminal`.
- a página não escolhe programa, argumentos nem pasta: `open` recebe só colunas e linhas; o navegador abre o shell do usuário em `HOME`.
- limites: 16 terminais por aba e 64 no navegador inteiro, 64 KiB por mensagem de escrita, tamanho entre 1 e 1000; mensagem malformada é descartada.
- escrita sem travar: o pty é não bloqueante. O que o programa ainda não leu espera numa fila por terminal (até 1 MiB), esvaziada quando o pty aceita mais. Se a fila encher (ex.: colar muito texto em algo que não lê a entrada), o excesso é descartado e a janela mostra `[entrada descartada: o programa não está lendo]`. Antes, colar mais de ~22 KiB num programa parado travava todos os terminais da aba e o fechamento do navegador.
- saída com controle de fluxo: depois de 256 KiB entregues sem confirmação, o navegador para de ler aquele terminal; a página confirma (`ack`) cada bloco quando o xterm.js termina de processá-lo, e a leitura volta. Um `yes` não enche mais a memória da aba.
- a política de conteúdo continua sem rede e sem script inline; só os estilos inline foram liberados nesta página porque o xterm.js cria elementos `<style>`.
- a saída vai para a página em base64, porque bytes do terminal nem sempre são UTF-8.

## limite que não depende do terminal

abrir o navegador com `--remote-debugging-port` (ou `--remote-debugging-pipe`) dá a qualquer programa local que fale CDP controle total do navegador, inclusive desta página: isso equivale a execução de código como o usuário, com ou sem terminal. O mesmo vale para `--extensions-on-chrome-urls`. Não use essas opções num perfil do dia a dia.

## arquivos

- `chrome/browser/ui/webui/aero_terminal/aero_terminal_ui.{h,cc}`: configuração e controlador.
- `chrome/browser/resources/aero_terminal/terminal.{html,css,js}`: quadro.
- `chrome/browser/ui/webui/aero_terminal/terminal_session.{h,cc}` e `terminal_session_unittest.cc`: pty e testes.
- `chrome/browser/ui/webui/aero_terminal/terminal_host.{h,cc}` e `terminal_host_unittest.cc`: sessões de uma aba numa sequência de I/O, e testes.
- `chrome/browser/ui/webui/aero_terminal/terminal_handler.{h,cc}`: mensagens da página.
- `chrome/browser/resources/aero_terminal/xterm.{mjs,css}` e `XTERM_LICENSE`: xterm.js vendorizado.

## resumo para agentes

- `chrome://terminal` = `AeroTerminalUI` + `TerminalHandler` (WebUIMessageHandler: `open(cb, cols, rows)`, `write(id, text)`, `resize`, `close`, `ack(id, bytes)`; eventos `output(id, base64)`, `exit(id, code)` e `writeDropped(id)` por `cr.webUIListenerCallback`) + `TerminalHost` (alvo `aero_terminal:host`, `base::SequenceBound` numa sequência MayBlock/WithBaseSyncPrimitives/BLOCK_SHUTDOWN, `FileDescriptorWatcher`). Recursos `IDR_AERO_TERMINAL_XTERM_{JS,CSS}`. Sem Mojo (desvio no plano), `AeroTerminalUIConfig` em `chrome_web_ui_configs.cc` sob `BUILDFLAG(IS_LINUX)`; `IDR_AERO_TERMINAL_{HTML,CSS,JS}`; off-the-record desabilitado.
- `aerographene::TerminalSession` (`Start/WriteSome/Resize/Terminate`, `master_fd()` O_NONBLOCK); `WriteSome` devolve quantos bytes o pty aceitou, nunca bloqueia. `TerminalHost`: fila de entrada por sessão (`kMaxPendingInput` 1 MiB, `Write` devolve false e o handler emite `writeDropped(id)`), drenada por `WatchWritable`; créditos de saída (`kMaxUnackedOutput` 256 KiB, mensagem `ack(id, bytes)` com bytes ≤ 16 KiB); `kMaxSessionsGlobal` 64 (contador atômico no processo). Alvo `aero_terminal:session`, testes `aero_terminal:unit_tests` ligados a `chrome/test:unit_tests`.
- `--remote-debugging-port`/CDP e `--extensions-on-chrome-urls` equivalem a execução de código (documentado acima, item 4 do plano).
- da seção "segurança do terminal" do plano faltam: revisar `override-chrome-protocol`/branding-scheme (itens 3/4), review opus e teste negativo (item 8); sem `ReportBadMessage` (mensagens WebUI só descartam).
- validação: ver `docs/PLANO-V0.3.md`, seção C (status). Não testado no navegador.
