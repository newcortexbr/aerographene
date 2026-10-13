# plano da v0.3

Status: proposto em 13/10/2026; B e C em andamento na branch `v0.3-ui` (ver status nas seções). Escopo decidido pelo dono em 13/10/2026: A (build avx1), B (notas), C (terminal), D (Windows 10 e 11 por cross-compile), E (pacotes nativos). Google Sync (ADR 0006) fica fora da v0.3.

Status em 13/10/2026, manhã (branch `v0.3`, HEAD `95eafb8`): `v0.3-ui` mergeada na `v0.3` (sem merge na `main`). Build avx2 38392093934 verde; smoke 38399339291 verde; build avx1 38399420162 verde (agora com notas e terminal). Releases para o draft `v0.3.0`: avx2 38402316949 e avx1 38402602679, ambos success; o draft segue não publicado. Smoke CDP headless (contêiner `aerographene-builder:v2`, launcher `aerographene`): `chrome://notes` mostra "Pick a vault folder to start." e o botão "Choose folder"; `chrome://terminal` abre o shell; num contexto anônimo real (`Target.createBrowserContext`) as duas páginas recusam com `ERR_INVALID_URL`. Continua não testado à mão; falta smoke dedicado e verificação de ISA do avx1.

Fontes: `docs/SCOPE.md`, `CONTEXT.md`, ADRs 0004/0008/0009, `docs/BUILD.md`, `build/`, `.github/workflows/{build,release}.yml`, `patches/series`, `theming/1/DECISIONS.md` e mockups C-r02/D-r02/G-r01, nota do vault `agents/projetos/navegador-fork-contexto-e-decisoes`. APIs do upstream conferidas por leitura (ssh, só leitura) na árvore do Chromium 154 do Cezanne (`~/aerographene-build/portablelinux/build/src`); caminhos citados abaixo como `src/...`.

## regras que valem para todos os itens

- branch `v0.3` a partir da `main`; um item por fatia; pré-checagem estática da série antes de qualquer envio ao runner (AGENTS.md).
- validação de compilação: primeiro objeto/alvo afetado (overlay docker somente leitura, `ninja -C out/Default obj/<caminho>.o`); build completa só para fechar o pacote.
- runner único `[self-hosted, linux, intense]`, grupo de concurrency `build`: uma build por vez.
- desempenho: nada piora mais de 2% contra o Helium. B e C têm custo zero quando não usados: nenhum processo, thread, watcher ou recurso carregado no startup; tudo nasce ao abrir a aba.
- cada função nova ganha página em `docs/wiki/` e linha no README (abaixo da linha humana).

## fatos do upstream conferidos (Chromium 154, árvore do Cezanne)

- painel lateral: ids em `src/chrome/browser/ui/side_panel/side_panel_entry_id.h` (macro `V(k..., action, "Nome")`); há escopo por aba (`side_panel_entry_scope.h`, `side_panel_entry_key.h`, entrada de teste `kTestTabScopedEntry`); a hospedagem WebUI fica em `src/chrome/browser/ui/views/side_panel/side_panel_web_ui_view.{h,cc}`. O Helium já mexe aqui (`helium/ui/side-panel.patch`).
- WebUI: `content::WebUIConfig`/`DefaultWebUIConfig` (`src/content/public/browser/webui_config.h`), `TopChromeWebUIConfig` (`src/chrome/browser/ui/webui/top_chrome/top_chrome_webui_config.h:25`); binders Mojo por controlador em `src/chrome/browser/chrome_browser_interface_binders_webui.cc` (`RegisterWebUIControllerInterfaceBinder<>`, linha 181) e partes desktop em `..._webui_parts_desktop.cc`. Esquema `chrome-untrusted` existe (`src/content/public/common/url_constants.h:24`).
- processo: `base::LaunchOptions` tem `fds_to_remap` (`src/base/process/launch.h:229`), `pre_exec_delegate` com `RunAsyncSafe()` (103–115, 354) e `new_process_group` (365). Observação de arquivos: `src/base/files/file_path_watcher.h`.
- pty no próprio Chromium, para copiar o padrão (não o código ChromeOS): `src/remoting/host/terminal_session_linux.cc` usa `posix_openpt(O_RDWR|O_NOCTTY|O_CLOEXEC)` (182), e no filho `setsid()` + `ioctl(STDIN_FILENO, TIOCSCTTY, 0)` (118–119), lançando com `base::LaunchProcess` (157). `src/chromeos/process_proxy/process_proxy.cc` (202, 262) é o equivalente ChromeOS. A API `terminalPrivate` (`src/chrome/browser/extensions/api/terminal/`) tem `assert(is_chromeos)`: não serve no Linux.
- bibliotecas JS: não há xterm.js, hterm, CodeMirror nem renderizador Markdown JS na árvore (`third_party/markdown` é Python de build). Há `lit` em `third_party/node/node_modules`. Precisaremos vendorizar (licenças compatíveis com GPL-3.0).
- Windows: `src/build/vs_toolchain.py` pede VS 2026 (18) + SDK `10.0.28000.0` (`SDK_VERSION`, linha 63; `TOOLCHAIN_HASH = '3bfcb536c8'`, linha 62; chave `GYP_MSVS_HASH_<hash>`, 541). `src/build/toolchain/win/` presente no tarball.
- disco do Cezanne agora: 218 GB, 118 GB livres; `out/Default` 16 GB.

## A. build avx1 (x86-64-v2 + AVX, ADR 0009)

Objetivo: segundo pacote `aerographene-vX.Y.Z-avx1-linux.tar.zst`, ao lado de `aerographene-vX.Y.Z-avx2-linux.tar.zst`.

Status em 13/10/2026, noite (branch `v0.3`, sem merge na `main`): B5 feita em `notes-b5.patch` (último da série). Watcher recursivo (`VaultWatcher` + `FilePathWatcher`) dono do handler, evento `vaultChanged` agrupado em 200 ms; a página refaz a árvore, recarrega nota limpa e manda nota alterada ao fluxo de conflito do B4. Busca por nome e conteúdo no navegador com limites (100 resultados, 20000 arquivos, 128 MiB, 16 níveis). Imagens da vault no preview (`![](x.png)`, `![[x.png|300]]`), lidas com o mesmo confinamento e entregues como `data:` (CSP `img-src 'self' data:`). Título da aba continua `o: <nome da vault>`. Validação no overlay `/tmp/aero-d3b` do Cezanne: patch aplica sobre a série de notas com `--fuzz=0`; `aero_ui_tests` com 9 `VaultSearchTest.*` e 4 `VaultWatcher*Test.*` novos (inotify real: criar fora, subpasta, ocultos ignorados, parar após `Reset`, raiz inexistente) passando; `notes_handler.o` e `aero_notes_ui.o` compilam; página: 66 verificações no Chrome headless com backend simulado (`tests/notes-editor/`), incluindo arquivo criado fora, nota limpa/alterada/apagada, rajada coalescida, busca e imagens. Não verificado: `chrome://notes` real (Trusted Types, CSP com `data:`, `FireWebUIListener` de fato chegando), inotify em vaults com milhares de pastas, Windows, desempenho da busca em vaults grandes, ID de recurso no grit completo. Achado no caminho: a listagem (B2) podia passar nome de arquivo não UTF-8 a `base::Value`; corrigido (nome ignorado).

Fatias:

