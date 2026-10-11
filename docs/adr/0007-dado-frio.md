# Dado frio em banco separado, sem compressão, nunca apagado

Status: aceito em 11/10/2026 (proposto em 10/10/2026; plano revisto com o dono em 11/10/2026). Nada implementado.

Histórico, favicons, registros de downloads e sessões antigas sem uso há mais que o prazo de frio (padrão 30 dias, pref `aerographene.cold_after_days`) saem do banco quente e vão para um banco SQLite por perfil, `History-Cold`, sem compressão. O objetivo é manter o `History` quente pequeno (abertura, `InMemoryURLIndex`, omnibox), não economizar disco. O `ExpireHistoryBackend` do Chromium (que apaga visitas com mais de 90 dias, `kExpireDaysThreshold` em `components/history/core/browser/history_backend.h`) passa a mover em vez de apagar; só a exclusão pedida pelo usuário apaga.

Cada URL existe num lugar só. Ao revisitar uma URL que está no frio, a linha de `urls` dela sai do frio e volta ao quente com a visita nova (contagens preservadas); as visitas antigas ficam no frio. Não há outra reidratação.

O cache de sites não vai para o frio: entradas com mais de 30 dias são apagadas. Cookies nunca esfriam.

Alternativas descartadas: a expiração do Chromium (apaga; rejeitada pelo dono em 06/10/2026); comprimir o histórico (texto curto, ganho nulo; decisão do dono em 11/10/2026); zstd no cache HTTP (conteúdo já chega comprimido; substituído por apagar o antigo); prazo de 10–15 dias (tiraria do autocomplete do omnibox sites visitados há poucas semanas); teto de disco (sem compressão nem cache, o volume esperado não justifica).

## decisões do dono (11/10/2026)

- prazo de frio: 30 dias, o mesmo do cache.
- omnibox não sugere dado frio.
- "limpar histórico" apaga também o frio.
- `chrome://history` mostra o quente; uma seção "30+ dias" no fim da lista consulta o frio sob demanda. A busca de texto também cai no frio nessa seção.
- sem compressão, sem teto de disco e sem aviso de tamanho.
- cache de sites: apagar entradas com mais de 30 dias.
- cookies fora do frio.

Revogado por este texto: prazo de 45 dias, compressão zstd por linha, catálogo FTS5, sessões em `.zst`, fatia `cold-data-compress`, a frase "mover sem comprimir viola a definição de dado frio" (o `CONTEXT.md` foi ajustado).

## fatias

1. `cold-data-store`: `ColdHistoryDatabase` (schema igual ao das tabelas movidas, abertura sob demanda, recovery isolado) e a pref; sem efeito no produto.
2. `cold-data-history-move`: o expirer usa o prazo de frio e move `urls`/`visits`/`keyword_search_terms` em transação (copia, confirma, apaga do quente).
3. `cold-data-history-revisit`: visita a URL que está no frio move a linha de `urls` de volta ao quente, sem duplicata.
4. `cold-data-history-ui`: seção "30+ dias" em `chrome://history`, consulta e busca no frio; "limpar histórico" apaga o frio.
5. `cold-data-cache-expire`: apagar entradas do cache de sites com mais de 30 dias.
6. `cold-data-favicons`, 7. `cold-data-downloads`, 8. `cold-data-sessions` (conferir conflito com `lazy-session-restore` e se o Chromium já limita as gerações de sessão).

Cada fatia compila `components/history` (ou o alvo afetado) no runner antes de build completa; o runner não compila unit tests, então a checagem de comportamento é por QA em pacote com perfil envelhecido. Medição: harness com perfil envelhecido e frio ativo; regra de 2% contra o Helium.

## pendente de conferir no código (Chromium 154)

- corte de idade do índice do omnibox (`URLIndexPrivateData`): define quanto o frio realmente alivia a abertura.
- onde aplicar a idade máxima no cache (`disk_cache` simple backend) sem patch invasivo.

## verificado no código (Chromium 154, 11/10/2026)

- favicons: `ExpireHistoryBackend::DeleteOneURL`/`DeleteIcons` apagam os mapeamentos da URL que sai do quente e `DeleteFaviconsIfPossible` apaga os ícones sem mapeamento; `ClearOldOnDemandFaviconsIfPossible` (30 dias) só liga em Android/iOS (`kClearOldOnDemandFaviconsEnabled`). Fatia 6 em `cold-data-favicons-downloads`.
- miniaturas: não há dado persistente. `top_sites` (`top_sites_database.cc`) guarda só `url`, `url_rank`, `title`; `chrome/browser/ui/thumbnails/` não grava em disco. Sem código.
- downloads: a tabela `downloads` do `History` não expira por idade; a limpeza de 90 dias de `components/download/internal/common/download_utils.cc` vale só para entradas em andamento/interrompidas do banco de downloads em progresso. Fatia 7 em `cold-data-favicons-downloads`.
- sessões: `CommandStorageBackend` (`components/sessions/core/command_storage_backend.cc`) mantém por tipo (`Session_*`, `Tabs_*`) só o arquivo atual e o último: `DeleteLastSessionFiles` apaga no início os demais e `MoveCurrentSessionToLastSession` apaga o último anterior. Não há sessões antigas acumuladas para esfriar; `lazy-session-restore` não toca esse arquivo. Fatia 8 sem código.

## Consequences

- O banco frio abre sob demanda e o movimento roda no task runner de background do backend de histórico: nada no caminho de abertura.
- Disco do frio cresce sem limite, aceito pelo dono.
- Sites visitados há mais de 30 dias não aparecem no autocomplete até serem revisitados.
- Patches concentrados em `components/history/core/browser/`, expostos a mudanças do upstream no expirer.
- Corrupção do frio fica isolada; o histórico quente não é afetado.
