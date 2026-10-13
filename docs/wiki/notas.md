# notas

página interna `aerographene://notes` (por baixo, `chrome://notes`) para ler e editar uma vault de notas Markdown no estilo Obsidian. Plano completo em [`docs/PLANO-V0.3.md`](../PLANO-V0.3.md), seção B.

## estado atual (v0.3, em desenvolvimento)

leitura e edição no código (B4), ainda não testadas à mão no navegador com o backend real: escolher a pasta, navegar na árvore, abrir uma nota num editor com live preview, salvar, criar, renomear e apagar notas `.md`.

validado até aqui (Chromium 154, Cezanne, overlay): os patches aplicam com `--fuzz=0`, os objetos compilam e `aero_ui_tests` passa 55/55 (inclui 21 testes de vault: 8 de leitura e 13 de salvar, conflito, criar, renomear, apagar e symlink; executável mínimo com só `base` e `gtest`). A página (`notes.js` + `editor.js`) rodou 31 verificações num Chrome headless do próprio pacote, com um backend simulado em memória no lugar do `chrome.send`: renderização, linha crua, Enter/Backspace/desfazer, salvar, conflito, cópia, renomear, apagar, nova nota e o título da aba. Não testado: a página servida como `chrome://notes` (Trusted Types do WebUI, handler real), o seletor de pasta real e o Windows (lá a escrita responde "não suportado").

- feito (B1, `patches/aerographene/notes-webui.patch`): página estática com uma segunda barra lateral da vault dentro da própria página (redimensionável com o mouse ou com as setas no divisor) e a área da nota. A sidebar do navegador e os painéis laterais não são tocados.
- feito (B2, parte backend, `patches/aerographene/notes-vault-reader.patch`): código que lista e lê a vault sem sair da pasta escolhida, com testes unitários.
- feito (B2 ligação e B3, `patches/aerographene/notes-render.patch`): botão "escolher pasta" (diálogo de pasta do sistema; a escolha fica salva no perfil), árvore lateral que abre pastas sob demanda e visualização da nota em Markdown. `[[wikilinks]]` abrem a nota com esse nome ao lado da atual ou na raiz da vault.
- feito (B4, `patches/aerographene/notes-editor.patch`): editor de coluna única com live preview, escrita atômica com detecção de conflito, criar/renomear/apagar e abertura sem seguir symlink (ver as seções abaixo).
- feito (B5, `notes-b5.patch`): watcher da vault, busca por nome e conteúdo e imagens embutidas (seção "watcher, busca e imagens").
- feito (B6, `patches/aerographene/notes-b6.patch`, último da série): aba única por janela e entrada `o:` na command bar (seção "aba única e command bar").
- falta: a migração para Mojo (hoje usa mensagens WebUI), cor/ícone próprios da aba e a verificação como `chrome://notes` real.

## título da aba

decisão do dono em 13/10/2026: o título da aba de notas é sempre `o: <nome da vault>` (nome da pasta escolhida), nunca o nome do arquivo aberto. O nome do arquivo aparece só no cabeçalho da nota dentro da página. Sem vault escolhida o título é `o: notas`. Isso substitui o rótulo `o: <arquivo>.md` do plano (B6) e dos mockups C-r02 para o título da aba.

## aba única e command bar (B6)

command bar (prefixo `o:`, decisão do dono em 13/10/2026; vale a primeira troca de `-o` por `o:`):

- `o: <termo>` + Enter: abre a página de notas sem documento aberto. A barra lateral mostra a árvore com todos os documentos e o centro mostra os resultados da busca (B5, nome e conteúdo) pelo termo; clicar num resultado abre a nota. A URL é `chrome://notes/?q=<termo>`; a página lê `q` depois de carregar a vault. Termo de 2 a 256 unidades, sem caracteres de controle.
- `o:` sozinho + Enter: abre uma aba NOVA de notas, na raiz da vault, sem documento (o centro mostra a dica de sempre). A URL é `chrome://notes/?new=1`. Desde a C6 o Enter abre mesmo outra aba (antes navegava a atual): `ChromeOmniboxClient` troca a disposição para aba nova quando o match é o `o:` sozinho do `BuiltinProvider`.
- digitar `o:` deixa o texto da command bar em itálico, com o prefixo na cor de link (aparência de busca da vault; `terminal-c6-look.patch`).
- `o` sem distinção de caixa, espaço depois dos dois pontos opcional (`o:ideias` funciona). `o`, `ox:`, `o :` e `-o` não são o comando.
- o título da aba continua `o: <nome da vault>` em todos os casos; o termo nunca vai para o título.

