# linha de base (05/10/2026, Comet Lake i3-10110U, perfil performance)

Harness: `bench/harness.py`. Estado de energia: `power_profile=performance`, governor `powersave` + EPP `performance` (intel_pstate ativo). Tomada não detectada pelo harness (`on_ac=null`). Versões: Helium 0.18.3.1, ungoogled 154.0.8037.97-1, Thorium 154.0.8037.45 AVX2, Zen 1.22.3b. Valores são medianas.

## abertura, perfil já criado (warm, n=10)

| navegador | first_ms |
|---|---|
| thorium | 436,4 |
| helium | 469,1 |
| ungoogled | 528,6 |
| zen | 1708,4 |

## abertura, perfil novo (first, n=5)

| navegador | first_ms |
|---|---|
| thorium | 524,5 |
| helium | 610,5 |
| ungoogled | 633,1 |
| zen | 4961,0 |

## 10 abas sintéticas (n=5)

| navegador | all_ms | PSS MiB | procs |
|---|---|---|---|
| helium | 1367,7 | 638,1 | 19 |
| ungoogled | 1696,5 | 633,8 | 19 |
| zen | 4272,4 | 648,8 | 21 |
| thorium | 6674,7 (instável: 1393–9266) | 636,1 | 19 |

Referência do aerographene (revisada em 08/10/2026 pelo dono, substitui "ungoogled é a base"): Helium. Meta: nada pior que +2% sobre o Helium medido na mesma rodada, com ordem intercalada; alvo: passar Helium e Thorium. O ungoogled segue como piso informativo, não como regra: a diferença do aero e do Helium contra ele (cerca de +70 ms e +90 a +105 MiB no pacote 46f2308, n=12) vem de algo herdado do Helium, provavelmente o uBlock como componente, e não é cobrada. Descobrir por que Helium e ungoogled abrem mais rápido é objetivo desejável, sem cobrança.

Rodada de 08/10/2026 (aero 46f2308, n=12, máquina ociosa, ordem intercalada; `~/.cache/aero-bench/run-20261008/`, fora do git): aero 833 ms / 751 MiB / 19 procs; Helium 829 / 734 / 19; ungoogled 761 / 646 / 19.

## limites

- Thorium com 10 abas tem variância alta; mediana de `all_ms` não é confiável.
- Sem drop de page cache (exige root), sem Speedometer, sem controle de temperatura/throttling.
- Dados brutos: `bench/out/results-20261005-002939.jsonl`, `-003912.jsonl`, `-004351.jsonl` (fora do git).

## rodada de 10/10/2026 (aero 83dde84 = 0.1.0, PGO; Comet Lake na bateria, perfil performance, load < 1)

Medianas. Mesmo estado de energia nos três navegadores; não comparar valores absolutos com 08/10 (outra condição e outro pacote). Dados em `bench/out/results-20261010-*.jsonl` (fora do git).

| medição | aero | Helium | ungoogled | aero vs Helium | aero vs ungoogled |
|---|---|---|---|---|---|
| warm first_ms (n=12, por blocos) | 479,5 | 499,8 | 521,0 | -4,1% | -8,0% |
| first, perfil novo (n=6, por blocos) | 502,4 | 517,4 | 548,0 | -2,9% | -8,3% |
| 10 abas all_ms (n=16, intercalado) | 877,5 | 900,9 | 1050,7 | -2,6% | -16,5% |
| 10 abas PSS MiB (n=16, intercalado) | 677,0 | 661,1 | 635,3 | +2,4% | +6,6% |

A rodada de 10 abas por blocos (n=6) deu +2,1% em all_ms contra o Helium; repetida com ordem intercalada (8 voltas alternando a ordem, uma chamada do harness por navegador) virou -2,6% (razão pareada mediana 0,975, aero abaixo em 7 de 8 voltas): sem regressão. Diferenças de PSS ficam dentro do IQR (~80 MiB). O harness itera por blocos; intercalar exige chamá-lo uma vez por navegador.
