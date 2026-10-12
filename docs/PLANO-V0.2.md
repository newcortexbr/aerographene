# plano da v0.2

Estado em 12/10/2026. Fontes: README (roadmap), `docs/SCOPE.md`, `docs/NOITE-20261012.md`, ADR 0007.

## itens

1. páginas internas seguem o tema: feito (PR #41); falta aprovação visual do dono (não há mockup).
2. storage de sites: sem dado frio (ADR 0007, 11/10/2026). Cache de sites apagado após 30 dias (`cold-data-cache-expire`, PR #16); cookies nunca frios; histórico, favicons e downloads vão para o frio. Não há reidratação nem exceções de frio.
3. seletor de tema na UI: não iniciado.
   - entrega: escolha do tema na página de configurações, aplicada na hora e guardada em pref. Cada tema define o próprio esquema (sem alternância claro/escuro).
   - hoje: pref `aerographene.theme` lida em `ThemeService::Init`; trocar exige reiniciar (`theme-builtin.patch`).
   - decisões do dono (12/10/2026):
     - troca com reinício: modal "reiniciar agora" ou "depois".
     - o seletor lista todos os temas do repositório local de temas (uma pasta de temas dentro do navegador), não só os dois embutidos.
     - ícones fora da v0.2: um tema escolhe um dos pacotes compilados (`default`, `pixelized`). Depois: cerca de 5 pacotes de ícones bem diferentes, compilados, e o tema declara um pacote-base com overrides por ícone vindos de outros pacotes (ex.: base x, ícones 12 e 14 de y, 34 e 35 de z). Sem ícones como dado nem parser em runtime.
     - distribuição: tema empacotado em arquivo `.aerotheme` (decisão do dono, 12/10/2026). O arquivo tem ícone do aerographene e associação de tipo no sistema (MIME + desktop entry); abrir o arquivo dispara um diálogo portátil de importação, mesmo com o navegador fechado (ex.: `aerographene --import-theme=<arquivo>`). Substitui "só `theme.json` na v0.2".
     - repositório de temas global, `~/.config/aerographene/themes/<nome>/`, visto por todos os spaces. Pasta e pref pelo nome do tema, não por id.
     - nomes de ícone (para os pacotes futuros): camelCase, com numeração onde houver variantes. Ex.: `back`, `backArrow`, `backArrow1`, `backArrow2`.
     - formato: `"icons": {"base": "<pacote>"}` desde a v0.2, para aceitar `"overrides": {"<ícone>": "<pacote>"}` depois sem quebrar temas existentes.
     - desejável: importar tema arrastando um arquivo para um modal de importar tema, ou instalar via extensões. Viabilidade a investigar.
   - verificação: compilar só o alvo afetado no runner; smoke no pacote nos 4 combos.
4. teste de uso real: roteiro em `docs/TESTE-USO-REAL.md`; execução do dono, com clique e teclado. Falhas viram entrada em `docs/NOITE-*.md`.

## ordem

1. teste de uso real começa já sobre o pacote v0.1.0, em paralelo.
2. seletor de tema.
3. v0.2 fecha com pacote novo, smoke, roteiro sem falha bloqueante e baseline sem regressão >2% contra o Helium.

## a conferir no desenho

- nome como chave de pasta (decidido 12/10): o nome do `theme.json` vira a pasta como está, aceitando espaço e acento; rejeita vazio, `/`, `\`, `.`/`..`, início com `.`, caracteres de controle e mais de 64 bytes. Comparação de conflito sem diferenciar caixa. `default` e `pixelized` são reservados.
- conflito na importação (decidido 12/10): o diálogo pergunta substituir ou cancelar; sem renomear automático.
- `.aerotheme` (decidido 12/10): zip com `theme.json` na raiz e nada mais na v0.2; lido com `third_party/zlib/google/zip` (a confirmar na árvore 154 pela fatia).
- associação de tipo: entra no PKGBUILD (`packaging/arch/`); o `.tar.zst` avulso não registra MIME sozinho.
- diálogo portátil sem o navegador aberto: janela mínima, sem abrir perfil ou sessão; custo de abertura a medir.

## não verificado

- atribuição do PSS +9,6% contra o ungoogled.