aba única: `chrome::Navigate` trata `chrome://notes` (disposição atual, nova aba em primeiro plano ou singleton): se a janela já tem uma aba de notas, foca essa e a leva à URL pedida (o termo novo recarrega a página; nota com edição não salva pede confirmação pelo `beforeunload`); sem aba de notas, abre normalmente. Abas em segundo plano não são alteradas. Exceção: `?new=1` (o `o:` sozinho) não é dobrado e abre outra aba, a pedido do dono. Desde a C6 o `o:` sozinho força aba nova no Enter (ver acima). Verificado só por unit test do parser, `-fsyntax-only` de `builtin_provider.cc` e `browser_navigator.cc` e a página no Chrome headless; o comportamento no navegador não foi testado.

## editor (B4)

- uma visão só, estilo Obsidian: a linha com o cursor aparece como Markdown cru (um `textarea`), as outras são renderizadas por `markdown.js`. Clicar numa linha renderizada a ativa; as setas passam para a linha vizinha. Dentro de um bloco de código a linha ativa fica crua e as demais do bloco também.
- Enter divide a linha e continua listas, tarefas e citações (Enter num item vazio sai da lista); Backspace no início e Delete no fim juntam linhas; colar várias linhas divide em linhas; Ctrl+Z / Ctrl+Y (ou Ctrl+Shift+Z) desfazem e refazem; Ctrl+S salva.
- limite: não há seleção que atravesse várias linhas durante a edição (copiar do texto renderizado funciona); notas muito grandes refazem todo o bloco afetado a cada alteração estrutural.
- salvar: botão "salvar" ou Ctrl+S. O indicador mostra "● alterado" ou "salvo". Trocar de nota, escolher outra vault ou criar nota com alterações pendentes pergunta se salva ou descarta.
- conflito: a página guarda o mtime (microssegundos) do arquivo no momento em que o abriu. Se o arquivo mudou no disco, nada é gravado e aparece um aviso com "salvar como cópia" (cria `nome (conflito AAAA-MM-DD hhmmss).md` e abre a cópia), "sobrescrever o arquivo" ou "recarregar do disco (descarta o meu texto)". O texto do editor nunca é descartado sem escolha explícita. Se a nota foi apagada no disco, o aviso oferece recriá-la com o texto atual.
- "+ nota" cria uma nota (nome relativo à vault, `.md` é acrescentado se faltar), "renomear" move/renomeia sem sobrescrever outra nota, "apagar" pede confirmação e remove o arquivo de vez (não vai para a lixeira).

## segurança da escrita (B4)

- toda abertura (leitura e escrita) passa por `OpenVaultFileNoFollow`: parte de um descritor da raiz real da vault e abre cada componente do caminho com `openat(O_NOFOLLOW)`. Se qualquer componente, inclusive o último, for ou virar um symlink, a abertura falha: o arquivo aberto é sempre o que foi conferido. Symlink para dentro da vault continua funcionando porque é resolvido uma vez antes e aberto depois sem seguir nada.
- salvar: arquivo temporário oculto (`.aero-N.tmp`) na mesma pasta, `fsync`, `rename` sobre o original; o modo do arquivo é mantido. O mtime é conferido antes e de novo logo antes do `rename`. Janela restante: uma escrita externa nesse intervalo de microssegundos seria sobrescrita.
- criar usa `O_CREAT|O_EXCL|O_NOFOLLOW` (nunca substitui nem segue um symlink pendente); renomear usa `renameat2(RENAME_NOREPLACE)` (com verificação prévia se o sistema de arquivos não suportar) e nunca sobrescreve; apagar é `unlink`.
- só nomes `.md`, sem ponto inicial (a lista esconde ocultos), até 255 bytes; só arquivos comuns; uma entrada que é symlink não pode ser renomeada nem apagada pela página; diretório não pode ser criado, renomeado nem apagado; destino em pasta inexistente é recusado.
- Windows: escrita não suportada (`kVaultWriteSupported` false): salvar, criar, renomear e apagar respondem `unsupported` e a página mostra "escrita ainda não disponível neste sistema". A leitura é confinada desde a D3c (ver "Windows (D3c)").

## watcher, busca e imagens (B5)

