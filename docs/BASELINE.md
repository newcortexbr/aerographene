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

## rodada de 11/10/2026 (aero b1a7fed, Comet Lake na tomada, perfil performance, load1 < 1,0; rotação entre os 3 navegadores)

Dados em `bench/out/qa-layout/bench/` (fora do git). Medianas; razão pareada por volta.

- warm first_ms (n=12): aero 494,4, Helium 429,0 (IQR 415,7–499,4, bimodal), ungoogled 536,0. Vs Helium +3,7% (aero abaixo em 5/12); vs ungoogled -7,6%.
- perfil novo (n=6): aero 519,1, Helium 533,3, ungoogled 555,2. Vs Helium -2,5%; vs ungoogled -6,3%.
- 10 abas all_ms (n=12): aero 907,2, Helium 926,1, ungoogled 1087,2. Vs Helium -2,6%; vs ungoogled -18,4%.
- 10 abas PSS (n=12): aero 719,1, Helium 728,4, ungoogled 655,2 MiB. Vs Helium -1,2%; vs ungoogled +9,6%.
- trace de startup (n=5, b1a7fed vs 8f7d5fa): `perf-startup-layout` reduziu pouco as passadas de layout (LayoutImmediately 1611 vs 1687, ToolbarView 9 vs 10); o excesso contra o Helium (~1118) continua. Desligar o omnibox centralizado baixa para ~1481.
- leitura: warm contra o Helium segue inconclusivo e oscila entre rodadas (-4%, +10%, +0,9%, +3,7%); o Helium tem dois modos (~410 e ~490 ms) e o aero fica quase sempre no superior. Entender o modo rápido é a próxima pista.

## bimodal da abertura warm (11/10/2026)

- causa observada (traces `bench/out/trace-startup/`, 14 de 14): a execução é lenta (~+80 ms) quando o renderer pede `/favicon.ico` antes do beacon `/ready`; o fetch do beacon fica ~80 ms parado antes de chegar ao serviço de rede. Pré-BrowserMain, GPU, renderer e DOMContentLoaded são iguais nos dois modos. Acontece igual em aero e Helium; não é do produto. Mecanismo interno no serviço de rede não identificado.
- página com favicon `data:` não remove o bimodal (`bench/out/bimodal/`, 40 execuções); fração rápida 20–30% nos dois navegadores nessa rodada.
- por modo, juntando os dados de 10 e 11/10 (pacotes e condições misturados, n=165 aero, 160 Helium): rápido 405,8 vs 405,0 ms; lento 490,9 vs 499,6 ms. A diferença nas medianas vem da proporção de execuções rápidas em cada rodada, não de abertura mais lenta.
- consequência: com n=12 a mediana warm é loteria entre os modos. Comparar por modo ou com n>=30; o harness também não registra AC nesta máquina (`on_ac` procura `AC`/`ACAD`, a fonte é `ADP1`). Mudanças no harness ficam para o dono (`bench/harness.py` não é editado por agentes).
- correção (11/10): o perfil warm do aero em `bench/out/trace-startup/` estava com `profile.exit_type=Crashed` (artefato do `collect.py`), então os traces do aero incluem o balão "Restore pages?" (widget extra, RootView/ImageButton a mais). Parte do excesso de layout atribuído ao aero contra o Helium vem disso. Com SIGTERM normal, aero, Helium e ungoogled gravam `SessionEnded` (`bench/out/exittype/`, 3 de 3 cada). Traces futuros precisam conferir `exit_type` antes de cada execução.
- trace sem balão (`bench/out/trace-clean/`, n=7, exit_type conferido, 1 `Widget::Init` em todas): aero b1a7fed 1628 LayoutImmediately / 148,6 ms; com omnibox centralizado desligado 1547 / 120,1 ms; Helium 1128 / 81,5 ms. FCP aero 587,5 vs Helium 661,3 ms; first_ms 450,4 vs 459,4. Os perfis usam o layout padrão de cada navegador (aero vertical, Helium sem a pref), então parte do excesso de layout vem da sidebar vertical; ele não aparece no caminho crítico (FCP e beacon não pioram). Comparação vertical contra vertical fica na medição de 10/10 (+1,8%).