1. A1 parametrizar `MARCH` e saída. `build/config.sh` aceita `MARCH` por env (padrão `x86-64-v3`); `build/inner.sh` usa `out/<alvo>` (`out/Default` para v3, `out/Avx1` para ivybridge) em vez de `out/Default` fixo (hoje em `inner.sh:348-392`) e o nome do pacote carrega `avx2`/`avx1`; `smoke.sh` recebe o caminho. ccache em diretório próprio por alvo. Aceite: `bash -n`, build v3 com ccache quente idêntica à anterior (mesmo hash de série, ~20 min, pacote com `-avx2-`).
2. A2 input `cpu` no `build.yml` (`avx2` padrão, `avx1` opcional; push em `main` continua só avx2) e nome do artifact por cpu. `release.yml` passa a aceitar dois `run_id` e renomear para `aerographene-vX.Y.Z-{avx2,avx1}-linux.tar.zst`. Aceite: `actionlint`/leitura, sem `pull_request` (ADR 0004).
3. A3 build avx1 completa no runner. Aceite: log do `gn gen` com `-march=ivybridge` depois de `-msse3` (`ninja -t commands`), rust com `-Ctarget-cpu=ivybridge`, pacote gerado, smoke no Cezanne. Resultado: build run 38353476105 (branch v0.3) concluída com success; release run 38379817425 (`tag=v0.3.0`, `cpu=avx1`) success; `v0.3.0` segue draft com `aerographene-v0.3.0-avx1-linux.{tar.zst,pkg.tar.zst,deb,rpm}` e `namcap-avx1.txt`. Smoke no Cezanne e verificação de ISA ainda pendentes.
4. A4 verificação de ISA: `objdump -d chrome | grep -cE 'vfmadd|andn|shlx|vpbroadcast.*ymm'` próximo de zero no código próprio (dispatch por CPU do Skia/V8 pode legitimamente conter AVX2 em caminhos protegidos; comparar com ungoogled). Aceite final: abre na Ivy Bridge (máquina do dono) e bench `--quick` lá contra Helium.

Custo: A3 é build fria (o `MARCH` entra no hash do ccache): ~8 h. Alternar v3/avx1 re-patcheia `BUILD.gn`; com `out` separado o v3 volta rápido. Disco: +16 GB `out/Avx1` + ~6 GB ccache, cabe.

## B. notas estilo Obsidian

Produto: uma única aba especial (`aerographene://notes`, título da aba `o: <nome da vault>` (decisão do dono em 13/10/2026; nunca o arquivo aberto), cor lilás, cristal outline, mockups C-r02a/b) com editor e visualizador da vault (pasta Markdown local escolhida pelo usuário) e uma segunda barra lateral só da vault, que não interfere na sidebar do navegador.

Arquitetura recomendada:

- WebUI confiável `chrome://notes` (Lit + TS no padrão de `chrome/browser/resources/`), controlador `NotesUI` com `DefaultWebUIConfig`. A segunda sidebar é um painel dentro da própria página (árvore de arquivos à esquerda, redimensionável), não um side panel nativo: zero mudança em Views, sem conflito com a sidebar vertical do Helium/aerographene nem com `helium/ui/side-panel.patch`. Alternativa (decisão em aberto 3): side panel com escopo de aba (`kTestTabScopedEntry` mostra que o escopo existe).
- Mojo `notes.mojom::PageHandler` no browser: `ListTree`, `Read(path)`, `Write(path, text, expected_mtime)`, `Create/Rename/Delete`, `Watch` (eventos por `FilePathWatcher` só enquanto a aba existe). Tudo em `base::ThreadPool` com `MayBlock`.
- confinamento: raiz da vault guardada em pref do perfil; todo caminho recebido é relativo, normalizado, sem `..`, e resolvido com `base::MakeAbsoluteFilePath`/realpath conferindo prefixo da raiz (symlink para fora = recusa). Só `.md` e anexos de imagem para leitura; escrita só `.md`. Escrita atômica (`base::ImportantFileWriter` ou temporário + rename), conflito por mtime.
- escolha da pasta: `ui::SelectFileDialog` (já usado pelo import de tema da v0.2).
- render: Markdown → HTML no renderer da WebUI com biblioteca vendorizada (markdown-it, MIT) e saída sanitizada sob Trusted Types (a WebUI já exige); `[[wikilinks]]`, embeds de imagem via URL `chrome://notes/file?path=` servida pelo `URLDataSource` com o mesmo confinamento. Sem HTML cru da nota, sem scripts, sem recursos remotos (CSP padrão da WebUI).
- editor v1: `textarea` com pré-visualização lado a lado (como C-r02); CodeMirror 6 (MIT) fica para depois se o dono quiser.
- uma aba só: abrir `chrome://notes` quando já existe uma na janela ativa a existente (`GetIndexOfExistingTabMatchingURL` em `chrome::Navigate`). Exceção do dono (13/10/2026): `o:` sozinho abre uma aba NOVA de notas (`?new=1`, não dobrada); `o: <termo>` reaproveita a aba existente.
- command bar: prefixo `o:` (substitui o `-o` do plano e do primeiro esboço da B6): `o: <termo>` abre as notas sem documento, com a árvore na lateral e a busca B5 pelo termo no centro (`?q=`); `o:` sozinho abre aba nova na raiz da vault.

Status em 13/10/2026 (branch `v0.3-ui`, sem merge): B1 feito sem a entrada `-o` na command bar nem ícone (`notes-webui.patch`); B2 só o backend (`notes-vault-reader.patch`: `ResolveInVault`/`ListVaultDir`/`ReadVaultNote` + `vault_reader_unittest.cc`), sem Mojo, sem seletor de pasta e sem árvore na página. Validação no overlay `/tmp/aero-st8` do Cezanne (árvore somente leitura com a série v0.3 já aplicada, patches com `--fuzz=0`): `aero_notes_ui.o`, `chrome_web_ui_configs.o`, `vault_reader.o` e `vault_reader_unittest.o` compilam; `gn check` OK em `aero_notes:*` e `chrome/test:unit_tests` (em `webui:configs` só um erro anterior, `autofill_ml_internals`); grit de `browser_resources` gerado. Não verificado: testes executados (o link exigiria 1001 passos com o CI reconstruindo o lower), link do `chrome`, página aberta no navegador, custo no startup medido.

Status em 13/10/2026, madrugada (branch `v0.3-ui`, sem merge): B2 ligada e B3 feita em `notes-render.patch` (`NotesHandler` com `getVault`/`pickVault`/`listDir`/`readNote`, pref `aerographene.notes.vault_path`, árvore lateral e visualização por `markdown.js` próprio, que só cria nós DOM). Desvios registrados: (1) mensagens WebUI (`chrome.send` + `WebUIMessageHandler`, o mesmo do import de tema da v0.2) em vez de Mojo, porque os bindings Mojo de WebUI do 154 saem em TS (`*.mojom-webui.ts`) e exigem o pipeline `build_webui`/`ts_library`; a fronteira é a mesma (só o renderer da WebUI tem os bindings). Migrar para Mojo fica em aberto. (2) markdown-it não vendorizado (exigiria `build/inner.sh`); renderizador mínimo próprio (subconjunto: títulos, parágrafos, listas, tarefas, citações, código, ênfase, links http(s)/mailto, `[[wikilinks]]`; imagens ainda não). Validado: os 7 testes `VaultReaderTest.*` passaram (executável mínimo `aero_ui_tests` no overlay, main próprio, só `base` + `gtest`); `notes_handler.o` e `aero_notes_ui.o` compilam com o grit regenerado; `gn check` OK em `aero_notes:aero_notes`; `markdown.js` passou 10 casos num DOM simulado em Node (`<script>`, `onerror=`, `javascript:` saem como texto). `browser_prefs.o` (pref nova) compila. Não verificado: página no navegador, seletor de pasta real, Trusted Types no DevTools.

