# terminal

página interna `aerographene://terminal` (por baixo, `chrome://terminal`): um quadro com janelas de terminal arrastáveis, cada uma com um shell local real. Plano completo e regras de segurança em [`docs/PLANO-V0.3.md`](../PLANO-V0.3.md), seção C.

## estado atual (v0.3, em desenvolvimento)

ligado no código, mas ainda não aberto no navegador: cada janela do quadro tem um xterm.js conectado a um shell real, num workspace com pan e zoom.

validado até aqui (Chromium 154, Cezanne, overlay): os patches aplicam sem fuzz, os objetos compilam e os testes passam: 9 da sessão pty (incl. processo em primeiro plano), 9 do host e 3 do comando `-t` (eco pelo shell e código de saída, resize, limite de 16 sessões por aba e 64 no processo, destruir o host mata o shell, colar 1 MiB num programa que não lê não trava, saída pausa sem ack). Não testado: a página no navegador (xterm sob a CSP real, vim, htop, Ctrl+C) e o teste negativo de acesso por página web ou extensão.

- feito (C1, `patches/aerographene/terminal-webui.patch`): quadro com grade de fundo e botão `+ terminal`; cada janela se arrasta pelo cabeçalho, redimensiona pelo canto, ganha foco ao clicar e fecha no `×`. O título da aba segue `t: N terminals`. Nenhum processo é criado.
- feito (C2, `patches/aerographene/terminal-pty.patch`): sessão de pseudo-terminal no processo do browser, com testes unitários.
- feito (C3, `patches/aerographene/terminal-xterm.patch` e `terminal-bridge.patch`): xterm.js 6.0.0 vendorizado (MIT) em cada janela, ligado ao shell; título da janela pelo OSC 0/2; recarregar ou fechar a página mata os shells.
- feito (correções do review de segurança de 13/10/2026): escrita no pty nunca bloqueia, controle de fluxo da saída e limite global de sessões (ver abaixo).
- feito (C4, `patches/aerographene/terminal-c4.patch`): pan e zoom do workspace, layout persistido, título da aba `t: workspace N` e entrada `-t` na command bar (seção abaixo). Overlay do Cezanne: `aero_ui_tests` 47/47; `builtin_provider.cc` e `terminal_handler.cc` passam `-fsyntax-only` com os flags da `out/Default`.
- feito (C5, `patches/aerographene/terminal-c5.patch`): só perfil normal (nem anônimo, nem convidado, nem perfil de sistema), checagem de frame/origem num helper testado, e links OSC 8 abrindo só http(s) numa aba nova sem `opener` (seção "revisão de segurança C5"). Overlay do Cezanne: `aero_ui_tests` 49/49.
- falta: review opus e teste negativo no navegador (página web e extensão de teste), a página aberta no navegador (pan/zoom, restauração, tooltip, `-t` na omnibox) e a migração para Mojo (hoje usa mensagens WebUI).

## workspace, título e `-t` (C4)

- título da aba: sempre `t: workspace N` (ex.: `t: workspace 1`), nunca o processo. Decisão do dono em 13/10/2026; substitui o `t: <processo>` e o `t: N terminals` do plano. N vem de `?w=N` na URL (1 a 99, padrão 1).
- o processo em primeiro plano (`tcgetpgrp` no mestre + `/proc/<pgid>/comm`, só ASCII imprimível, até 15 caracteres) aparece apenas no tooltip do cabeçalho da janela, consultado ao passar o mouse (mensagem `foreground(cb, id)`). O título da janela continua vindo do OSC 0/2.
- pan: arrastar o fundo (botão esquerdo ou do meio) ou rolar a roda sobre o fundo. Zoom: Ctrl+roda no ponto do cursor ou botões `−`/`+`/`1:1`, de 25% a 200%. A grade acompanha. Janelas ficam em unidades do mundo, sem limite do quadro; arrastar e redimensionar dividem o delta pelo zoom. Limitação conhecida: com zoom diferente de 100% a seleção com mouse no xterm.js pode ficar deslocada (ele não conhece a transformação).
- layout: posições e tamanhos das janelas e a vista (pan/zoom) são salvos por workspace no `localStorage` da origem `chrome://terminal` (chave `aero-terminal-layout-N`), 300 ms depois da última mudança. Desvio do plano, que previa pref do perfil: evita mexer em `browser_prefs` do upstream. Ao ler, tudo é validado e limitado (máx. 16 janelas, faixas de coordenadas, JSON inválido ignorado). Os shells não sobrevivem: janelas restauradas abrem shells novos.
- command bar: `-t` ou `-t N` (N de 1 a 99, depois de espaço; `-t2`, `-t 0` e `-t 1 2` não valem) vira a sugestão padrão `t: workspace N` que abre `chrome://terminal/?w=N`. Implementado em `BuiltinProvider::Start` (o texto é classificado como QUERY, por isso o provedor ignorava) com o parser puro `aero_terminal_command` em `components/omnibox/browser`.

