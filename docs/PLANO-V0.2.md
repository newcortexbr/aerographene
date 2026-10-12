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
     - desejável: importar tema arrastando um arquivo para um modal de importar tema, ou instalar via extensões. Viabilidade a investigar.
   - verificação: compilar só o alvo afetado no runner; smoke no pacote nos 4 combos.
4. teste de uso real: roteiro em `docs/TESTE-USO-REAL.md`; execução do dono, com clique e teclado. Falhas viram entrada em `docs/NOITE-*.md`.

## ordem

1. teste de uso real começa já sobre o pacote v0.1.0, em paralelo.
2. seletor de tema.
3. v0.2 fecha com pacote novo, smoke, roteiro sem falha bloqueante e baseline sem regressão >2% contra o Helium.

## não verificado

- se a v0.1.0 (`d83fc39`) inclui as fatias de cold-data.
- atribuição do PSS +9,6% contra o ungoogled.