Status em 13/10/2026, tarde (branch `v0.3`, sem merge na `main`): B4 feita em `notes-editor.patch` (logo após `notes-render` na série). Editor de coluna única com live preview (`editor.js`: linha ativa crua, demais por `markdown.js`), salvar atômico (temporário + fsync + rename) com conflito por mtime (µs; aviso com "salvar como cópia", "sobrescrever" ou "recarregar", sem perder o texto), criar/renomear (`RENAME_NOREPLACE`)/apagar `.md`, e abertura relativa à raiz com `openat(O_NOFOLLOW)` por componente (`OpenVaultFileNoFollow`, fecha o TOCTOU da B2). Windows: escrita responde `unsupported`. Validação no overlay `/tmp/aero-d3b` do Cezanne (`aerographene-builder:v2`, `--init`): patch aplica com `--fuzz=0`; `aero_ui_tests` 55/55 (42 anteriores + 13 novos de vault); `vault_reader.o`, `vault_reader_unittest.o` e `notes_handler.o` compilam (o último com `-I` dos headers gerados do `out/Default`, só leitura); `aero_notes_ui.o` compila com `-DIDR_AERO_NOTES_EDITOR_JS` porque o grit do CI ainda não tem o ID novo; a página roda 31 verificações num Chrome headless do pacote com backend simulado (`tests/notes-editor/`). Decisão do dono, mesma data: o título da aba é sempre `o: <nome da vault>`. Não verificado: handler real aberto como `chrome://notes` (Trusted Types, CSP), seletor de pasta real, Windows, desempenho, notas muito grandes (refaz o bloco afetado inteiro), gerar o ID no grit completo.

Fatias:

1. B1 esqueleto: WebUI vazia `chrome://notes` registrada, `.grd`, ícone, entrada na command bar (`o:`, ver B6). Aceite: compila (alvo `chrome/browser/ui:ui` objeto + recursos), página abre, nada carregado no startup (sem registro além do config).
2. B2 Mojo de leitura: escolher vault, `ListTree`, `Read`; árvore lateral e visualização crua. Aceite: testes unitários do confinamento (`..`, absoluto, symlink para fora, nome com NUL) em `notes_handler_unittest.cc`; leitura de uma vault de exemplo.
3. B3 render Markdown + sanitização + wikilinks e imagens. Aceite: nota com `<script>`, `onerror=`, `javascript:` não executa nada (teste manual + DevTools sem erro de Trusted Types).
4. B4 escrita: editor, salvar, criar/renomear/apagar, conflito por mtime. Aceite: edição externa durante edição gera aviso, sem perda.
5. B5 watcher e busca simples por nome/conteúdo (no browser, limitada). Aceite: arquivo criado fora aparece; watcher some ao fechar a aba.
6. B6 aba única, título `o: <nome da vault>`, cor/ícone do tema, página wiki. Aceite: smoke com perfil novo; bench `--quick` sem a aba aberta dentro de 2% do Helium.

Status em 13/10/2026, tarde (branch `v0.3`, sem merge na `main`): B6 feita em `notes-b6.patch` (último da série). Command bar `o:`/`o: <termo>` (parser `aero_notes_command`, `BuiltinProvider::Start` depois do `-t`), `?q=` lido pela página (centro mostra os resultados da busca, lateral mantém a árvore, nenhum documento aberto), aba única por janela em `chrome::Navigate` com a exceção `?new=1` (`o:` sozinho abre aba nova, pedido do dono). Título da aba continua `o: <nome da vault>`. Validação no overlay `/tmp/aero-d3b` do Cezanne: patch aplica com `--fuzz=0` sobre o estado da série; `aero_ui_tests` 71/71 (3 `AeroNotesCommandTest.*` novos); `builtin_provider.cc` e `browser_navigator.cc` passam `-fsyntax-only` com os flags da `out/Default` (com os arquivos do terminal-c4 copiados no overlay); página no Chrome headless com backend simulado, incluindo `?q=` (`tests/notes-editor/`, 0 falhas). Não verificado: o fluxo no navegador real (foco da aba existente, navegação com `?q=` numa aba já aberta, `beforeunload` com nota suja), o Enter da omnibox abre na aba atual (não força aba extra para `o:` sozinho), cor/ícone da aba, smoke com perfil novo e o bench `--quick` da fatia.

Patches esperados: `aerographene/notes-webui.patch` (controlador, config, mojom, handler, `BUILD.gn`, grd), `aerographene/notes-resources.patch` (TS/Lit/CSS), `aerographene/notes-tab.patch` (aba única, rótulo, command bar). Vendor markdown-it baixado com sha256 fixado no `inner.sh`, como o uBlock, ou incluído no patch (decisão em aberto 4).

## C. terminal em quadro

Produto: aba `aerographene://terminal`, um quadro (canvas) com janelas virtuais de terminal arrastáveis, redimensionáveis, fecháveis, com pty real local (mockups D-r02a/b e G-r01; título da aba `t: <título do processo>` ou `t: N terminals`, azul, âmbar só para espera).

Arquitetura recomendada:

- WebUI confiável `chrome://terminal`; quadro em HTML/CSS (transform para pan/zoom, janelas posicionadas absolutas), cada janela com xterm.js vendorizado (MIT) renderizando em DOM/canvas.
- browser: `TerminalHost` por aba (não `KeyedService` global) dono das sessões; cada sessão: `posix_openpt` + `grantpt`/`unlockpt`/`ptsname_r`, filho por `base::LaunchProcess` com `fds_to_remap` (escravo em 0/1/2), `pre_exec_delegate` fazendo `setsid()` + `TIOCSCTTY` (padrão de `remoting/host/terminal_session_linux.cc:118-182`), `new_process_group`, env limpo (`TERM=xterm-256color`, `HOME`, `SHELL`, `LANG`, `PATH`), shell de `getpwuid`/`$SHELL`. Leitura do mestre com `base::FileDescriptorWatcher` numa sequência `MayBlock`; escrita e `TIOCSWINSZ` para resize. Fechar janela = `SIGHUP` ao grupo, depois `SIGKILL` com timeout; fechar a aba ou o perfil mata todas as sessões.
- fora do sandbox do renderer: o pty vive no processo do browser (como o ProcessProxy do ChromeOS), e o renderer só troca bytes por Mojo.
- Mojo `terminal.mojom`: `PageHandler.Open(cols, rows) => (session_id)`, `Write(id, bytes)`, `Resize(id, cols, rows)`, `Close(id)`; `Page.OnOutput(id, bytes)`, `OnExit(id, code)`, `OnTitle(id, title)`. Saída em lotes (ex.: 16 KiB ou 8 ms) para não inundar o IPC.
- layout do quadro (posições e tamanhos das janelas) salvo em pref do perfil; sessões não sobrevivem ao fechamento (sem reconexão na v0.3).

### segurança do terminal (obrigatório)

O pty dá execução de código arbitrário como o usuário. Toda falha aqui é RCE.

1. só WebUI confiável `chrome://terminal` (não `chrome-untrusted`, que existe para conteúdo menos confiável). O binder Mojo é registrado só para `TerminalUI` via `RegisterWebUIControllerInterfaceBinder<terminal::mojom::PageHandlerFactory, TerminalUI>`; nenhum outro frame, extensão ou site recebe a interface. Conferir também que o frame é o principal e a origem é exatamente `chrome://terminal` antes de criar o handler.
2. sem `iframe` de conteúdo web, sem recursos remotos, CSP padrão da WebUI (sem `unsafe-eval`, Trusted Types). xterm.js só renderiza texto; links OSC 8 abrem em aba normal via handler, nunca navegam a WebUI.
3. sites não navegam para `chrome://` (regra do upstream) e a linha de comando não abre `chrome://` (`src/chrome/browser/ui/startup/url_util.cc`, já registrado em `docs/BUILD.md`); manter. Não habilitar em convidado, incógnito nem perfis de sistema.
4. extensões: content scripts não rodam em `chrome://` e `chrome.debugger` não anexa a `chrome://` por padrão; documentar que `--extensions-on-chrome-urls` e `--remote-debugging-port` anulam isso (já são equivalentes a execução de código). Revisar se algum patch da série (Helium `override-chrome-protocol`, branding-scheme) muda essas checagens para `aerographene://`.
5. nenhum comando vem do renderer como argv: o renderer só manda bytes para o pty de uma sessão aberta pelo usuário; `Open` não aceita comando nem cwd arbitrário na v0.3 (cwd = `HOME`).
6. limites: no máximo N sessões por aba (ex.: 16), tamanho de mensagem limitado, `mojo::ReportBadMessage` para id desconhecido ou tamanho inválido.
7. fds: `O_CLOEXEC` no mestre, `fds_to_remap` só com o escravo; nenhum fd do browser vaza para o shell (LaunchProcess fecha o resto).
8. review de segurança dedicado (opus) antes do merge, mais teste com página web tentando `chrome://terminal` (window.open, link, iframe, `location`) e extensão de teste.