- watcher: enquanto a aba existe, o navegador observa a pasta da vault (recursivo, inotify no Linux). Arquivo criado, alterado, renomeado ou apagado fora do navegador aparece na árvore em cerca de meio segundo. Caminhos ocultos (`.git`, `.obsidian`, `.aero-N.tmp` do próprio salvar) são ignorados. Fechar a aba (ou recarregar a página) remove o watcher. Se o sistema não deixar observar (limite de inotify), a barra mostra "(sem observar arquivos)" e a árvore só atualiza ao reabrir.
- nota aberta e edição externa: a página compara o mtime em disco com o que abriu. Nota sem alterações locais recarrega sozinha (o estado mostra "atualizado do disco"; o cursor volta ao início). Nota com alterações abre o mesmo aviso de conflito do salvar (salvar como cópia, sobrescrever, recarregar): nada é gravado nem descartado sem escolha. "cancelar" não repete a pergunta para a mesma versão do disco, mas salvar depois ainda cai no conflito. Se o disco passou a ter o mesmo texto do editor, só o mtime é atualizado. Nota apagada ou renomeada fora avisa (com texto alterado, ele continua no editor e salvar recria a nota).
- busca: campo no topo da barra lateral (Ctrl+Shift+F foca). Mínimo 2 caracteres; busca ~300 ms depois de digitar (Enter busca já, Esc limpa). Procura no nome de todos os arquivos listáveis e no texto das notas `.md`, sem distinguir maiúsculas de minúsculas (só ASCII: "É" não casa com "é"). Resultados: nomes primeiro, depois conteúdo, com a linha do primeiro acerto. Limites no navegador: 100 resultados, 20000 arquivos, 128 MiB de texto lido, 16 níveis de pasta, notas de até 4 MiB; passando disso aparece "resultado parcial". Não segue ocultos nem symlink para fora da vault.
- imagens: `![alt](caminho.png)` (relativo à pasta da nota, depois à raiz) e `![[nome.png|300]]` (só o nome acha o primeiro arquivo com esse nome na vault; `|300` é a largura). png, jpg, gif e webp até 10 MiB; SVG não. Imagem remota (`http:`), absoluta ou com esquema não carrega: aparece `[imagem: alt]`, como imagem que falta. `![[outra nota]]` aparece como `[nota embutida: ...]` (sem transclusão ainda).
- custo: sem aba de notas não há watcher nem busca; a atualização da árvore refaz a árvore inteira (pastas abertas incluídas) a cada rajada de mudanças.

## segurança de watcher, busca e imagens (B5)

- imagens passam pelo mesmo confinamento das notas (`ResolveInVault` + `openat` `O_NOFOLLOW` por componente, só arquivo comum, FIFO não trava); o browser devolve bytes em base64 e a página os mostra como URL `data:`. A CSP da página passou a `img-src 'self' data:` (nada de rede). Imagens ficam em cache por nota (até 48 Mi caracteres) e o cache é limpo a cada mudança na vault.
- busca e `FindVaultFileByName` andam pela árvore visível (mesmos filtros da listagem) com limites de arquivos, bytes e profundidade, então symlink em laço ou pasta enorme não prende o worker. Trechos e caminhos devolvidos são UTF-8 válido (o trecho é realinhado se o corte cai no meio de um caractere); nomes de arquivo que não são UTF-8 são ignorados na listagem, busca e imagens, porque `base::Value` exige UTF-8.
- o watcher usa a raiz real da vault; ele só avisa "mudou" (sem caminho), então a página nunca recebe nomes de arquivos por esse canal. Limitação: inotify recursivo observa também as pastas ocultas (cada uma gasta um watch), só o aviso é filtrado; vaults com milhares de pastas podem bater no limite do sistema.
- Windows (D3c): watcher (`FilePathWatcher` recursivo), busca e imagens funcionam pela leitura confinada; ver "Windows (D3c)".

## Windows (D3c)