## como funciona

- custo zero no startup: só a configuração da página é registrada; nada nasce até uma aba abrir `aerographene://terminal`.
- só em perfil normal: desabilitada em janelas anônimas, no perfil convidado e no perfil de sistema (seletor de perfis).
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

## revisão de segurança C5

revisão dos patches `terminal-*` contra os itens 1 a 8 do plano (13/10/2026):

- 1: o handler só nasce no controlador de `chrome://terminal`; cada mensagem exige frame principal, origem exatamente `chrome://terminal` e perfil normal (`aerographene::IsTerminalFrame` e `TerminalAllowedForContext`, alvo `aero_terminal:access`). `aerographene://terminal`, `chrome-untrusted://terminal`, outros hosts e origens opacas são recusados (testado).
- 2: sem rede nem script inline. Corrigido: o padrão do xterm.js para links OSC 8 abria uma janela `about:blank` (que herda a origem `chrome://terminal`) e depois trocava o endereço; agora só `http:`/`https:`, com confirmação, numa aba nova com `noopener,noreferrer`. Segue o desvio `style-src 'unsafe-inline'`.
- 3: corrigido: antes só `IsOffTheRecord` era recusado, o que deixava passar o perfil de sistema e o perfil original do convidado; agora vale só `BrowserProfileType::kRegular` (testado para os seis tipos). A linha de comando continua sem abrir `chrome://` (`startup/url_util.cc` não é tocado por nenhum patch); sites continuam sem navegar a `chrome://` (regra do upstream).
- 4: `override-chrome-protocol` (Helium) e `branding-scheme` não afrouxam extensões: `aerographene` não é esquema válido para extensões (`URLPattern::IsValidSchemeForExtensions`), então `PermissionsData::IsRestrictedUrl` já recusa content scripts e `chrome.debugger` nele; a checagem de `chrome://` fica intacta; `ExtensionTabUtil::IsKillURL` só ficou mais restritivo. O navegador reescreve `aerographene://` para `chrome://` antes de navegar, e o terminal só aceita a origem `chrome://terminal`.
- 5 e 7: sem mudança (open sem comando nem cwd; `O_CLOEXEC` e só o escravo no filho).
- 6: limites presentes; `ReportBadMessage` não existe para `WebUIMessageHandler`, então mensagem inválida continua só descartada (desvio registrado).
- 8: pendente: review opus e teste no navegador com página web (`window.open`, link, `iframe`, `location`) e extensão de teste.

## limite que não depende do terminal

abrir o navegador com `--remote-debugging-port` (ou `--remote-debugging-pipe`) dá a qualquer programa local que fale CDP controle total do navegador, inclusive desta página: isso equivale a execução de código como o usuário, com ou sem terminal. O mesmo vale para `--extensions-on-chrome-urls`. Não use essas opções num perfil do dia a dia.

## arquivos