Status em 13/10/2026 (branch `v0.3-ui`, sem merge): C1 feito sem a entrada `-t` na command bar (`terminal-webui.patch`); C2 escrito (`terminal-pty.patch`: `TerminalSession` + `terminal_session_unittest.cc` com eco, líder de sessão/tty, tamanho inicial e resize, tamanhos inválidos, ambiente limpo, morte do grupo e idempotência). Compilam no overlay: `aero_terminal_ui.o`, `terminal_session.o`, `terminal_session_unittest.o`; `gn check` OK em `aero_terminal:*`. Não verificado: execução dos testes (mesmo bloqueio do link da B2), página no navegador. C3+ (Mojo, xterm.js) não começadas.

Status em 13/10/2026, madrugada (branch `v0.3-ui`, sem merge): C3 escrita em `terminal-xterm.patch` (xterm.js 6.0.0 vendorizado, MIT, sha256 do tgz no cabeçalho) e `terminal-bridge.patch` (`TerminalHandler` + `TerminalHost`, alvo `aero_terminal:host`, teste `terminal_host_unittest.cc`). Segurança cumprida no código: itens 1 (só o `AeroTerminalUI` adiciona o handler; cada mensagem confere frame principal e origem `chrome://terminal`; off-the-record recusado pelo config), 2 (sem rede; `script-src 'self'`; `style-src` ganhou `'unsafe-inline'` só nesta página porque o xterm.js cria `<style>`), 5 (`open(cols, rows)` sem comando nem cwd), 6 parcial (16 sessões por aba, escrita até 64 KiB, tamanhos 1..1000, mensagem malformada ou id desconhecido descartado; `WebUIMessageHandler` não tem `ReportBadMessage`) e 7 (herdado da C2). Pendentes: 3/4 (revisar `override-chrome-protocol`/branding-scheme), 8 (review opus e teste negativo com página web/extensão), backpressure (saída de `yes` sem limite de fila no renderer; `Write` bloqueante pode travar a sequência se o shell não ler). Mesmo desvio da B: mensagens WebUI em vez de Mojo. Validado: 7 `TerminalSessionTest.*` e os testes `TerminalHostTest.*` (eco pelo shell, resize, limite de sessões, destruir o host mata o shell) no executável mínimo `aero_ui_tests` do overlay: 18/18 passam (7 VaultReader, 7 TerminalSession, 4 TerminalHost); `terminal_handler.o`, `terminal_host.o`, `aero_terminal_ui.o` compilam; `gn check` OK em `aero_terminal:{aero_terminal,host,unit_tests}`. Não verificado: página no navegador (xterm sob a CSP/Trusted Types reais, vim/htop, Ctrl+C), link do `chrome`.

Status em 13/10/2026, manhã (branch `v0.3-ui`, sem merge): achados do review de segurança (veredito FAIL) corrigidos. HIGH: `Write` bloqueante no pty travava a sequência BLOCK_SHUTDOWN ao colar >~22 KiB num programa que não lê; agora o mestre é O_NONBLOCK, `TerminalSession::WriteSome` nunca bloqueia e o `TerminalHost` mantém fila por sessão (teto 1 MiB, excesso descartado com evento `writeDropped`) drenada por `WatchWritable`. MEDIUM: saída com créditos (host para de ler acima de 256 KiB sem `ack`; a página manda `ack(id, bytes)` no callback de `term.write`). LOW: limite global de 64 sessões no processo; vault com `open(O_NOFOLLOW|O_NONBLOCK)` + `fstat`/`S_ISREG` (lista usa `lstat`, só diretório e arquivo regular); `NotesHandler` confere frame principal e origem `chrome://notes` e `pickVault` exige `HasTransientUserActivation`; `markdown.js` com inline linear (cada regra guarda o próximo match) e só 64 KiB por linha interpretados. Info: wiki do terminal documenta que `--remote-debugging-port`/CDP equivale a execução de código. Mantida BLOCK_SHUTDOWN (precisa matar os grupos no fechamento; nada mais bloqueia indefinidamente, só a espera de até 200 ms por sessão no `Terminate`). TOCTOU da vault segue para B4. Validado no overlay do Cezanne: 24/24 testes em `aero_ui_tests` (8 VaultReader, 8 TerminalSession, 8 TerminalHost; novos: FIFO, `WriteNeverBlocks`, colar em programa que não lê, 1 MiB em `cat` + Close, pausa até ack, limite global); `gn check` OK em `aero_terminal:{aero_terminal,host,unit_tests}` e `aero_notes:{aero_notes,unit_tests}`; compilados `vault_reader.o`, `terminal_session.o`, `terminal_host.o`, os três `*_unittest.o`, `notes_handler.o`, `terminal_handler.o`; `markdown.js` passa os 10 casos e linhas de 1 MB em ~25 ms no DOM simulado (a versão anterior passava de 60 s). Série aplica com `--fuzz=0` e reproduz a árvore compilada. Não verificado: página no navegador (ack/`writeDropped` reais, seletor exigindo gesto), novo review.

Status em 13/10/2026, tarde (branch `v0.3`): C4 em `terminal-c4.patch`. Mudança de requisito do dono: título da aba sempre `t: workspace N` (revoga `t: <processo>`/`t: N terminals` das fatias; processo em primeiro plano só no tooltip da janela). Feito: pan/zoom, layout em `localStorage` por workspace (desvio: não é pref do perfil), `-t`/`-t N` na command bar (parser em `components/omnibox/browser`, gancho em `BuiltinProvider::Start`). Validado no overlay `/tmp/aero-c4` do Cezanne: `aero_ui_tests` 47/47 (novos: `AeroTerminalCommandTest.*` 3, `TerminalSessionTest.ForegroundProcessName`, `TerminalHostTest.ForegroundProcess`); `builtin_provider.cc` e `terminal_handler.cc` passam `-fsyntax-only` com os flags da `out/Default`; `terminal.js` rodado com DOM falso (título, zoom, pan, arrasto sob zoom, persistência, restauração, limite de 16, layout corrompido). Não verificado: página no navegador, `-t` na omnibox real, aceite "4 terminais ativos; fechar aba não deixa processo (`pgrep`)" no navegador, bench.