## otimizações descartadas (2026-10-11)

- pasta raiz de pinned sob demanda (`EnsureRoot` só no primeiro pin): descartada pelo dono. Ganho só para perfil que nunca fixa aba (um nó e uma gravação no primeiro startup), abaixo do ruído. Risco: `PinnedModel::IsLoaded()` depende de `root_`, o que afetaria `OnPinnedModelLoaded`/`AdoptStartupTabs` (#4), exigiria null checks em barra, menu e `RefreshClosedPinned` e abriria janela para raiz duplicada via sync.
- leitura assíncrona do `theme.json`: descartada pelo dono. Leitura síncrona de arquivo pequeno, abaixo do ruído no warm; disco frio não medido. Risco: flash do tema padrão no primeiro frame ou, para evitá-lo, segurar o paint (ganho zero) e corrida com troca de tema. Reconsiderar só com medição em disco frio mostrando custo real.

# linha de base v0.1 (12/10/2026, aerographene d83fc39)

Harness: `bench/harness.py`, copiado de `/home/dasher/projects/browser` (working tree, sem edição) para `/tmp/bench01`, com o binário aerographene apontado para o pacote `pkg-d83fc39` (`0.1.0-154.0.8037.97-1-d83fc39-x86_64_linux`). Versões: aerographene d83fc39 (Chromium 154.0.8037.97), Helium 0.18.3.1, ungoogled 154.0.8037.97-1. Máquina: Comet Lake i3-10110U. Energia: `power_profile=performance`, governor `powersave`, EPP `performance`; `on_ac` não detectado.

Condições: cada uma das 30 rodadas por configuração começou com `load1 < 1.0` e sem processos de teste ativos (checagem por `/proc`, `fd`, `cwd`, `cmdline` e `SingletonLock`). A ordem dos três navegadores foi rotacionada a cada rodada (`aerographene, helium, ungoogled`; `helium, ungoogled, aerographene`; `ungoogled, aerographene, helium`). Cada chamada do harness fez uma rodada com `--repeat 1`, então n=30 é por navegador e por configuração. `loaded` foi completo em todas as execuções (1 ou 10 de 10).

Pacote de dados: `/tmp/bench01-out` (fora do git).

## abertura, perfil já criado (warm, n=30, ms)

| navegador | first_ms mediana | p10 | p90 | delta vs helium | delta vs ungoogled |
|---|---|---|---|---|---|
| aerographene | 474,1 | 391,7 | 502,6 | -3,3% | -10,8% |
| helium | 490,1 | 404,4 | 507,5 | - | -7,8% |
| ungoogled | 531,6 | 514,8 | 546,2 | +8,5% | - |

## abertura, perfil novo (first, n=30, ms)

| navegador | first_ms mediana | p10 | p90 | delta vs helium | delta vs ungoogled |
|---|---|---|---|---|---|
| aerographene | 506,4 | 499,4 | 534,4 | -3,1% | -8,6% |
| helium | 522,7 | 504,8 | 547,1 | - | -5,6% |
| ungoogled | 554,1 | 542,1 | 572,1 | +6,0% | - |

## 10 abas sintéticas (warm, n=30)

| navegador | first_ms mediana | all_ms mediana | all_ms p10 | all_ms p90 | PSS MiB mediana | PSS p10 | PSS p90 | procs |
|---|---|---|---|---|---|---|---|---|
| aerographene | 743,9 | 877,5 | 798,9 | 902,6 | 725,0 | 722,0 | 726,4 | 19 |
| helium | 787,9 | 912,3 | 818,8 | 973,7 | 736,6 | 729,4 | 739,5 | 19 |
| ungoogled | 728,2 | 1073,0 | 1039,2 | 1173,0 | 661,5 | 659,6 | 663,1 | 19 |

Deltas do aerographene: `all_ms` -3,8% vs helium e -18,2% vs ungoogled; `PSS` -1,6% vs helium e +9,6% vs ungoogled; `first_ms` -5,6% vs helium e +2,2% vs ungoogled.

## regra do produto

Regra: aerographene não piora mais de 10% vs Helium (meta: 2%). Resultado nesta rodada: nenhuma métrica medida piora vs Helium (todas os deltas ficam entre -1,6% e -5,6%). Vs ungoogled (piso informativo, não regra): o PSS fica +9,6%, abaixo do limite de 10%, mas acima da meta de 2%; isso fica registrado como ponto de atenção, a ser atribuído (ver limites).

## limites

- "perfil novo" aqui é `first` (perfil recriado a cada execução), não disco frio: sem `--drop-caches` (exige sudo, não disponível sem senha).
- PSS com 10 abas só em modo warm; não foi medido em modo first.
- Speedometer não está automatizado.
- Idle de input não tem fonte confiável nesta máquina (`GetSessionIdleTime` do KWin retorna NotSupported); a condição de "sem uso" foi load1 < 1.0 mais ausência de processos de teste, não idle de input.
- Medições feitas em janelas de baixa carga após uma espera de cerca de 3h para o portão; houve rodadas com load até 0,98 e pausas longas entre execuções. Não controlado: temperatura e throttling.
- Os dados de Helium e ungoogled desta rodada não são comparáveis diretamente à rodada de 08/10 (`46f2308`), que usou outro pacote.

# linha de base v0.2 (13/10/2026, aerographene 3bb3c2f, build 38293664167)

Máquina: Comet Lake i3-10110U, ociosa (load1 0,5 a 0,9 no início, gate load1 < 1,0 antes de cada chamada, 0 esperas estouradas, 0 falhas), nenhum outro navegador aberto. Início 00:51, fim 02:32 de 13/10. Energia: `power_profile=performance` (confirmado com `powerprofilesctl get`), governor `powersave`, EPP `performance`; `on_ac` não detectado pelo harness (a fonte é `ADP1`, em 1). Sem comparação com medições do Cezanne.

Uma primeira rodada (00:29 a 00:48) foi descartada: o Zen estava aberto na máquina. Tudo abaixo é da rodada limpa; a contaminada fica em `/tmp/bench02b-out.contaminado` (fora do git).

Versões: aerographene 154.0.8037.97 (pacote `...-3bb3c2f`), Helium 0.18.3.1, Thorium 154.0.8037.45 AVX2, ungoogled 154.0.8037.97-1, Google Chrome 155.0.8059.39 estável (o Chromium oficial não tem build estável para Linux; o `.deb` foi extraído em `/tmp/chrome-off/x`, sem instalar). O Chrome é uma versão acima das demais.

Comandos (harness `bench/harness.py` sem edição; orquestração em `bench/ab.py`, resumo e gráficos em `bench/charts.py`):

```bash
python3 bench/ab.py --browsers aerographene,helium,thorium,chrome,ungoogled --bin aerographene=<pacote>/chrome \
  --bin chrome=<chrome>/opt/google/chrome/chrome --out /tmp/bench02b-out --block warm --laps 10      # 2 execuções por chamada
python3 bench/ab.py ... --block tabs --laps 10     # 10 abas, 2 execuções por chamada
python3 bench/ab.py ... --block first --laps 6 --repeat 1
python3 bench/charts.py --data /tmp/bench02b-out --json docs/img/bench/v02.json --out docs/img/bench \
  --title "aerographene v0.2" --note "..."
```

Ordem: uma chamada do harness por navegador por volta, ordem rotacionada a cada volta (5 navegadores). warm e tabs: 10 voltas, n=20 por navegador; first: 6 voltas, n=6. Razão pareada = mediana das razões das medianas por volta contra o Helium. IC95 = bootstrap percentil da mediana (2000 reamostragens). Dados resumidos em `docs/img/bench/v02.json`; os `results-*.jsonl` brutos ficam fora do git.

| medição | aero | Helium | Thorium | Chrome 155 | ungoogled | aero vs Helium (pareada) | aero IC95 |
|---|---|---|---|---|---|---|---|
| warm first_ms | 476,4 | 484,9 | 435,9 | 496,3 | 523,4 | -1,7% (+0,2%; abaixo em 5/10) | 465,8–482,5 |
| perfil novo first_ms (n=6) | 494,4 | 506,5 | 460,1 | 542,5 | 543,5 | -2,4% (-1,7%; 6/6) | 488,1–518,9 |
| 10 abas all_ms | 875,2 | 898,0 | 837,2 | 912,5 | 1044,3 | -2,5% (-3,0%; 7/10) | 863,4–886,7 |
| 10 abas PSS MiB | 635,3 | 662,0 | 627,5 | 686,7 | 634,6 | -4,0% (-2,0%; 9/10) | 628,8–712,4 |

Processos com 10 abas: 19 em todos os Chromium testados (aero, Helium, ungoogled).

## regra do produto

Nenhuma métrica do aerographene fica mais de 2% pior que o Helium (maior valor: +0,2% pareado em warm, dentro do ruído; IC95 do aero e do Helium se sobrepõem em warm). Meta "passar também o Thorium": não atingida em abertura (Thorium 8 a 9% mais rápido em warm e perfil novo, 6,8% em all_ms) nem em memória (-1,2% contra o aero, dentro do IC). Thorium ficou estável nesta rodada (all_ms IQR 800,8–863,9), ao contrário de 05/10.

## PSS: o +9,6% contra o ungoogled

A mediana de PSS com 10 abas é bimodal em aero e Helium, não no ungoogled (IQR 632,0–637,5). A posição da execução dentro da chamada explica: a primeira execução depois da criação do perfil (`i=0`) é alta; a segunda, no mesmo perfil (`i=1`), é baixa.

| navegador | PSS i=0 | PSS i=1 |
|---|---|---|
| aerographene | 712,7 | 622,0 |
| Helium | 722,5 | 644,0 |
| ungoogled | 637,5 | 632,0 |
| Thorium | 628,7 | 618,5 |
| Chrome 155 | 688,5 | 685,2 |

- Em `i=0` o aero fica +11,8% sobre o ungoogled (o +9,6% da v0.1 se reproduz); em `i=1`, -1,6%. O Helium tem o mesmo padrão, então o excedente vem do que ele e o aero compartilham.
- PSS por processo (`bench/pss_proc.py`, uma execução em perfil novo, 19 processos cada, PSS MiB): aero 712,3 vs ungoogled 638,7 (+73,6). Processo do navegador: 118,2 vs 156,2 (-38,0; menos arquivo mapeado, 63,6 vs 97,4). Dois renderers a mais pesados no aero: um com 150,3 (anon 129,7) e outro com 44,3, contra 46,4 + 46,4 no ungoogled (+101,8 nos renderers de abas/páginas). GPU (59,7 vs 59,3), rede (30,0 vs 32,5 utilitário) e os 10 renderers de aba (~29,6 vs 28,4) são equivalentes.
- Hipótese (não verificada): o renderer de 150 MiB é o contexto do uBlock Origin built-in (filtros carregados na criação do perfil), que o ungoogled não tem; some nas execuções seguintes do mesmo perfil, mas só se confirma identificando o processo (URL/tipo via CDP). Concorda com a nota de 08/10 (excesso herdado do Helium, provavelmente uBlock). Não é corrigido aqui.
- Na prática: em perfil já usado a memória do aero é igual à do ungoogled (-1,6%) e menor que a do Helium (-3,4%); em perfil recém-criado é +11,8% sobre o ungoogled e -1,4% sobre o Helium.

## limites

- Mediana de PSS agrega as duas posições; o gráfico de memória mostra essa mediana (aero 635,3, mas IC95 de 628,8 a 712,4).
- A atribuição de PSS por processo é de uma execução por navegador; uma repetição (3 execuções, só pelo total) deu 713,0 / 721,8 / 637,6.
- Sem drop de page cache (exige sudo), Speedometer não automatizado, sem controle de temperatura/throttling; perfil novo não é disco frio.
- Chrome é 155; first (n=6) tem IC largo.