- `chrome/browser/ui/webui/aero_terminal/aero_terminal_ui.{h,cc}`: configuração e controlador.
- `chrome/browser/resources/aero_terminal/terminal.{html,css,js}`: quadro.
- `chrome/browser/ui/webui/aero_terminal/terminal_session.{h,cc}` e `terminal_session_unittest.cc`: pty e testes.
- `chrome/browser/ui/webui/aero_terminal/terminal_host.{h,cc}` e `terminal_host_unittest.cc`: sessões de uma aba numa sequência de I/O, e testes.
- `chrome/browser/ui/webui/aero_terminal/terminal_handler.{h,cc}`: mensagens da página.
- `components/omnibox/browser/aero_terminal_command.{h,cc}` e `_unittest.cc`: parser do `-t`.
- `chrome/browser/resources/aero_terminal/xterm.{mjs,css}` e `XTERM_LICENSE`: xterm.js vendorizado.

## resumo para agentes

- `chrome://terminal` = `AeroTerminalUI` + `TerminalHandler` (WebUIMessageHandler: `open(cb, cols, rows)`, `write(id, text)`, `resize`, `close`, `ack(id, bytes)`; eventos `output(id, base64)`, `exit(id, code)` e `writeDropped(id)` por `cr.webUIListenerCallback`) + `TerminalHost` (alvo `aero_terminal:host`, `base::SequenceBound` numa sequência MayBlock/WithBaseSyncPrimitives/BLOCK_SHUTDOWN, `FileDescriptorWatcher`). Recursos `IDR_AERO_TERMINAL_XTERM_{JS,CSS}`. Sem Mojo (desvio no plano), `AeroTerminalUIConfig` em `chrome_web_ui_configs.cc` sob `BUILDFLAG(IS_LINUX)`; `IDR_AERO_TERMINAL_{HTML,CSS,JS}`; off-the-record desabilitado.
- `aerographene::TerminalSession` (`Start/WriteSome/Resize/Terminate`, `master_fd()` O_NONBLOCK); `WriteSome` devolve quantos bytes o pty aceitou, nunca bloqueia. `TerminalHost`: fila de entrada por sessão (`kMaxPendingInput` 1 MiB, `Write` devolve false e o handler emite `writeDropped(id)`), drenada por `WatchWritable`; créditos de saída (`kMaxUnackedOutput` 256 KiB, mensagem `ack(id, bytes)` com bytes ≤ 16 KiB); `kMaxSessionsGlobal` 64 (contador atômico no processo). Alvo `aero_terminal:session`, testes `aero_terminal:unit_tests` ligados a `chrome/test:unit_tests`.
- `--remote-debugging-port`/CDP e `--extensions-on-chrome-urls` equivalem a execução de código (documentado acima, item 4 do plano).
- C5 (`terminal-c5.patch`): alvo `aero_terminal:access` (`TerminalAllowedForContext` = só `profile_metrics::BrowserProfileType::kRegular`, usado no `IsWebUIEnabled` e em cada mensagem; `IsTerminalFrame` = frame principal + origem `chrome://terminal`), testes `TerminalAccessTest.*`; `LINK_HANDLER` no `terminal.js` para OSC 8. Itens 3/4 revisados (ver seção). Falta do item 8: review opus e teste negativo no navegador; sem `ReportBadMessage` (mensagens WebUI só descartam).
- C4 (`terminal-c4.patch`, depois de `terminal-bridge`): título da aba fixo `t: workspace N` (N = `?w=N`, 1..99); processo em primeiro plano só no tooltip (`TerminalSession::ForegroundProcessName`, `TerminalHost::Foreground`, mensagem `foreground(cb, id)` -> string); pan/zoom por transform em `#world`; layout em `localStorage` `aero-terminal-layout-N` (validado, máx. 16 janelas); `-t`/`-t N` em `BuiltinProvider::Start` via `aerographene::ParseTerminalCommand`/`TerminalCommandUrl` (nota: a omnibox trata "-t" como QUERY). Teste de JS só com DOM falso (fora do repo); `aero_ui_tests` do overlay inclui os testes do parser por fonte temporária.
- validação: ver `docs/PLANO-V0.3.md`, seção C (status). Não testado no navegador.
