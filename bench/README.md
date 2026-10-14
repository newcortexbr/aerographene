# bench

Linha de base de desempenho do aerographene (item 1 de `docs/SCOPE.md`). Regra: nenhuma mudança piora mais de 2% o que está medido aqui.

## uso

```bash
bench/fetch-browsers.sh                     # baixa ungoogled, helium e thorium (AVX2) em bench/browsers/
python3 bench/harness.py --repeat 10        # abertura, perfil já criado ("warm")
python3 bench/harness.py --mode first       # abertura com perfil novo a cada vez
python3 bench/harness.py --tabs 10 --repeat 5   # PSS total com 10 abas sintéticas
python3 bench/harness.py --quick --tabs 10   # rodada rápida do dia a dia (~3x mais rápida)
```

O harness aborta se o perfil de energia não for `performance` (`--require-profile ''` desliga). Cada linha do resultado grava perfil, governor, EPP e se está na tomada; só compare resultados com o mesmo estado. Não rode junto com build ou outra carga pesada (são só 4 threads).

Não rode no runner do Cezanne: é outra CPU (Ryzen 5600G, Ubuntu bare metal) e a máquina-alvo da medição é o Comet Lake.

Resultados em `bench/out/results-*.jsonl` (fora do git), com resumo pela mediana no fim.

## o que é medido

- `first_ms`: do `exec` do navegador até a primeira página carregar e pintar dois frames (beacon HTTP para o servidor local do harness).
- `all_ms`: até todas as N abas avisarem. `loaded` mostra quantas avisaram (navegadores que adiam abas em segundo plano carregam menos).
- `pss_mib`: soma do PSS de toda a árvore de processos, `--settle` segundos depois do último beacon (ou do timeout).
- `procs`: número de processos nessa árvore.

Páginas sintéticas em `pages/` (sem rede externa), para não medir a internet.

## limites conhecidos

- "cold" real exige limpar o page cache: `--drop-caches` usa `sudo -n`. Sem isso, `first` mede perfil novo, não disco frio.
- Speedometer 3.1: `bench/speedometer.py` (ver BASELINE).
- PSS conta só os descendentes do processo lançado.
- Zen é Gecko: é régua de comparação, não alvo de patch.