- lista, leitura, busca, imagens e watcher funcionam; escrita não (acima).
- confinamento próprio do Windows, mais estrito que o Linux: nenhum reparse point (symlink, junção) abaixo da raiz é seguido nem listado; cada pasta do caminho fica aberta sem permitir apagar/renomear enquanto a leitura acontece; nome 8.3 (`NOTAS~1`), `:` (fluxos alternativos), ponto/espaço final, nomes reservados (`CON`, `NUL`, `COM1`...) e raiz UNC ou `\\?\` são recusados. Maiúsculas/minúsculas não importam, como no NTFS. Detalhe em `docs/wiki/windows.md`, seção "confinamento (D3c)".
- nomes que o Windows não abre de volta iguais não aparecem na árvore.

## como funciona

- custo zero no startup: só a entrada de configuração da página é registrada; controlador e recursos nascem quando uma aba abre `aerographene://notes`.
- desabilitada em janelas anônimas e no perfil convidado.
- sem rede: a política de segurança (CSP) da página bloqueia tudo que não seja o próprio HTML, CSS e JS dela (`default-src 'none'`, `connect-src 'none'`, sem script inline, Trusted Types ligado).
- Linux e Windows (no Windows sem escrita, D3c).

## render do Markdown

`markdown.js` é um renderizador próprio e pequeno (markdown-it exigiria mudar `build/inner.sh`). Ele nunca interpreta HTML: monta a nota criando elementos e texto, então HTML escrito na nota (`<script>`, `<img onerror=...>`) aparece como texto. Links só abrem se forem `http(s)` ou `mailto`; `javascript:`, `data:` e `chrome:` ficam como texto. Imagens aparecem como `[imagem: nome]` por enquanto. Suporta títulos, parágrafos, listas (inclusive tarefas `- [x]`), citações, blocos de código, linha horizontal, negrito, itálico, tachado, código inline, links e wikilinks; o front matter YAML é escondido. Para não travar com notas enormes, só os primeiros 64 KiB de cada linha recebem formatação; o resto aparece como texto.

## segurança da leitura da vault

o caminho de cada arquivo vem da página e é tratado como não confiável:

- precisa ser relativo à vault, sem `..`, `.`, componentes vazios, NUL e com no máximo 4096 bytes;
- depois de resolver symlinks, o arquivo tem de continuar dentro da pasta real da vault: symlink para fora é recusado, symlink para dentro funciona;
- a listagem é por nível (árvore sob demanda), mostra pastas e arquivos `.md` e de imagem, esconde ocultos e para em 5000 itens;
- só `.md` é lido como nota, até 4 MiB, e só se for arquivo comum: o arquivo é aberto sem seguir symlink e sem esperar (um FIFO chamado `x.md` não trava a leitura); FIFOs, sockets e dispositivos não aparecem na lista;
- as mensagens só são aceitas do frame principal com origem `chrome://notes`, e o seletor de pasta só abre a partir de um clique do usuário.

o antigo limite (alguém trocar um componente por symlink entre conferir e abrir) foi fechado na B4: a abertura percorre o caminho com `openat(O_NOFOLLOW)` (seção "segurança da escrita").

## arquivos

- `chrome/browser/ui/webui/aero_notes/aero_notes_ui.{h,cc}`: configuração e controlador.
- `chrome/browser/resources/aero_notes/notes.{html,css,js}`: página.
- `chrome/browser/ui/webui/aero_notes/vault_reader.{h,cc}` e `vault_reader_unittest.cc`: leitura confinada e testes.
- `chrome/browser/ui/webui/aero_notes/notes_handler.{h,cc}`: mensagens da página (pasta, lista, leitura).
- `chrome/browser/resources/aero_notes/markdown.js`: renderizador.
- `chrome/browser/resources/aero_notes/editor.js`: editor com live preview (modelo puro + visão).
- `chrome/browser/ui/webui/aero_notes/vault_watcher.{h,cc}` e `vault_watcher_unittest.cc`: watcher recursivo e testes (inotify real).
- `components/omnibox/browser/aero_notes_command.{h,cc}` e `_unittest.cc`: parser do `o:` e URL.
- `tests/notes-editor/`: verificação da página num Chrome headless com backend simulado (`run.sh`; cobre editor, watcher, busca e imagens).

## resumo para agentes

