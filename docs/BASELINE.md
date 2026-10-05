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

Referência do aerographene: ungoogled (a base). Meta: nada pior que +2% sobre a base; alvo: passar Thorium e Helium.

## limites

- Thorium com 10 abas tem variância alta; mediana de `all_ms` não é confiável.
- Sem drop de page cache (exige root), sem Speedometer, sem controle de temperatura/throttling.
- Dados brutos: `bench/out/results-20261005-002939.jsonl`, `-003912.jsonl`, `-004351.jsonl` (fora do git).
