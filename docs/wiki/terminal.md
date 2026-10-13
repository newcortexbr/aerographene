# terminal

página interna `aerographene://terminal` (por baixo, `chrome://terminal`): um quadro com janelas de terminal arrastáveis, cada uma com um shell local real. Plano completo e regras de segurança em [`docs/PLANO-V0.3.md`](../PLANO-V0.3.md), seção C.

## estado atual (v0.3, em desenvolvimento)

ligado no código, mas ainda não aberto no navegador: cada janela do quadro tem um xterm.js conectado a um shell real.

validado até aqui (Chromium 154, Cezanne, overlay): os patches aplicam sem fuzz, os objetos compilam e os testes passam: 7 da sessão pty e 4 do host (eco pelo shell e código de saída, resize, limite de 16 sessões, destruir o host mata o shell). Não testado: a página no navegador (xterm sob a CSP real, vim, htop, Ctrl+C) e o teste negativo de acesso por página web ou extensão.

- feito (C1, `patches/aerographene/terminal-webui.patch`): quadro com grade de fundo e botão `+ terminal`; cada janela se arrasta pelo cabeçalho, redimensiona pelo canto, ganha foco ao clicar e fecha no `×`. O título da aba segue `t: N terminals`. Nenhum processo é criado.
- feito (C2, `patches/aerographene/terminal-pty.patch`): sessão de pseudo-terminal no processo do browser, com testes unitários.
- feito (C3, `patches/aerographene/terminal-xterm.patch` e `terminal-bridge.patch`): xterm.js 6.0.0 vendorizado (MIT) em cada janela, ligado ao shell; título da janela pelo OSC 0/2; recarregar ou fechar a página mata os shells.
- falta: título da aba `t: <processo>`, persistência do layout, backpressure da saída, review de segurança dedicado e teste negativo (C4–C5), e a migração para Mojo (hoje usa mensagens WebUI).

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
- limites: 16 terminais por aba, 64 KiB por escrita, tamanho entre 1 e 1000; mensagem malformada é descartada.
- a política de conteúdo continua sem rede e sem script inline; só os estilos inline foram liberados nesta página porque o xterm.js cria elementos `<style>`.
- a saída vai para a página em base64, porque bytes do terminal nem sempre são UTF-8.

## arquivos

- `chrome/browser/ui/webui/aero_terminal/aero_terminal_ui.{h,cc}`: configuração e controlador.
- `chrome/browser/resources/aero_terminal/terminal.{html,css,js}`: quadro.
- `chrome/browser/ui/webui/aero_terminal/terminal_session.{h,cc}` e `terminal_session_unittest.cc`: pty e testes.
- `chrome/browser/ui/webui/aero_terminal/terminal_host.{h,cc}` e `terminal_host_unittest.cc`: sessões de uma aba numa sequência de I/O, e testes.
- `chrome/browser/ui/webui/aero_terminal/terminal_handler.{h,cc}`: mensagens da página.
- `chrome/browser/resources/aero_terminal/xterm.{mjs,css}` e `XTERM_LICENSE`: xterm.js vendorizado.

## resumo para agentes

- `chrome://terminal` = `AeroTerminalUI` + `TerminalHandler` (WebUIMessageHandler: `open(cb, cols, rows)`, `write(id, text)`, `resize`, `close`; eventos `output(id, base64)` e `exit(id, code)` por `cr.webUIListenerCallback`) + `TerminalHost` (alvo `aero_terminal:host`, `base::SequenceBound` numa sequência MayBlock/WithBaseSyncPrimitives/BLOCK_SHUTDOWN, `FileDescriptorWatcher`). Recursos `IDR_AERO_TERMINAL_XTERM_{JS,CSS}`. Sem Mojo (desvio no plano), `AeroTerminalUIConfig` em `chrome_web_ui_configs.cc` sob `BUILDFLAG(IS_LINUX)`; `IDR_AERO_TERMINAL_{HTML,CSS,JS}`; off-the-record desabilitado.
- `aerographene::TerminalSession` (`Start/Write/Resize/Terminate`, `master_fd()`), métodos bloqueantes; leitura do mestre feita pelo `TerminalHost`. Alvo `aero_terminal:session`, testes `aero_terminal:unit_tests` ligados a `chrome/test:unit_tests`.
- da seção "segurança do terminal" do plano faltam: revisar `override-chrome-protocol`/branding-scheme (itens 3/4), review opus e teste negativo (item 8); sem `ReportBadMessage` (mensagens WebUI só descartam).
- validação: ver `docs/PLANO-V0.3.md`, seção C (status). Não testado no navegador.