Status em 13/10/2026, fim da tarde (branch `v0.3`): C5 em `terminal-c5.patch`. Itens 3 e 4 cumpridos e revisão dos patches `terminal-*` contra 1–8 (detalhe em `docs/wiki/terminal.md`, seção "revisão de segurança C5"). Corrigido: perfil permitido passa a ser só `kRegular` (antes `!IsOffTheRecord` aceitava perfil de sistema e o original do convidado); links OSC 8 do xterm.js não abrem mais `about:blank` com a origem `chrome://terminal` (só http(s), `noopener,noreferrer`). Revisado sem mudança: `override-chrome-protocol`/branding-scheme não afrouxam extensões (`aerographene` não é esquema de extensão; `IsRestrictedUrl` e debugger recusam) nem a linha de comando (`url_util.cc` intocado). Validado no overlay `/tmp/aero-c4` do Cezanne: `aero_ui_tests` 49/49 (novos `TerminalAccessTest.OnlyRegularProfile` e `.OnlyChromeTerminalMainFrame`, negativos para seis tipos de perfil e onze origens/frames); `terminal_handler.cc` e `aero_terminal_ui.cc` passam `-fsyntax-only` com os flags da `out/Default`; `gn check` OK em `aero_terminal:*`; patch aplica com `--fuzz=0`. Pendentes: item 8 (review opus e teste negativo no navegador com página web e extensão), `ReportBadMessage` (inexistente em mensagens WebUI), bench `--quick` sem a aba, página no navegador.

Fatias:

1. C1 esqueleto `chrome://terminal` + quadro estático com janelas falsas (drag/resize/fechar) só em front. Aceite: compila, abre, nada no startup.
2. C2 `TerminalSession` (pty + launch + leitura) com teste unitário: abre `/bin/sh -c 'echo ok'`, lê `ok`, resize muda `stty size`, fechar mata o grupo (sem zumbi, `waitpid`). Aceite: `unit_tests --gtest_filter=TerminalSession*` no overlay.
3. C3 Mojo + binder restrito + xterm.js numa janela. Aceite: shell interativo (vim, htop, cores, Ctrl+C), teste negativo de acesso pela web.
4. C4 várias janelas, título por OSC 0/2 e `t: ...`/`t: N terminals`, foco e teclado, persistência do layout. Aceite: 4 terminais ativos; fechar aba não deixa processo (`pgrep`).
5. C5 hardening (limites, bad message, convidado/incógnito) + review de segurança + wiki. Aceite: zero Critical/High do review; bench `--quick` sem a aba dentro de 2%.
6. C6 command bar `t:` e UX do workspace (pedido do dono, 13/10/2026; substitui o `-t N` da C4):
   - `t:` sozinho + Enter: abre um workspace novo com um terminal aberto. `t: <comando>` + Enter: idem, e o comando roda nesse terminal depois que a página carrega (ou após 0,5 s, o que vier depois). Digitar `t:` deixa a command bar com aparência de linha de comando.
   - o comando nunca viaja na URL nem em parâmetro que outra origem possa forjar: vai do navegador ao handler por canal interno, uso único, ligado à aba recém-aberta; vira texto digitado no pty (como se o usuário digitasse), sem `exec` direto.
   - todo terminal aberto pelo aerographene começa com um resumo estilo fastfetch, impresso pela página antes do prompt (não depende de `fastfetch` instalado; funciona no Windows): logo ASCII do gatinho (arte braille do dono), versão do Chromium, versão do aerographene, CPU, GPU, RAM e discos. Dados vêm do processo do navegador (`base::SysInfo`, GPU info); nada sai da máquina.
   - cantos do workspace: um botão abre a sidebar com todos os terminais abertos (clicar leva/centraliza e foca o terminal) e um botão `+` abre terminal novo. A barra superior atual sai.
   - barra de título de cada terminal só com `×`. Arrastar a janela só pela barra de título; no conteúdo o mouse seleciona texto para copiar.
   - foco: com um terminal focado, todo input vai para ele (Ctrl+C manda SIGINT, Ctrl+Shift+C copia, Ctrl+Shift+V cola); atalhos do navegador não roubam essas teclas. Clicar fora de qualquer terminal tira o foco.
   - título da aba continua `t: workspace N`.
   Aceite: unittests do parser `t:` e do canal do comando (recusa sem aba de destino, uso único); teste da página para foco/teclas/sidebar; review de segurança do canal do comando sem Critical/High.

Status em 13/10/2026, fim da tarde (branch `v0.3`): C6 feita em `terminal-c6.patch` (parser `t:`, aba nova para `t:` e `o:` sozinho, canal de uso único, mensagem `start`), `terminal-c6-page.patch` (página: cantos, sidebar, banner com o gatinho, foco/teclas, `?new=1`) e `terminal-c6-look.patch` (aparência de `t:`/`o:` na command bar); `patches/aerographene/terminal-cat.txt` virou recurso da página (`banner.js`) e foi apagado. Validado no overlay `/tmp/aero-c4` do Cezanne (com os hunks não-`notes.js` do `notes-b6` aplicados): os três patches aplicam com `--fuzz=0` sobre o estado da série e reproduzem a árvore testada; `aero_ui_tests` 60/60 (inclui `AeroTerminalCommandTest.*` do `t:`, `AeroNotesCommandTest.*` e 7 `TerminalLaunchTest.*`: recusa sem aba de destino, uso único, preso à aba, validade, registro); página no Chrome headless com handler simulado: 51/51 (`tests/terminal-page/`). Ver a linha de `-fsyntax-only` na wiki do terminal. Não verificado: fluxo real da omnibox (aba nova, comando chegando ao shell), aparência da command bar, atalhos com os aceleradores reais, GPU real no resumo; review de segurança do canal (aceite da C6) pendente.

Patches esperados: `aerographene/terminal-pty.patch` (sessão, host, `BUILD.gn`, unittest), `aerographene/terminal-webui.patch` (controlador, mojom, binder), `aerographene/terminal-resources.patch` (quadro, xterm.js), `aerographene/terminal-tab.patch` (rótulo, command bar `-t`). Só Linux na v0.3 (`BUILDFLAG(IS_LINUX)`); Windows (ConPTY) fica para depois.

## D. Windows 10 e 11 por cross-compile no Cezanne

Alvo (decisão do dono, 13/10/2026): Windows 10 e 11 x64, mesma base. Nada exclusivo do Windows 11: APIs, manifesto e instalador precisam funcionar no Windows 10 (piso: 1809, primeira versão com ConPTY). O teste real é só no Windows 11; o Windows 10 fica "suportado, não testado".

Pedido do dono (13/10/2026): tentar cross-compilar no Cezanne; se exigir atenção especial, compilar depois numa máquina Windows (ADR 0008 recomendava runner Windows; esta decisão o substitui como primeira tentativa).

Viabilidade (fatos + avaliação):

- suportado pelo upstream (`target_os="win"`, clang-cl, lld-link), documentado em `docs/win_cross.md`. Exige o pacote VS+SDK no hash exato `3bfcb536c8` (VS 2026 18 + SDK 10.0.28000) gerado numa máquina Windows com `build/vs_toolchain.py`/`package_from_installed.py`, apontado por `DEPOT_TOOLS_WIN_TOOLCHAIN_BASE_URL` e `GYP_MSVS_HASH_3bfcb536c8`.
- licença: o pacote contém VS e SDK da Microsoft; uso próprio no runner com licença do dono é o caso normal, redistribuir não. O zip do toolchain nunca vai para o repo público, artifact nem release; fica só no disco do runner (ou em storage privado). Conferir os termos do VS Community/Build Tools para uso em CI (decisão em aberto 6).
- ungoogled-chromium-windows e helium-windows não fazem cross: só reutilizamos os patches `windows/` do helium-windows (GPL-3.0) e o `flags.windows.gn`. O portablelinux não tem lado Windows: árvore e container Linux servem, mas o tarball podado do ungoogled pode não trazer partes só-Windows (a confirmar com `gn gen` de diagnóstico, barato).
- ressalvas conhecidas do cross: `.asm` stubados, Crashpad sem relatório (irrelevante, não reportamos crash), PGO Windows usa perfil `win64`.
- custo: segundo `out/Win` (~20–30 GB, hipótese), sem ccache útil do Linux (outro alvo): build fria ~8 h ou mais. Disco cabe nos 118 GB livres, mas apertado com `out/Avx1`.

