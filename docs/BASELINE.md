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
