# notas

página interna `aerographene://notes` (por baixo, `chrome://notes`) para ler e editar uma vault de notas Markdown no estilo Obsidian. Plano completo em [`docs/PLANO-V0.3.md`](../PLANO-V0.3.md), seção B.

## estado atual (v0.3, em desenvolvimento)

leitura e edição no código (B4), ainda não testadas à mão no navegador com o backend real: escolher a pasta, navegar na árvore, abrir uma nota num editor com live preview, salvar, criar, renomear e apagar notas `.md`.

validado até aqui (Chromium 154, Cezanne, overlay): os patches aplicam com `--fuzz=0`, os objetos compilam e `aero_ui_tests` passa 55/55 (inclui 21 testes de vault: 8 de leitura e 13 de salvar, conflito, criar, renomear, apagar e symlink; executável mínimo com só `base` e `gtest`). A página (`notes.js` + `editor.js`) rodou 31 verificações num Chrome headless do próprio pacote, com um backend simulado em memória no lugar do `chrome.send`: renderização, linha crua, Enter/Backspace/desfazer, salvar, conflito, cópia, renomear, apagar, nova nota e o título da aba. Não testado: a página servida como `chrome://notes` (Trusted Types do WebUI, handler real), o seletor de pasta real e o Windows (lá a escrita responde "não suportado").

- feito (B1, `patches/aerographene/notes-webui.patch`): página estática com uma segunda barra lateral da vault dentro da própria página (redimensionável com o mouse ou com as setas no divisor) e a área da nota. A sidebar do navegador e os painéis laterais não são tocados.
- feito (B2, parte backend, `patches/aerographene/notes-vault-reader.patch`): código que lista e lê a vault sem sair da pasta escolhida, com testes unitários.
- feito (B2 ligação e B3, `patches/aerographene/notes-render.patch`): botão "escolher pasta" (diálogo de pasta do sistema; a escolha fica salva no perfil), árvore lateral que abre pastas sob demanda e visualização da nota em Markdown. `[[wikilinks]]` abrem a nota com esse nome ao lado da atual ou na raiz da vault.
- feito (B4, `patches/aerographene/notes-editor.patch`): editor de coluna única com live preview, escrita atômica com detecção de conflito, criar/renomear/apagar e abertura sem seguir symlink (ver as seções abaixo).
- falta: imagens nas notas, observação de mudanças (B5), aba única e entrada `-o` na command bar (B6) e a migração para Mojo (hoje usa mensagens WebUI).

## título da aba

decisão do dono em 13/10/2026: o título da aba de notas é sempre `o: <nome da vault>` (nome da pasta escolhida), nunca o nome do arquivo aberto. O nome do arquivo aparece só no cabeçalho da nota dentro da página. Sem vault escolhida o título é `o: notas`. Isso substitui o rótulo `o: <arquivo>.md` do plano (B6) e dos mockups C-r02 para o título da aba.

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
- Windows: o código novo fica atrás das guardas existentes e responde `unsupported` (como a leitura), sem fallback sem confinamento, até o leitor confinado da D3c.

## como funciona

- custo zero no startup: só a entrada de configuração da página é registrada; controlador e recursos nascem quando uma aba abre `aerographene://notes`.
- desabilitada em janelas anônimas e no perfil convidado.
- sem rede: a política de segurança (CSP) da página bloqueia tudo que não seja o próprio HTML, CSS e JS dela (`default-src 'none'`, `connect-src 'none'`, sem script inline, Trusted Types ligado).
- só Linux.

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
- `tests/notes-editor/`: verificação da página num Chrome headless com backend simulado (`run.sh`).

## resumo para agentes

- `chrome://notes` = `AeroNotesUI` + `NotesHandler` (WebUIMessageHandler, `chrome.send`: `getVault`, `pickVault`, `listDir`, `readNote` (devolve `{text, mtime}`), `writeNote(path, text, expectedMtime|null)`, `createNote(path, text)`, `renameNote(from, to)`, `deleteNote(path)` (estes devolvem `{status, mtime}`; `status` = `ok|conflict|notFound|exists|invalid|tooLarge|unsupported|ioError`); resposta por `cr.webUIResponse`, shim próprio em `notes.js`). Pref `aerographene.notes.vault_path` (FilePath) registrada em `browser_prefs.cc` sob `IS_LINUX`. Sem Mojo (desvio no plano, seção B), `AeroNotesUIConfig` registrado em `chrome_web_ui_configs.cc` sob `BUILDFLAG(IS_LINUX)`; recursos `IDR_AERO_NOTES_{HTML,CSS,JS}` em `chrome/browser/browser_resources.grd`; desabilitada em off-the-record.
- título da aba = sempre `o: <nome da vault>` (`document.title` só em `showVault`); nunca o arquivo aberto (decisão do dono, 13/10/2026).
- escrita: `WriteVaultNote/CreateVaultNote/RenameVaultNote/DeleteVaultNote` + `OpenVaultFileNoFollow` (openat O_NOFOLLOW por componente) em `vault_reader.*`; token de conflito = mtime em µs; Windows responde `kUnsupported`. Patch `notes-editor` vem logo depois de `notes-render` na série; recurso `IDR_AERO_NOTES_EDITOR_JS`.
- `aerographene::notes::{ResolveInVault, ListVaultDir, ReadVaultNote}` em `aero_notes/vault_reader.*`, I/O bloqueante (sequência MayBlock); alvo `aero_notes:unit_tests` ligado a `chrome/test:unit_tests` no Linux.
- recursos: `IDR_AERO_NOTES_MARKDOWN_JS`. Novos `IDR_` no `browser_resources.grd` exigem regenerar `gen/tools/gritsettings/default_resource_ids` (ação `update_resource_ids`) antes do grit, senão dá `IdRangeOverlap`.
- patches: `notes-webui` → `terminal-webui` → `notes-vault-reader` → `terminal-pty` → `notes-render` → `terminal-xterm` → `terminal-bridge` (compartilham blocos do grd, configs, `chrome/test/BUILD.gn`); ordem importa.
- testes rápidos sem `unit_tests`: executável temporário `aero_ui_tests` no overlay (main próprio, deps `base`, `gtest` e os `unit_tests` aero), compilando só as saídas ausentes e linkando à mão.
- validação: ver `docs/PLANO-V0.3.md`, seção B (status). Página verificada num Chrome headless com backend simulado (`tests/notes-editor/run.sh`); não testada como `chrome://notes` real.
