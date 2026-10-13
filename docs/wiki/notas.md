# notas

página interna `aerographene://notes` (por baixo, `chrome://notes`) para ler e editar uma vault de notas Markdown no estilo Obsidian. Plano completo em [`docs/PLANO-V0.3.md`](../PLANO-V0.3.md), seção B.

## estado atual (v0.3, em desenvolvimento)

ainda não é usável: só o esqueleto da página e o núcleo de leitura da vault existem, e nenhum dos dois foi testado no navegador.

validado até aqui: os patches aplicam sem fuzz e os objetos compilam (Chromium 154, Cezanne); os testes unitários compilam, mas ainda não foram executados.

- feito (B1, `patches/aerographene/notes-webui.patch`): página estática com uma segunda barra lateral da vault dentro da própria página (redimensionável com o mouse ou com as setas no divisor) e a área da nota. A sidebar do navegador e os painéis laterais não são tocados.
- feito (B2, parte backend, `patches/aerographene/notes-vault-reader.patch`): código que lista e lê a vault sem sair da pasta escolhida, com testes unitários. Ainda não ligado à página.
- falta: escolher a pasta, ligar a leitura à página por Mojo, render do Markdown (com live preview, decisão de `theming/1/DECISIONS.md`), edição e salvamento, observação de mudanças, aba única com rótulo `o: arquivo.md` e entrada `-o` na command bar.

## como funciona

- custo zero no startup: só a entrada de configuração da página é registrada; controlador e recursos nascem quando uma aba abre `aerographene://notes`.
- desabilitada em janelas anônimas e no perfil convidado.
- sem rede: a política de segurança (CSP) da página bloqueia tudo que não seja o próprio HTML, CSS e JS dela (`default-src 'none'`, `connect-src 'none'`, sem script inline, Trusted Types ligado).
- só Linux.

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

## resumo para agentes

- `chrome://notes` = `AeroNotesUI` (WebUIController puro, sem Mojo), `AeroNotesUIConfig` registrado em `chrome_web_ui_configs.cc` sob `BUILDFLAG(IS_LINUX)`; recursos `IDR_AERO_NOTES_{HTML,CSS,JS}` em `chrome/browser/browser_resources.grd`; desabilitada em off-the-record.
- `aerographene::notes::{ResolveInVault, ListVaultDir, ReadVaultNote}` em `aero_notes/vault_reader.*`, I/O bloqueante (sequência MayBlock); alvo `aero_notes:unit_tests` ligado a `chrome/test:unit_tests` no Linux.
- patches: `notes-webui.patch` → `terminal-webui.patch` → `notes-vault-reader.patch` → `terminal-pty.patch` (compartilham blocos do grd, configs, `chrome/test/BUILD.gn`); ordem importa.
- validação: ver `docs/PLANO-V0.3.md`, seção B (status). Não testado no navegador.
