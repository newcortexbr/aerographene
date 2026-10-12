# plano da v0.2

Estado em 12/10/2026. Fontes: README (roadmap), `docs/SCOPE.md`, `docs/NOITE-20261012.md`, ADR 0007.

## itens

1. páginas internas seguem o tema: feito (PR #41); falta aprovação visual do dono (não há mockup).
2. seletor de tema na UI: não iniciado.
   - entrega: escolha entre default e pixelized na página de configurações, aplicada na hora e guardada em pref. Cada tema define o próprio esquema (sem alternância claro/escuro).
   - ver `docs/wiki/temas.md` para o carregamento de temas. Em aberto: listar temas de extensão no seletor.
   - verificação: compilar só o alvo afetado no runner; smoke no pacote nos 4 combos.
3. dado frio do storage de sites: não iniciado, falta ADR.
   - o ADR 0007 já entregou histórico, favicons, downloads, sessões e o cache de sites (apagado após 30 dias, não esfriado). Cookies nunca esfriam.
   - o que resta é o storage do site (localStorage, IndexedDB, Cache Storage, service workers), com reidratação na navegação e exceções de frio (contas Google, Proton, Microsoft etc.). Origem: decisões do dono de 04 a 06/10/2026 e `docs/SCOPE.md` (v0.2).
   - o ADR 0007 não cobre isso: reduziu a reidratação ao caso da revisita de histórico. Antes de codar, abrir o ADR 0010 com: prazo (30 dias, igual ao frio), onde guardar, como reidratar sem atrasar a navegação, exceções, iframes/service workers/sync.
   - verificação: perfil envelhecido; regra de 2% contra o Helium.
4. teste de uso real: roteiro pronto em `docs/TESTE-USO-REAL.md`; execução é do dono, com clique e teclado.
   - gate de release: nenhum item do roteiro em falha bloqueante; falhas viram entrada em `docs/NOITE-*.md`.

## ordem

1. teste de uso real começa já sobre o pacote v0.1.0 (não depende de código novo) e corre em paralelo.
2. seletor de tema (pequeno, só UI).
3. ADR 0010 e depois as fatias do dado frio de storage.
4. v0.2 fecha com pacote novo, smoke, roteiro sem falha bloqueante e baseline sem regressão >2% contra o Helium.

## não verificado

- se o ADR 0007 já está em build/pacote publicado: a v0.1.0 é de `d83fc39`; conferir se esse commit inclui as fatias de cold-data.
- atribuição do PSS +9,6% contra o ungoogled.
