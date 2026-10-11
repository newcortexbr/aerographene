# Dado frio em banco separado comprimido, nunca apagado (proposto)

Status: proposto em 10/10/2026, aguardando o dono. Nada implementado.

Histórico, favicons, registros de downloads e sessões antigas sem uso há mais que o prazo de frio (padrão 45 dias, pref `aerographene.cold_after_days`) saem do banco quente e vão para um banco SQLite por perfil, `History-Cold`, com compressão zstd por linha nas colunas de texto/blob e um catálogo FTS5 de URL e título. Sessões antigas viram arquivos `.zst` registrados no mesmo catálogo. O `ExpireHistoryBackend` do Chromium (que apaga visitas com mais de 90 dias, `kExpireDaysThreshold` em `components/history/core/browser/history_backend.h`) passa a mover em vez de apagar; só a exclusão pedida pelo usuário apaga. `chrome://history` consulta quente e frio; o omnibox, só o quente. Alternativas descartadas: a expiração do Chromium (apaga; rejeitada pelo dono em 06/10/2026); comprimir colunas no próprio `History` (schema e migrações, risco ao startup pelo `InMemoryURLIndex`, conflito contínuo com o upstream); arquivo morto puro com índice (busca e lookup de favicon ruins, perda de um bloco = um mês), aceito só para sessões; mover sem comprimir (viola a definição de dado frio no `CONTEXT.md`). Dados de sites ficam para a v1.1.

## Fatias

1. `cold-data-store`: `ColdHistoryDatabase` (schema, abertura preguiçosa, recovery) e a pref; sem efeito no produto.
2. `cold-data-history-move`: o expirer usa o prazo de frio e move `urls`/`visits`/`keyword_search_terms` em transação (copia, confirma, apaga do quente).
3. `cold-data-compress`: zstd por linha, nível baixo.
4. `cold-data-history-search`: busca de texto no `QueryHistory` cai no FTS do frio; rótulo na UI atual.
5. `cold-data-favicons`, 6. `cold-data-downloads`, 7. `cold-data-sessions` (arquivo `.zst` + catálogo; conferir conflito com `lazy-session-restore`).

Cada fatia compila `components/history` e roda os `history_unittests` afetados no runner antes de build completa. Medição: harness com perfil envelhecido e frio ativo; regra de 2% contra o Helium.

## Decisões do dono (11/10/2026)

- omnibox não sugere dado frio.
- "limpar histórico" apaga também o frio.
- sem reidratação do histórico: a visita nova cria linha quente; o frio só recebe dado com mais de 45 dias.
- teto de disco: pendente (ver discussão de compressão forte e teto de 1 GB).

## Decisões pendentes do dono (texto original)

- omnibox sugere dado frio? Proposta: não na v1.0 (startup e memória).
- "limpar histórico" apaga também o frio? Proposta: sim (privacidade).
- reidratação do histórico: proposta: não mover de volta; a visita nova já cria a linha quente. Reidratação fica para dados de sites (v1.1).
- teto de disco do frio? "Nunca apagar" implica crescimento sem limite.

## Consequences

- O banco frio abre sob demanda e o movimento roda no task runner de background do backend de histórico: nada no caminho de abertura.
- Disco do frio cresce sem limite enquanto não houver teto.
- Patches concentrados em `components/history/core/browser/`, expostos a mudanças do upstream no expirer.
- Corrupção do frio fica isolada; o histórico quente não é afetado.
- Não conferido no 154: expiração de downloads por idade, número de gerações de sessão, ponto de remoção de favicons órfãos.