- `chrome://notes` = `AeroNotesUI` + `NotesHandler` (WebUIMessageHandler, `chrome.send`: `getVault`, `pickVault`, `listDir`, `readNote` (devolve `{text, mtime}`), `writeNote(path, text, expectedMtime|null)`, `createNote(path, text)`, `renameNote(from, to)`, `deleteNote(path)` (estes devolvem `{status, mtime}`; `status` = `ok|conflict|notFound|exists|invalid|tooLarge|unsupported|ioError`); resposta por `cr.webUIResponse`, shim próprio em `notes.js`). Pref `aerographene.notes.vault_path` (FilePath) registrada em `browser_prefs.cc` sob `IS_LINUX`. Sem Mojo (desvio no plano, seção B), `AeroNotesUIConfig` registrado em `chrome_web_ui_configs.cc` sob `BUILDFLAG(IS_LINUX)`; recursos `IDR_AERO_NOTES_{HTML,CSS,JS}` em `chrome/browser/browser_resources.grd`; desabilitada em off-the-record.
- título da aba = sempre `o: <nome da vault>` (`document.title` só em `showVault`); nunca o arquivo aberto (decisão do dono, 13/10/2026).
- escrita: `WriteVaultNote/CreateVaultNote/RenameVaultNote/DeleteVaultNote` + `OpenVaultFileNoFollow` (openat O_NOFOLLOW por componente) em `vault_reader.*`; token de conflito = mtime em µs; Windows responde `kUnsupported`. Patch `notes-editor` vem logo depois de `notes-render` na série; recurso `IDR_AERO_NOTES_EDITOR_JS`.
- `aerographene::notes::{ResolveInVault, ListVaultDir, ReadVaultNote}` em `aero_notes/vault_reader.*`, I/O bloqueante (sequência MayBlock); alvo `aero_notes:unit_tests` ligado a `chrome/test:unit_tests` no Linux e, com `vault_reader_win_unittest.cc` no lugar dos testes POSIX, no Windows (D3c, `windows-confine.patch`).
- recursos: `IDR_AERO_NOTES_MARKDOWN_JS`. Novos `IDR_` no `browser_resources.grd` exigem regenerar `gen/tools/gritsettings/default_resource_ids` (ação `update_resource_ids`) antes do grit, senão dá `IdRangeOverlap`.
- patches: `notes-webui` → `terminal-webui` → `notes-vault-reader` → `terminal-pty` → `notes-render` → `terminal-xterm` → `terminal-bridge` (compartilham blocos do grd, configs, `chrome/test/BUILD.gn`); ordem importa.
- testes rápidos sem `unit_tests`: executável temporário `aero_ui_tests` no overlay (main próprio, deps `base`, `gtest` e os `unit_tests` aero), compilando só as saídas ausentes e linkando à mão.
- validação: ver `docs/PLANO-V0.3.md`, seção B (status). Página verificada num Chrome headless com backend simulado (`tests/notes-editor/run.sh`); não testada como `chrome://notes` real.
- B5: `watchVault` (resposta bool; depois o evento `vaultChanged` por `FireWebUIListener`, shim `cr.webUIListenerCallback` em `notes.js`), `searchVault(query)` -> `{hits:[{path,nameMatch,snippet}], truncated}`, `readImage(path, noteDir)` -> `{mime, data}`. Backend em `vault_reader.*` (`SearchVault`, `FindVaultFileByName`, `ReadVaultImage`) e `vault_watcher.*`. O watcher é `SequenceBound<VaultWatcher>` no handler: morre com a aba. Patch `notes-b5` é o último da série.
- a página, ao receber `vaultChanged`: `syncExternal` (limpa cache de imagens, refaz a árvore, refaz a busca ativa, `checkOpenNote`). Edição externa em nota alterada reutiliza `resolveConflict` do B4. `markdown.js` recebe `opts.loadImage(path, img, onFail)` do editor; sem ele (ou com URL remota/absoluta) imagem vira texto.
- B6 (`notes-b6`, último da série): `aerographene::ParseNotesCommand(text)` -> `optional<u16string>` (termo; `""` para `o:` sozinho) e `NotesCommandUrl(termo)` (`chrome://notes/?q=<termo>` ou `?new=1`) em `components/omnibox/browser/aero_notes_command.*`, chamados em `BuiltinProvider::Start` logo após o `-t` do terminal-c4 (patch depende dele pelo contexto). Aba única: bloco em `NavigateImpl` (`browser_navigator.cc`, depois do hunk `kHeliumUIScheme`) converte para `SINGLETON_TAB` + `IGNORE_AND_NAVIGATE` quando `GetIndexOfExistingTabMatchingURL` acha uma aba `chrome://notes`; `query == "new=1"` fica de fora. Página: `openFromQuery()` em `notes.js` e `renderHits(target, r)` (compartilhada com a busca lateral). Teste da página com `?q=`: `tests/notes-editor/test-q.js` (rodado por `run.sh`).
