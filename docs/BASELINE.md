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

## rodada final de 10/10/2026 (aero 7fa451f, PGO; Comet Lake na tomada, perfil performance, load1 < 1,0 antes de cada chamada)

Ordem intercalada: uma chamada do harness por navegador por volta, ordem invertida a cada volta, 6 voltas por bloco; 54 chamadas sem falha. Medianas; razão pareada = mediana das razões por volta. Versões: aero 154.0.8037.97 (0.1.0), Helium 0.18.3.1, ungoogled 154.0.8037.97. Dados em `bench/out/results-20261010-11*.jsonl` e `-12*.jsonl` (fora do git).

| medição | aero | Helium | ungoogled | aero vs Helium (pareada) | aero vs ungoogled (pareada) |
|---|---|---|---|---|---|
| warm first_ms (n=12) | 475,2 | 432,0 | 516,4 | +10,0% (+8,8%) | -8,0% (-8,3%) |
| first, perfil novo (n=6) | 497,5 | 506,1 | 535,0 | -1,7% (-3,0%) | -7,0% (-6,8%) |
| 10 abas all_ms (n=12) | 864,2 | 852,9 | 1052,2 | +1,3% (+1,2%) | -17,9% (-17,7%) |
| 10 abas PSS MiB (n=12) | 639,6 | 662,4 | 637,8 | -3,4% (-1,2%) | +0,3% (+4,7%) |
| 10 abas processos | 19 | 19 | 19 | 0 | 0 |

- warm contra o Helium encosta na regra fixa de 10% (meta 2%), mas o IQR do Helium foi 90,5 ms (aero 29,5) e a rodada de 83dde84 (mesmo dia, bateria) deu -4,1%: tratar como sinal a investigar, não regressão confirmada.
- layout vertical (`helium.browser.layout` = 2), warm, aero vs Helium, 8 repetições intercaladas: 488,9 vs 480,4 ms, +1,8% (pareada +1,5%); sem crash. Layout confirmado por captura nos dois (`bench/out/vertical/confirm-*.png`). Medição com script próprio que importa o harness; dados em `bench/out/vertical/results-20261010-122653.jsonl`.
- confirmação do warm (10/10, 13:52–14:04, mesmas condições, só aero e Helium, 10 voltas intercaladas, n=20 cada): aero 489,4 ms (IQR 35,5) vs Helium 485,1 ms (IQR 89,7), +0,9% (pareada +1,0%; aero abaixo em 3 de 10 voltas). Combinada com a rodada acima (n=32 cada): +3,5%. O +10% não se reproduziu; a dispersão vem do Helium. Sem regressão acima da regra fixa de 10%; contra a meta de 2% o resultado é inconclusivo. Dados: `/tmp/bench7w.manifest` aponta os `bench/out/results-20261010-135*`/`-140*.jsonl`.

## pinned no startup (11/10/2026, Comet Lake na tomada, perfil performance, load1 < 1,0)

Perfil com 6 pinned (3 `open=1`, 3 fechadas, span 2, gaveta), mesmo modelo para os dois pacotes (`pinned_tabs` zerado), 12 voltas intercaladas. Script e dados em `bench/out/qa-defer/` (fora do git).

- 1fa0bdf (reabrir pinned de fundo adiado, `perf-pinned-reopen-deferred`) vs 4abf68a: tempo até a pinned ativa ter título 561,6 vs 597,5 ms, pareada -5,8% (12/12 voltas a favor); PSS aos 5 s 405,4 vs 419,4 MiB, pareada -5,7%; 10 vs 12 processos.
- 783ee4d (`perf-pinned-nocopy`) vs 859390d em perfil limpo (n=12, bateria): nenhuma métrica pior que 2% com evidência; abertura warm +0,8% dentro do ruído.
- `perf-pinned-batch` (4abf68a): neutro no comportamento; a aparente diferença de 10 s vinha de perfis-modelo diferentes (pref `pinned_tabs`) e de timeout do script, não do patch.
- comportamento: no startup só a pinned ativa carrega; as de fundo carregam ao ativar (~30 ms até o request), como o `AddDeferredPinnedStartupTab` do Helium.