Fatias:

1. D0 (sem build, esta noite) `gn gen out/WinProbe` com `target_os="win" target_cpu="x64"` e flags do Helium-windows, na cópia overlay: descobre o que falta no tarball e se o toolchain é exigido já no gen. Aceite: lista de erros/arquivos faltando.
2. D1 dono gera o pacote do toolchain numa máquina Windows (uma vez) e copia ao Cezanne fora do git. Bloqueio humano.
3. D2 alvo pequeno (`base`, depois `chrome/installer/mini_installer` só configurado) para validar toolchain. Aceite: `base.dll`/objetos linkam.
4. D3 série única Linux+Windows, Windows sem tirar funções (decisão do dono, 13/10/2026; detalhe em "desenho D3" abaixo). Pré-checagem estática em cada subfatia.
5. D4 build completa `chrome` + `mini_installer`. Aceite: abre no Windows 11 real (perfil novo, spaces, uBlock); sem dependência exclusiva do 11 (Windows 10 suportado, não testado).
6. D5 empacotamento (ver E4).

Se D1 não sair ou D2 mostrar bloqueio estrutural, cai para o ADR 0008 opção 1a (máquina Windows).

### desenho D3 (decisão do dono, 13/10/2026)

Revogado: a fatia D3 anterior deste plano ("série Windows: lista derivada sem `helium/linux/use-default-theme`, `process-names`, `branding-desktop`"), revogada pelo dono em 13/10/2026. No lugar:

- uma só série (`patches/series`) para Linux e Windows. Patches que tocam arquivos só-Linux continuam nela: aplicam na árvore Win e não entram na compilação Windows. Nada de série derivada.
- funções nossas ganham implementação Windows; Windows não perde função. `process-names` não precisa de equivalente (o Windows já mostra `aerographene.exe`).

subfatias:

1. D3a `build/win/prepare.sh` (reproduz os contornos 1–8 abaixo, com hash conferido) + `aerographene/windows-disable-rlz.patch` (substitui o contorno manual do erro 3). Feito em 13/10/2026, ver status abaixo.
2. D3b (feito em 13/10/2026, ver status abaixo) guardas `BUILDFLAG(IS_LINUX)` → `IS_LINUX || IS_WIN` em space-one-window, space-switch-in-place, theme-radius, theme-font, theme-import-cli, notes-webui/notes-render; POSIX cru trocado por `base::File` em theme-tokens, theme-repo, settings-theme-import. Na prática a leitura Windows é Win32 (`CreateFileW`), não `base::File`, para não disparar as asserções de bloqueio na thread de UI.
3. D3c confinamento Windows de notes-vault-reader e theme-repo: reparse points (abrir com `FILE_FLAG_OPEN_REPARSE_POINT`), só arquivo regular, nomes reservados (CON, NUL...), ADS (`:`), nomes 8.3, UNC e `\\?\`, comparação sem caixa, ponto/espaço final; com testes.
4. D3d branding Windows: install_static, `aerographene.exe`, `.ico`, VERSIONINFO, AppUserModelID, dados em `%LOCALAPPDATA%\aerographene`; theme-scheme no ThemeService Windows; ícones da barra de título em `WindowsCaptionButton`/`BrowserFrameViewWin`; JetBrains Mono embarcada.
5. D3e `TerminalSession` com ConPTY (`CreatePseudoConsole`, `CreateProcessW` + `PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE`, `ResizePseudoConsole`, Job Object com `KILL_ON_JOB_CLOSE`, shell pwsh → powershell → `ComSpec`), mesma interface do Linux; review opus.

D4 (`chrome.exe`) e D5 (instalador) seguem depois do D3.

### status D3b em 13/10/2026

- 12 patches da série alterados (mesma série Linux+Windows): guardas `IS_LINUX || IS_WIN` em space-one-window, space-switch-in-place, theme-radius, theme-font, theme-import-cli; ramo Win32 de leitura em theme-tokens, theme-repo e settings-theme-import (archive); página de notas registrada no Windows (notes-webui, notes-render, notes-vault-reader), com `kVaultReadSupported = false` no Windows: `listDir`/`readNote` respondem "unsupported" e `vault_reader` devolve `nullopt` até a D3c (nunca lê sem confinamento); terminal-webui só ajuste de contexto. Dados do tema no Windows em `%LOCALAPPDATA%\aerographene\` (provisório até a D3d); fonte reserva do pixelized: Consolas.
- ramo Windows das leituras de arquivo: `CreateFileW` com `FILE_FLAG_OPEN_REPARSE_POINT`, recusa o que não for `FILE_TYPE_DISK`, reparse point (symlink/junction) e diretório, teto de tamanho antes e durante a leitura. É mais estrito que o Linux (que segue symlink em `theme.json` e `.aerotheme`); o confinamento do repositório (nomes reservados, ADS, 8.3, UNC, caixa) segue na D3c.
- Linux inalterado: `S_ISREG`, `O_NONBLOCK` contra FIFO, `lstat` sem seguir symlink em `.install-*`, `O_NOFOLLOW` na vault; nenhuma linha dessas foi removida dos patches.
- cadeia: série completa aplica numa árvore Win nova (123 patches); os 12 patches aplicam com `--fuzz=0` (os 4 do Helium já exigiam fuzz, como no CI). `gn gen out/Win` passa; 18 objetos afetados compilam no `out/Win` (3 deles recompilados depois do endurecimento de reparse point). Sem link do `chrome` (D4).
- Linux: alvo temporário `aero_ui_tests` (só num overlay da árvore do CI, não vai para a série) com os testes de VaultReader, TerminalSession, TerminalHost e, novos no conjunto, os de tema (archive 7 e repo 11): 42 de 42 passam em `out/T`. Rodar sem init no container dá 1 falha de instrumento (`TerminateKillsWholeGroup` espera que o PID 1 colha zumbis; `sleep infinity` não colhe); com `docker run --init` passa.
- não verificado: execução no Windows (nenhum teste roda lá; a árvore só compila objetos), `link` do `chrome`, build oficial com ThinLTO/PGO.

pendências para D3c: leitor confinado Windows para `notes-vault-reader` (ativar `kVaultReadSupported`), confinamento do repositório de temas (nomes reservados, ADS, 8.3, UNC/`\\?\`, caixa, ponto/espaço final, reparse point em diretórios intermediários), testes Windows dos dois; teste de junção `.install-*` no Windows (hoje só POSIX).

### status D3d em 13/10/2026

- `aerographene/windows-branding.patch` (último da série, `--fuzz=0` limpo) e `build/win/apply_assets.sh` (passo 9 do `prepare.sh`): install_static (`aerographene`, dados em `%LOCALAPPDATA%\aerographene\User Data`, AppUserModelID via `base_app_id`, ProgIDs e GUIDs próprios), `aerographene.exe` (BUILD, constantes, instalador, mini_installer), VERSIONINFO (`OriginalFilename`; resto do BRANDING), `.ico` de `branding/win`, glifos do tema nos botões da janela (Windows 10 e 11 iguais), JetBrains Mono (SIL OFL 1.1) em `<exe>\fonts` como fonte privada. theme-scheme: a classe base `ThemeService` já vale no Windows (não há `ThemeServiceWin`). Detalhes em `docs/wiki/windows.md`.
- não verificado: execução no Windows, link, se o DirectWrite/Skia enxerga a fonte `FR_PRIVATE`, mini_installer/instalador (D5), WebUI/renderers com a fonte.

### status D3a em 13/10/2026

- `build/win/prepare.sh` + `build/win/args.gn`: numa árvore Win nova (hardlink da árvore do CI, série revertida e reaplicada como o CI, com `windows-disable-rlz.patch` aplicando com `--fuzz=0`) o script repôs ciopfs, libfuse2, runtime clang win, clang-format, rc e `windows.0.52.0.lib` com hash conferido (sha256 do `.crate` = índice do crates.io) e extraiu o toolchain. 2ª execução: tudo "ok", 5 s.
- `gn gen out/Win`: 36219 alvos, sem passo manual. `ninja -j8 chrome_elf` (nice 19): 2820 passos, 445 s, `PE32+ executable (DLL) (GUI) x86-64`.
- Linux com o patch RLZ: `gn gen` com os args do CI (sem PGO/ccache) no container passa, 35139 alvos.
- quatro patches do Helium só aplicam com fuzz (`keyboard-shortcuts`, `ublock-install-as-component`, `crash-reporting-prefs`, `toolbar-button-prefs`; contexto alterado pela domain substitution); o CI aplica assim desde antes.
- pendente: o aviso `-Wl,--icf=all` no lld-link continua (D4).

### status D em 13/10/2026 (D0, D1, D2)

- D1 feito pelo dono: `cezanne-wsl:~/win-toolchain/b353c3b35e.zip` (VS 2026 + SDK 10.0.28000, `--noarm`). Fica fora do git, artifact e release (licenciado).
- D0 feito: árvore `~/aerographene-win/src` = `cp -al` da árvore base (sem `out/`), ~0 GB extra; toolchain extraído (`vs_files.ciopfs` 4,4 GB). `gn gen out/Win` passa: 36219 alvos.
- D2 feito: `base` compila (`obj/base/base.lib`, 2543 passos, ~5 min a -j8); `crashpad_handler.exe` (`PE32+ executable (GUI) x86-64, for MS Windows`) e `chrome_elf.dll` (`PE32+ executable (DLL) (GUI) x86-64`) linkam com lld-link. `base_unittests` falha (erro 9). `out/Win` 4,4 GB; espaço livre do host caiu de 97 para 85 GB no total (toolchain, `out/Win`, cópia do llvm-build, CI de outros projetos no mesmo host).
- procedimento completo e comandos em [docs/wiki/windows.md](wiki/windows.md).

args de `out/Win/args.gn` (os do Linux menos `use_sysroot`, `use_vaapi`, `rtc_use_pipewire`, `use_kerberos`, `use_system_libffi`, `pgo_data_path`, `cc_wrapper`):

```
target_os="win"  target_cpu="x64"  is_official_build=true  is_debug=false  is_component_build=false
is_clang=true  chrome_pgo_phase=0  symbol_level=0  blink_symbol_level=0  v8_symbol_level=0
use_thin_lto=true  thin_lto_enable_optimizations=true  use_icf=true  clang_use_chrome_plugins=false
disable_fieldtrial_testing_config=true  enable_hangout_services_extension=false  enable_mdns=false
enable_remoting=false  enable_reporting=false  enable_service_discovery=false  enable_widevine=true
exclude_unwind_tables=true  google_api_key=""  google_default_client_id=""  google_default_client_secret=""
safe_browsing_mode=0  treat_warnings_as_errors=false  use_official_google_api_keys=false
use_unofficial_version_number=false  blink_enable_generated_code_formatting=false  ffmpeg_branding="Chrome"
proprietary_codecs=true  fatal_linker_warnings=false  enable_rust=true  enable_rlz=false
```

erros encontrados e tratamento (todos só na árvore Win, nenhum patch da série alterado):

1. `vs_toolchain.py update`: `build/ciopfs` ausente (hook `ciopfs_linux` do DEPS não roda no tarball). Baixado de `chromium-browser-clang/ciopfs/<build/ciopfs.sha1>`; precisa de `libfuse.so.2`/`libulockmgr.so.1`, extraídos de `libfuse2t64` com `apt-get download` + `dpkg-deb -x` em `~/aerographene-win/root` (sem sudo) e `LD_LIBRARY_PATH`.
2. `gn gen` com `use_sysroot=false` (flag do ungoogled-windows): a toolchain host Linux pede glib via `pkg-config` do host. Removido; usa o sysroot Debian da árvore.
3. `gn gen`: `//chrome/installer/setup:setup` e `//rlz:rlz_id` dependem de `//rlz:rlz_lib*`, que não existem porque o ungoogled força `enable_rlz_support = false`. Contorno local: dep removida de `chrome/installer/setup/BUILD.gn` e `rlz_id` condicionado a `enable_rlz_support` em `rlz/BUILD.gn`. `setup/uninstall.cc` ainda inclui headers do RLZ: vira patch na série Windows (D3), como no ungoogled-windows.
4. ninja em laço de "Regenerating ninja files": arquivos editados com mtime no futuro (relógio). `touch -d "2 minutes ago"` resolveu.
5. `clang_rt.builtins-x86_64.lib` ausente: o LLVM do tarball só tem runtimes Linux. Baixado `Win/clang-win-runtime-library-llvmorg-24-init-3796-g20e97c4b-27.tar.xz` (mesmo que `tools/clang/scripts/update.py` baixa com `target_os` win) em cópia real de `third_party/llvm-build` (a hardlinkada ficou em `llvm-build.hardlink-ci`).
6. `buildtools/linux64-format/clang-format` é symlink para `/usr/bin/clang-format` do container; o crubit precisa dele. Baixado de `chromium-clang-format/f5485c39…` (sha256 confere com o DEPS).
7. `build/toolchain/win/rc/linux64/rc` ausente (hook `rc_linux`). Baixado de `chromium-browser-clang/rc/<rc.sha1>` (sha1 confere).
8. `windows.0.52.0.lib` do crate vendorizado `windows_x86_64_msvc-v0_52` podado pelo ungoogled (binário). Recuperado do `.crate` 0.52.6 do crates.io.

