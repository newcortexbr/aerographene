# notas

página interna `aerographene://notes` (por baixo, `chrome://notes`) para ler e editar uma vault de notas Markdown no estilo Obsidian. Plano completo em [`docs/PLANO-V0.3.md`](../PLANO-V0.3.md), seção B.

## estado atual (v0.3, em desenvolvimento)

leitura funcionando no código, mas ainda não aberta no navegador: escolher a pasta, navegar na árvore e ver a nota renderizada. Sem edição.

validado até aqui (Chromium 154, Cezanne, overlay): os patches aplicam sem fuzz, os objetos compilam e os 7 testes da leitura confinada passam (executável mínimo com só `base` e `gtest`). O renderizador de Markdown passou 10 casos num DOM simulado em Node, incluindo `<script>`, `onerror=` e `javascript:`. Não testado: a página aberta no navegador e o seletor de pasta real.

- feito (B1, `patches/aerographene/notes-webui.patch`): página estática com uma segunda barra lateral da vault dentro da própria página (redimensionável com o mouse ou com as setas no divisor) e a área da nota. A sidebar do navegador e os painéis laterais não são tocados.
- feito (B2, parte backend, `patches/aerographene/notes-vault-reader.patch`): código que lista e lê a vault sem sair da pasta escolhida, com testes unitários.
- feito (B2 ligação e B3, `patches/aerographene/notes-render.patch`): botão "escolher pasta" (diálogo de pasta do sistema; a escolha fica salva no perfil), árvore lateral que abre pastas sob demanda e visualização da nota em Markdown. `[[wikilinks]]` abrem a nota com esse nome ao lado da atual ou na raiz da vault.
- falta: imagens nas notas, live preview e edição (decisão de `theming/1/DECISIONS.md`), salvamento, observação de mudanças, aba única com rótulo `o: arquivo.md` e entrada `-o` na command bar, e a migração para Mojo (hoje usa mensagens WebUI).

## como funciona

- custo zero no startup: só a entrada de configuração da página é registrada; controlador e recursos nascem quando uma aba abre `aerographene://notes`.
- desabilitada em janelas anônimas e no perfil convidado.
- sem rede: a política de segurança (CSP) da página bloqueia tudo que não seja o próprio HTML, CSS e JS dela (`default-src 'none'`, `connect-src 'none'`, sem script inline, Trusted Types ligado).
- só Linux.

## render do Markdown

`markdown.js` é um renderizador próprio e pequeno (markdown-it exigiria mudar `build/inner.sh`). Ele nunca interpreta HTML: monta a nota criando elementos e texto, então HTML escrito na nota (`<script>`, `<img onerror=...>`) aparece como texto. Links só abrem se forem `http(s)` ou `mailto`; `javascript:`, `data:` e `chrome:` ficam como texto. Imagens aparecem como `[imagem: nome]` por enquanto. Suporta títulos, parágrafos, listas (inclusive tarefas `- [x]`), citações, blocos de código, linha horizontal, negrito, itálico, tachado, código inline, links e wikilinks; o front matter YAML é escondido.

## segurança da leitura da vault

o caminho de cada arquivo vem da página e é tratado como não confiável:

- precisa ser relativo à vault, sem `..`, `.`, componentes vazios, NUL e com no máximo 4096 bytes;
- depois de resolver symlinks, o arquivo tem de continuar dentro da pasta real da vault: symlink para fora é recusado, symlink para dentro funciona;
- a listagem é por nível (árvore sob demanda), mostra pastas e arquivos `.md` e de imagem, esconde ocultos e para em 5000 itens;
- só `.md` é lido como nota, até 4 MiB.

limite conhecido: entre conferir o caminho e abrir o arquivo, alguém com acesso à pasta poderia trocar um componente por symlink. Fica para resolver junto com a escrita (B4).

## arquivos

- `chrome/browser/ui/webui/aero_notes/aero_notes_ui.{h,cc}`: configuração e controlador.
- `chrome/browser/resources/aero_notes/notes.{html,css,js}`: página.
- `chrome/browser/ui/webui/aero_notes/vault_reader.{h,cc}` e `vault_reader_unittest.cc`: leitura confinada e testes.
- `chrome/browser/ui/webui/aero_notes/notes_handler.{h,cc}`: mensagens da página (pasta, lista, leitura).
- `chrome/browser/resources/aero_notes/markdown.js`: renderizador.

## resumo para agentes

- `chrome://notes` = `AeroNotesUI` + `NotesHandler` (WebUIMessageHandler, `chrome.send`: `getVault`, `pickVault`, `listDir`, `readNote`; resposta por `cr.webUIResponse`, shim próprio em `notes.js`). Pref `aerographene.notes.vault_path` (FilePath) registrada em `browser_prefs.cc` sob `IS_LINUX`. Sem Mojo (desvio no plano, seção B), `AeroNotesUIConfig` registrado em `chrome_web_ui_configs.cc` sob `BUILDFLAG(IS_LINUX)`; recursos `IDR_AERO_NOTES_{HTML,CSS,JS}` em `chrome/browser/browser_resources.grd`; desabilitada em off-the-record.
- `aerographene::notes::{ResolveInVault, ListVaultDir, ReadVaultNote}` em `aero_notes/vault_reader.*`, I/O bloqueante (sequência MayBlock); alvo `aero_notes:unit_tests` ligado a `chrome/test:unit_tests` no Linux.
- recursos: `IDR_AERO_NOTES_MARKDOWN_JS`. Novos `IDR_` no `browser_resources.grd` exigem regenerar `gen/tools/gritsettings/default_resource_ids` (ação `update_resource_ids`) antes do grit, senão dá `IdRangeOverlap`.
- patches: `notes-webui` → `terminal-webui` → `notes-vault-reader` → `terminal-pty` → `notes-render` → `terminal-xterm` → `terminal-bridge` (compartilham blocos do grd, configs, `chrome/test/BUILD.gn`); ordem importa.
- testes rápidos sem `unit_tests`: executável temporário `aero_ui_tests` no overlay (main próprio, deps `base`, `gtest` e os `unit_tests` aero), compilando só as saídas ausentes e linkando à mão.
- validação: ver `docs/PLANO-V0.3.md`, seção B (status). Não testado no navegador.