9. `base_unittests`: `base/i18n/rtl_unittest.cc` com `hex escape sequence out of range`, porque a substituição de domínios do ungoogled troca `google.com` por `9oo91e.qjz9zk` logo após `\x202e`. Só testes; não afeta o navegador. Por isso o PE de prova foi `crashpad_handler`/`chrome_elf`.

aviso no link: `lld-link: warning: ignoring unknown argument '-Wl,--icf=all'` (flag ICF de ELF chegando ao link Windows); investigar em D4, o ICF do Windows é `/OPT:ICF`.

Rust std `x86_64-pc-windows-msvc` é compilado da fonte pela build (`local_rustc_sysroot`): não falta toolchain Rust.

deps só-Windows vazias no tarball, prováveis bloqueios de D4: `third_party/microsoft_dxheaders/src`, `microsoft_webauthn/src`, `microsoft_multimedia_redirection/src`, `widevine/cdm/win`, `wix` (instalador MSI, dispensável). Outros binários podados pelo ungoogled podem aparecer em D4.

próximos passos: D3 (série Windows: patch RLZ do setup, tirar patches Linux-only, versões Windows de branding/tema; preparar script que reproduz os itens 1–8), depois obter as deps acima e tentar `chrome` + `mini_installer` (D4), só com runner livre.

## E. pacotes nativos sem recompilar

Objetivo: do `.tar.zst` já gerado, produzir no CI o `.pkg.tar.zst` (asset da release, `pacman -U`), o `.deb` e o `.rpm`; avaliar instalador Windows. Correção do dono (13/10/2026): o pacote Arch sai do próprio `packaging/arch/PKGBUILD` rodado no CI sobre o binário compilado; não haverá PKGBUILD `-bin` que baixa da release.

Arquitetura recomendada:

- Arch: `makepkg` dentro de um container `archlinux:base-devel` (usuário não-root, sem rede para fontes) com o `PKGBUILD` apontando para o `.tar.zst` local (hoje `source=` aponta para a URL da release e `sha256sums` é `SKIP`: passar a `source` local + sha256 calculado no step, ou `makepkg` com `SRCDEST`/arquivo já no diretório). Saída renomeada `aerographene-vX.Y.Z-avx2-linux.pkg.tar.zst`.
- deb/rpm: nfpm (Go, Apache-2.0, binário único com sha256 fixado) com `packaging/nfpm.yaml` espelhando o layout do PKGBUILD (`/opt/aerographene`, symlink `/usr/bin/aerographene`, `.desktop`, MIME, ícones, wrapper, `chrome-sandbox` 4755, dependências por distro). fpm exigiria Ruby; dpkg-deb/rpmbuild separados duplicam a descrição.
- onde: step depois do upload no `build.yml` (o binário está no runner) ou no `release.yml` a partir do artifact; recomendo `release.yml` (minutos, não ocupa a janela de build). Docker já existe no runner.

Nomes: `aerographene-vX.Y.Z-avx2-linux.{tar.zst,pkg.tar.zst,deb,rpm}` (e `avx1`), mais `SHA256SUMS`. Formato da release segue a nota do vault `agents/procedimentos/navegador-fork-formato-release.md`.

Fatias:

1. E1 `PKGBUILD` aceita tarball local (sem baixar da release) e `packaging/build-native.sh <tar.zst> <cpu> <versão>` (Bash `set -euo pipefail`) roda `makepkg` no container Arch e nfpm para deb/rpm. Aceite: os três gerados; `tar -tf`, `dpkg-deb -c`, `rpm -qlp` listam o esperado; `namcap` no pkg.
2. E2 instalar e checar: `pacman -U` em container Arch, `.deb` em `ubuntu:24.04`, `.rpm` em `fedora`, cada um com `aerographene --version` e `ldd` sem faltas; remoção limpa. Aceite: os três instalam e desinstalam.
3. E3 `release.yml` usa o padrão de nomes novo e anexa pkg/deb/rpm, um conjunto por cpu quando A estiver pronta. Aceite: release draft de teste com todos os assets e `SHA256SUMS`.
4. E4 Windows: o Chromium gera `mini_installer.exe` (alvo `mini_installer`; o Helium põe NSIS por cima). Recomendação: zip portátil + `mini_installer`; NSIS só se o dono quiser instalador com páginas; `makensis` roda nativo no Ubuntu (pacote `nsis`), sem wine. Depende de D4.

## ordem e dependências

1. E1–E3 (independe de tudo, usa o artefato v0.2/v0.3 existente).
2. A1–A2 (mudança de `build/` e workflow) → A3 (8 h de runner).
3. B1 e C1 em paralelo (arquivos disjuntos), compilação parcial no overlay; depois B2–B6 e C2–C5.
4. D0 qualquer hora (só `gn gen` no overlay); D1 bloqueia D2–D5.
5. E4 depois de D4.
6. fecho: build v3 completa com B+C, smoke, bench `--quick` contra Helium, build avx1 final, release draft.

## estimativa de runner

- A3: 1 build fria (~8 h) + 1 final (~1–2 h se só a série mudar, `out/Avx1` quente).
- B e C: ~6–10 compilações parciais (minutos cada) + 2 builds v3 completas incrementais (~1–3 h cada; mudanças em `chrome/browser` e grds recompilam bastante).
- D: D0 minutos; D4 ≥8 h fria, provavelmente 2 tentativas.
- E: nenhuma build; minutos por release.
- total realista: 4–6 noites de runner.

## subconjunto factível nesta noite (~8 h, runner livre)

1. E1–E3 (pacotes nativos e release.yml) com teste local: barato, sem runner.
2. A1–A2 e disparar A3 (build avx1 fria) como a carga longa da noite. Antes de disparar, usar o runner para as compilações parciais rápidas abaixo.
3. B1 e C1 escritos, pré-checados e compilados só por objeto no overlay; C2 (`TerminalSession` + unittest) se sobrar tempo, também só no overlay.
4. D0 (`gn gen` Windows de sondagem) no overlay, sem build.

Não cabe na noite: B2+ e C3+ funcionando no navegador, D com toolchain (depende do dono), avx1 testada na Ivy Bridge (depende do hardware).

## riscos

- A: SIGILL por código com AVX2 incondicional fora de dispatch; alternância de `MARCH` re-patcheia a árvore compartilhada; disco.
- B: corrida entre editor e edição externa; vaults grandes (milhares de arquivos) travando a árvore: listar sob demanda.
- C: RCE se o binder vazar; zumbis/órfãos; inundação de IPC com saída rápida (`yes`); renderer da WebUI congelando com xterm em muitas janelas.
- D: toolchain/licença, partes Windows podadas do tarball, tempo; pode cair para máquina Windows.
- E: dependências de libs diferem por distro (nomes de pacote `libnss3` vs `nss`); `chrome-sandbox` setuid em rpm/deb.
- geral: rebase do Chromium a cada major multiplica B/C/D.

## decisões em aberto (com recomendação)

1. alvo avx1: `-march=ivybridge` (recomendado, inclui F16C/PCLMUL/RDRAND; é a Ivy do dono) ou `x86-64-v2 -mavx` literal (mais portátil para Sandy Bridge). Recomendo `ivybridge`, nome do asset `avx1`.
2. PGO na avx1: manter perfil oficial (recomendado) e medir; desligar só se medir pior.
3. segunda sidebar das notas: painel dentro da página (recomendado, custo zero e sem tocar Views) ou side panel nativo com escopo de aba.
4. bibliotecas JS (markdown-it, xterm.js): baixar com sha256 no `inner.sh` (recomendado, como uBlock) ou embutir no patch.
5. editor: `textarea` + preview na v0.3 (recomendado); CodeMirror depois.
6. Windows: dono confirma que pode gerar o pacote VS+SDK numa máquina Windows e aceita os termos; senão, ADR 0008 opção 1a.
7. terminal habilitado por padrão ou atrás de opção em configurações: recomendo opção ligada por padrão, mas desligada em convidado/incógnito e sem nada no startup.

## resumo para agentes

- v0.3 = A (avx1), B (`chrome://notes`), C (`chrome://terminal` com pty), D (Windows cross), E (pkg via PKGBUILD no CI, deb, rpm). Google Sync fora.
- B/C: WebUI confiável + Mojo restrito ao controlador; nada no startup; sidebar das notas dentro da página.
- pty: `posix_openpt` + `base::LaunchProcess` (`fds_to_remap`, `pre_exec_delegate` com `setsid`/`TIOCSCTTY`), padrão de `remoting/host/terminal_session_linux.cc`.
- noite: E1–E3, A1–A2 + build avx1, B1/C1 (e C2) por objeto, D0.

## status em 13/10/2026 (fatias A e E)

- merge de `origin/main` (v0.2.1 + baseline v0.2) na `v0.3`; versão do produto 0.3.0 em `build/config.sh`, `branding-version.patch`, PKGBUILD e `.SRCINFO` (a build confirmou `aerographene-0.3.0-...` no nome do artefato).
- A1/A2 (parametrizar cpu, input `cpu` no build/release): feitas e usadas nos runs abaixo.
- E1-E3 (pacotes `pkg.tar.zst`/`deb`/`rpm` no `release.yml`): feitas; o draft v0.3.0 saiu com os quatro formatos avx2 + `SHA256SUMS` + `namcap-avx2.txt`.
- runs: build avx2 38352856892 verde (9e41178, PGO, smoke do próprio build verde); smoke.yml 38353472937 verde; release.yml 38353528300 verde (draft v0.3.0, avx2); build avx1 38353476105 (ver abaixo).
- A3/A4 (build avx1 completa, verificação de ISA, teste em Ivy Bridge): pendentes até o resultado do run avx1.
