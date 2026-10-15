# build

Fluxo do item 2 do `SCOPE.md`: ungoogled-chromium `154.0.8037.97-1` (Chromium 154.0.8037.97, o mesmo do Helium 0.18.3.1) pelo fluxo oficial do `ungoogled-chromium-portablelinux`, mais a série própria em `patches/series` e as flags do ADR 0003.

## arquivos

- `build/config.sh`: tag fixada do ungoogled/portablelinux e o alvo `-march`.
- `build/build.sh`: roda no host (runner). Requer só `git` e `docker`. Clona o portablelinux na tag (com o submódulo ungoogled), gera a imagem `chromium-builder:trixie-slim` do próprio portablelinux e a camada `aerographene-builder` (+ `zstd`, `patch`), e chama `build/inner.sh` no container.
- `build/inner.sh`: no container, usa as funções de `portablelinux/scripts/shared.sh`: download do tarball, pruning, patches ungoogled + portablelinux, série aerographene, `-march`, domain substitution, `args.gn`, toolchain, `gn gen`, `ninja chrome`, pacote `.tar.zst`.
- `build/flags.gn`: flags próprias, aplicadas por cima de `ungoogled-chromium/flags.gn` e `flags.linux.gn`; a última definição de cada chave vence.
- `.github/workflows/build.yml`: gatilhos `workflow_dispatch` e `push` em `main` com mudança em `build/**`, `patches/**` ou no workflow. Nunca `pull_request` (ADR 0004).

## estado das builds da v0.3.2 (15/10/2026)

- avx2: run 38671160082 sobre `82a7bf3` (branch `v0.3`), verde: a série completa compila e liga. Smoke test do pacote ainda não feito; nada foi usado no navegador.
- avx1: run 38672821734 em andamento.
- `o3=hot` e `o3=wide`: pausadas (seção -O3 abaixo).
- pendentes para fechar a v0.3.2: pre-release `v0.3.2` (workflow `release.yml`, gera draft; build não autoriza publicação) e merge da `v0.3` na `main`. Versão do produto ainda `0.3.0` em `config.sh` e no PKGBUILD.

## cache

Workdir fora do repo: `$AEROGRAPHENE_WORKDIR` (padrão `$HOME/aerographene-build`).

- `portablelinux/build/download_cache`: tarball do Chromium, baixado uma vez.
- `portablelinux/build/src`: árvore preparada, com stamps (`.downloaded.stamp`, `.patched.stamp`, `.domsub.stamp`, `.aero-patches.hash`). Ao contrário do `build.sh` do portablelinux, `out/` não é apagado: o ninja é incremental.
- se a série em `patches/` muda (hash do `series` + arquivos + `MARCH`), o re-patch é incremental: `.aero-applied/` guarda a série aplicada e o `BUILD.gn` pré-`-march`; o `inner.sh` desfaz o `fix_tool_downloading` do portablelinux (`unfix_tool_downloading`: o `sed` dele altera arquivos já substituídos e o revert do ungoogled confere CRC32), faz o revert da domain substitution (cache `portablelinux/build/domsub-cache.tar.gz`), restaura o `BUILD.gn`, aplica `patch -R` na série antiga em ordem inversa e aplica a nova. Arquivos afetados com conteúdo igual ao de antes voltam ao mtime antigo (o ninja não recompila). Patches ungoogled/portablelinux não são tocados.
- recriação completa (tarball em cache, `out/` preservado) só se: `patch -R` falha, falta `.aero-applied/` ou o cache de domsub (árvores anteriores a esta mudança: a primeira troca de série ainda recria), árvore parcial (sem `.aero-patches.hash`) ou `UC_TAG` diferente de `.aero-base`.
- ccache: `cc_wrapper="ccache"`, cache no host em `$AEROGRAPHENE_CCACHE_DIR` (padrão `$HOME/aerographene-ccache`, montado em `/ccache`), `max_size` `$AEROGRAPHENE_CCACHE_SIZE` (padrão `40G`), `base_dir` = src, `sloppiness=time_macros,include_file_mtime,include_file_ctime,pch_defines`, `compiler_check=%compiler% -v` (o clang re-baixado muda o mtime, não a versão). `ccache -s` no fim. Desligável com `AEROGRAPHENE_CCACHE=0`. Imagem `aerographene-builder:v2` (+ `ccache`). Riscos: só compilação C/C++ é cacheada (Rust, link e ThinLTO não); adicionar `cc_wrapper` muda as linhas de comando, então a primeira build com ele recompila tudo; perfil PGO e `-march` entram no hash, trocar o perfil invalida o cache; compatibilidade de `cc_wrapper` com `is_official_build` não confirmada (confirmar no `gn gen` e no hit rate).
- `portablelinux/build/pgo`: perfil PGO baixado.
- `dist/`: o `.tar.zst` da última execução.

Para forçar do zero: apagar `portablelinux/build/src`.

## decisões

- PGO: o ungoogled fixa `chrome_pgo_phase=0` no `flags.gn` porque o perfil é um binário do Google que não vem no tarball (o gclient hook o baixaria). Não está no `pruning.list` e o arquivo está acessível (`chrome/build/linux.pgo.txt` → `chrome-linux-8037-1790747267-…profdata`, HTTP 200 em `storage.googleapis.com/chromium-optimization-profiles/pgo_profiles/`, verificado em 05/10/2026). Então o build baixa o perfil oficial e usa `chrome_pgo_phase=2`; se o download falha, cai para `0`. Os patches do ungoogled deixam parte do perfil desatualizada (só gera avisos). Desligável com `AEROGRAPHENE_PGO=0` ou o input `pgo` do workflow.
- `-march=x86-64-v3`: o GN do Chromium 154 não tem arg de `-march` para x86 (só `arm_arch`) nem `extra_cflags`. O `inner.sh` acrescenta `-march=x86-64-v3` (cflags, asmflags, ldflags, para o LTO) e `-Ctarget-cpu=x86-64-v3` (Rust) à `config("compiler_cpu_abi")` de `build/config/compiler/BUILD.gn`, só em `current_cpu == "x64" && is_linux`. Isso vale também para as ferramentas do host, que rodam no Cezanne (v3). Candidato a virar patch em `patches/` quando o dono da série quiser.
- ThinLTO (`use_thin_lto`, `thin_lto_enable_optimizations`), ICF (`use_icf`), `symbol_level=0`, `is_official_build=true`; sem `-O3` global (só o seletivo opcional, seção abaixo).
- jobs: padrão `auto` = `nproc` dentro do container na hora da build (os runners dividem 5..12 CPUs dinamicamente); número explícito em `JOBS`/input `jobs` sobrepõe. O log mostra o valor e o `MemAvailable`. Sem teto por RAM, por decisão do dono: com ~13 GB e 12 jobs há risco de OOM (compilações pesadas e o link ThinLTO do `chrome`); se ocorrer, rodar com `jobs` menor.
- RAM (~14 GB): `concurrent_links` não pode ser definido com ThinLTO (assert do GN), o Chromium calcula pela RAM. O link do `chrome` com ThinLTO é o pico de memória; se estourar, o host tem zram de 7,8 GB (zstd) e `/swap.img` de 16 GB; se ainda estourar, limitar `--thinlto-jobs`.
- chaves Google (ADR 0006): lidas de secrets opcionais `GOOGLE_API_KEY`, `GOOGLE_DEFAULT_CLIENT_ID`, `GOOGLE_DEFAULT_CLIENT_SECRET`; ausentes, ficam os valores vazios do ungoogled. Não aparecem no log.
- labels do runner: `[self-hosted, linux, intense]`, suposição. A API de runners da org exige permissão de admin, então os labels exatos não foram confirmados.
- produto: o pacote se chama `aerographene-<AERO_VERSION>-<tag>-<sha>-x86_64_linux.tar.zst` (versão do produto de `build/config.sh`, tag ungoogled, SHA do repo) e tem um symlink `aerographene` → `chrome`. Ícones e nome do binário ficam para depois; versão e strings: seção "branding" abaixo.

## -O3 seletivo (opcional, desligado por padrão; ainda não medido)

Status em 15/10/2026: `wide` foi medido e rejeitado. Bench quick no Comet Lake, n=6, contra a build normal: `all_ms` +2,31% (pareada +1,65%), `first_ms` -0,97%, `pss` +0,19%. Inconclusivo (dentro do ruído, mas na direção errada e perto do limite de 2%); `wide` não entra na série. Próxima medição: n≥12, rodadas intercaladas (normal/-o3 alternadas). Os perfis novos abaixo ainda não foram compilados nem medidos. Um perfil só entra na série se vencer o teste (ganho acima do ruído, sem passar de 2% de piora na linha de base). Referência de comparação: a build normal da v0.3.2.

O quê: `AERO_O3=off|hot|wide|base|ui|skia|lto3|global` (input `o3` do workflow `build`, choice, padrão `off`). `build/o3.py` edita `BUILD.gn`/`.gni` a cada execução do `inner.sh` e desfaz os originais quando o perfil muda (guarda em `src/.aero-o3/`, um backup por arquivo; antes do revert da domain substitution, porque `base/BUILD.gn` está na lista dela). Valida todas as âncoras antes de escrever (âncora ausente ou duplicada aborta sem editar nada).

- `off`: build normal.
- `hot`: Blink `platform` e `platform/heap` (`third_party/blink/renderer/platform/BUILD.gn`, `.../heap/BUILD.gn`): troca `optimize_max` por `optimize_speed`.
- `wide`: `hot` + `base` (`base/BUILD.gn`, o alvo `base`). Rejeitado (ver status).
- `base`: só `base`.
- `ui`: `cc` (`cc/cc.gni`: `cc_add_configs` troca `optimize_max` por `optimize_speed`, vale para todo `cc_component`), mais `ui/gfx` (`component("gfx")`), `ui/views` (`component("views")`) e `chrome/browser/ui` (`static_library("ui")`). Esses três não têm `optimize_max` no Linux (o de `gfx` é só Android), então o `o3.py` insere `configs -= [default_optimization]; configs += [optimize_speed]` logo após a abertura do alvo; o revert devolve o arquivo original. `chrome/browser/ui` é grande: o mais caro em tempo de build.
- `skia`: componente `skia` em `skia/BUILD.gn` (bloco `if (!is_debug)` com `optimize_max`, troca por `optimize_speed`). Não toca `skcms` nem os `rust_*_ffi_cpp`.
- `lto3`: nenhum alvo muda de nível de compilação. Em `build/config/compiler/BUILD.gn`, `thinlto_optimize_max` passa de `lto_opt_level = 2` para `3` (`-Wl,--lto-O3`). Só afeta quem usa essa config: `chrome` (`chrome/BUILD.gn`), blink `heap` e `controller`, angle. O resto continua em `--lto-O0` (`thinlto_optimize_default`). Só tem efeito com `thin_lto_enable_optimizations` (= `is_official_build`, ligado no `out/Default`).
- `global`: em `build/config/compiler/BUILD.gn`, `default_optimization` passa a aplicar `optimize_speed` em vez de `optimize` (-O2 no Linux sem `optimize_for_size`), e `optimize_max` passa de `-O2` para `-O3`. Todo alvo não-V8 em -O3: a maior recompilação (tudo) e o maior risco de tamanho/regressão.

Validação do `o3.py` (15/10/2026, sem compilar): âncoras conferidas por leitura na árvore do Chromium 154 do runner (`~/aerographene-build/portablelinux/build/src`), e execução em cópia em `/tmp` do runner (originais de `base` e Blink vindos de `.aero-o3/`, porque a árvore ativa estava com `wide`). Os 8 perfis acharam todos os alvos, rodar duas vezes dá o mesmo resultado, trocar de perfil e `--restore`/`off` devolvem os arquivos byte a byte, perfil inválido aborta. Isso prova só a edição dos arquivos; que o GN aceita e que o código compila fica para a primeira build de cada perfil.

Por que esses e não o V8: o V8 já compila com -O3 no upstream (`v8/gni/v8.gni:412` aplica `optimize_speed` a todos os alvos do V8 em Linux; confirmado nas linhas de comando do `out/Default`: `-O3` em `v8_compiler`, `v8_base_without_compiler`). O mesmo vale para partition_alloc (`build_overrides/partition_alloc.gni:60`) e para as fontes `core_hot` do Blink (dom, html, layout, css: `core/BUILD.gn:484-506`). O bloco do Thorium em `v8/BUILD.gn` (~1713: `-O3` + `-Wl,-O3` em build oficial) portanto não muda o código do V8 aqui. Sobram, em -O2, os alvos de hot path JS/DOM abaixo: Blink `platform` (strings/fontes/paint/scheduler), `heap` (Oilpan, ligado ao V8 por cppgc) e `base` (task runners, sequence manager). Ficam de fora: `core` inteiro (o upstream já separa o quente em `core_hot`; trocar `core.gni` duplicaria a config em `core_hot` e é o alvo que mais incha), `wtf` e `bindings` (sem `optimize_max`; exigiria inserir config, não só trocar), codecs/mídia (já em `optimize_max`, fora do caminho do Speedometer).

Com PGO: o perfil PGO (`chrome_pgo_phase=2`) marca funções frias, que o clang otimiza para tamanho, e as quentes seguem o nível do alvo. Então -O3 num alvo com PGO só vale de fato para o código quente (inlining e unroll mais agressivos onde há contagem), e o custo em tamanho tende a ser menor que o medido sem PGO. É uma hipótese, não medida. O perfil oficial cobre o Chrome upstream; as partes que os patches do ungoogled/Helium/aerographene mudam não têm contagem.

Artefato (todo perfil diferente de `off`): variante com sufixo no nome, `aerographene-<ver>-<tag>-<sha>-o3<perfil>-<cpu>-x86_64_linux.tar.zst` (artifact do Actions `aerographene-linux-x86_64-o3<perfil>`). Convive em `dist/` com o da build normal; o `inner.sh` só apaga tarball do mesmo cpu e mesma variante. `release.yml` não conhece essas variantes (não são para release).

Como ligar e desligar (não dispara nada sozinho; só o dono, ADR 0004):

```
gh workflow run build.yml -R newcortexbr/aerographene --ref <branch> -f o3=hot    # variante hot
gh workflow run build.yml -R newcortexbr/aerographene --ref <branch> -f o3=wide   # variante wide (rejeitada)
gh workflow run build.yml -R newcortexbr/aerographene --ref <branch> -f o3=ui     # base | ui | skia | lto3 | global idem
gh workflow run build.yml -R newcortexbr/aerographene --ref <branch> -f o3=off    # build normal (também é o padrão)
```

Local: `AERO_O3=hot bash build/build.sh`. Valor inválido aborta antes de qualquer trabalho.

Cache e custo: o perfil não entra no hash da série (sem re-patch nem recriação da árvore). Mudar de perfil muda a linha de comando só dos objetos dos alvos listados; o ninja recompila só eles e relinka (o ThinLTO do `chrome` é refeito inteiro, é o custo dominante). O ccache indexa pela linha de comando, então alternar entre `off` e `hot` volta a acertar o cache dos objetos já compilados. Estimativa, não medida: `hot` ≈ 2 mil objetos, `wide` ≈ +1 mil; compilação de dezenas de minutos mais o link. Medir na primeira execução (`ccache -s` no log). A `out/Default` é compartilhada com a build normal; depois de uma noite `-o3*`, a próxima build normal (`o3=off`) recompila esses objetos (acerta o ccache) e restaura os `BUILD.gn`.

Efeito esperado: ganho pequeno em Speedometer/JetStream (o motor JS já é -O3); aumento do binário de ordem de poucos MB. Regra do produto (AGENTS.md): nenhuma mudança piora mais de 2% a linha de base. Plano de medição: duas builds `cpu=avx2` isoladas (`o3=hot`, depois `o3=wide`), cada uma contra a v0.3.2 normal, mesmo protocolo e mesmas condições do `docs/BASELINE.md` (perfil `performance`, sem carga paralela, Comet Lake), Speedometer manual repetido (não automatizado), mais tamanho do pacote e RSS/startup do harness. Um perfil só entra se o ganho superar o ruído sem violar os 2%.

Tamanho de `.text` por objeto, -O2 contra -O3 (14/10/2026, Cezanne, container `aero-c4-lin`, linha de comando do `out/Default` só lida, saída em `/tmp` do container; sem ThinLTO, CFI e PGO, porque `-c` com LTO gera bitcode; o `-march` do `out/Default` naquele momento era `ivybridge`). Só indicativo: com LTO o inlining entre módulos e o ICF mudam os números, e com PGO as funções frias não crescem.

```
objeto                              .text -O2   .text -O3
v8 turbolev-frontend-pipeline        1354165     1348718   -0,4%
v8 machine-lowering-phase             511710      546980   +6,9%
v8 maglev-graph-builder              1200951     1220873   +1,7%
v8 elements                           654267      933498  +42,7%
v8 mark-compact                       346516      364459   +5,2%
v8 code-stub-assembler                534016      544168   +1,9%
blink platform paint_artifact_comp.    59590       64334   +8,0%
blink platform widget_base             42563       44707   +5,0%
blink heap thread_state                 6823        7179   +5,2%
blink wtf string_impl                  45607       47240   +3,6%
base values                            46060       49723   +8,0%
base sequence_manager_impl             46446       52997  +14,1%
base task_queue_impl                   59745       63360   +6,1%
blink core local_frame_view           217811      240060  +10,2%
```

Somas da amostra: V8 +7,8% (+2,0% sem `elements`, que sozinho cresce 43%); `hot` (platform+heap, 3 objetos) +6,6%; platform+heap+wtf+base (7 objetos) +7,4%. Leitura: o crescimento típico é de 4% a 8% por objeto, com caudas (V8 `elements`, `sequence_manager_impl`). No V8 o -O3 já está ativo, então esses números dizem o que o upstream já paga, não o que este recurso acrescenta. O custo real de `hot`/`wide` no binário final não foi medido (precisa de build com ThinLTO e PGO); como `platform`+`heap`+`base` são uma fração pequena do `.text` do `chrome`, o esperado é bem menos de 1% do binário, hipótese a confirmar.

## release e pacote

Item 12 do `SCOPE.md`. A versão `vX.Y.Z` do aerographene (v0.x.x enquanto não houver release estável; primeira `v0.1.0`) é independente da do Chromium. Fonte única: `AERO_VERSION` em `build/config.sh`; `patches/aerographene/branding-version.patch` (`kVersion` em `chrome/common/aero_version.h`) e `pkgver` do PKGBUILD acompanham à mão, e o `inner.sh` aborta se o header divergir do `config.sh`. Subir a versão só recompila `chrome_main_delegate.cc` e `version_ui.cc` (+ link), não a árvore. Para subir a versão: mudar os três, a tag do `release` e o `.SRCINFO`.

1. rodar o workflow `build` (input `cpu`: `avx2` padrão, `avx1` = `-march=ivybridge`) e anotar o `run_id`. `AERO_CPU`/`MARCH` (env; `build/config.sh`) escolhem o alvo: avx2 usa `out/Default` e `~/aerographene-ccache`; avx1 usa `out/Avx1` e `~/aerographene-ccache-avx1` (o gn fica em `out/Default/gn`). Alternar re-patcheia o `BUILD.gn` da árvore compartilhada (o `-march` entra no hash da série), mas a linha de comando de cada `out/` não muda. Push em `main` compila só avx2.
2. disparar `release` (`workflow_dispatch`) com `run_id`, `tag` (`vX.Y.Z`) e `cpu`: baixa o artifact, gera ``<cpu>-linux--aerographene-vX.Y.Z.tar.zst`, `<cpu>-arch--….pkg.tar.zst`, `<cpu>-debian--….deb`, `<cpu>-fedora--….rpm`` com `packaging/build-native.sh`, `SHA256SUMS` e cria a release como draft (ou acrescenta ao draft da tag). Publicar à mão depois de conferir.
3. o `.pkg.tar.zst` vem do `packaging/arch/PKGBUILD` (instala em `/opt/aerographene`, wrapper `/usr/bin/aerographene`, GPL-3.0-only) rodado em container sobre o tarball local; deb e rpm vêm da mesma árvore via nfpm. Ver `docs/PACKAGING.md` e `docs/wiki/pacotes.md`. Para subir a versão do produto o `pkgver` não precisa mais ser editado (vem da tag via `AERO_PKGVER`).

`makepkg`, `namcap`, nfpm e instalação em containers testados em 13/10/2026 (`docs/PACKAGING.md`). O release.yml completo (dispatch) não foi executado.

## branding: versão e strings da UI

Versão: `patches/aerographene/branding-version.patch` cria `chrome/common/aero_version.h` (`aero::kVersion = "0.3.0"`, header estático em `non_code_constants`, incluído só por `chrome_main_delegate.cc` e `version_ui.cc`; não toca BRANDING nem `base/version_info`, que são incluídos em toda a árvore e forçariam recompilação total a cada bump), e usa em `--version` (`aerographene 0.1.0 (Chromium 154.0.8037.97)`), `--product-version`, chrome://version e Sobre (`0.1.0 (Chromium 154.0.8037.97)` no campo de versão). Não altera mensagens GRIT nem HTML (diferente do `add-helium-versioning.patch`, que muda a mensagem `IDS_SETTINGS_ABOUT_PAGE_BROWSER_VERSION` e perderia as traduções). `GetVersionNumber()`, UA e extensões continuam em 154.0.8037.97.

Strings: `build/branding_strings.py` roda no `inner.sh` depois dos patches e antes do `gn gen` (o script, `build/strings_ptbr_extra.json` entram no hash da série; o original de cada arquivo tocado vai para `.aero-applied/strings-orig` e é restaurado antes do `patch -R` do re-patch incremental). Troca "Chrome"/"Chromium"/"Google Chrome" e "Helium" por "aerographene" no texto das mensagens dos grds raiz `chrome/app/{chromium_strings,generated_resources}.grd`, `components/components_{chromium_,}strings.grd`, `extensions/strings/extensions_strings.grd`, `ui/strings/ui_strings.grd` e suas partes `.grdp`.

Ids: o id GRIT é o fingerprint do texto inglês (+ `meaning`), então mudar o texto sem mexer nos `.xtb` derrubaria todas as traduções para inglês. O script calcula o id antigo e o novo com o próprio grit da árvore (`grd_reader.Parse` de um grd sintético com as mensagens, `clique.GetId()` = `grit.extern.tclib.GenerateMessageId`), reescreve nos `.xtb` de cada idioma o id e troca o nome literal na tradução. É reproduzível porque usa o código do grit, não uma cópia do fingerprint. Limites: tradução sem o nome literal (idiomas que transliteram) só ganha o id novo e mantém o nome antigo; mensagens com `use_name_for_id` ou `translateable="false"` só têm o texto trocado; ids que colidem após a troca mantêm a primeira entrada do xtb (12 casos no espelho, `duplicadas descartadas`). Se um dia a árvore já estiver com texto novo e xtb antigo (execução interrompida entre as escritas), não há como recuperar: recriar a árvore. A escrita é xtb antes do grd, cada arquivo por rename atômico.

Helium: as mensagens adicionadas pelos patches do Helium (todas em `generated_resources.grd` e `settings_strings.grdp`) trocam "Helium" por "aerographene" com a mesma regra (palavra com maiúscula; `helium://`, prefs `helium.*` e identificadores não são texto de mensagem). `KEEP_NAMES` está vazio desde 14/10/2026: as 24 mensagens que mantinham "Helium" (serviços e setup do Helium) saíram com `services-prefs.patch` e `onboarding-page.patch`.

Vocabulário space: `build/strings_space.json` mapeia nome IDS → `{en, pt-BR}` (texto final, "profile" → "space"; ver [spaces](wiki/spaces.md)). Para cada mensagem listada o script troca o corpo no `.grd`/`.grdp` (restaurando os `<ph>` originais), recalcula o id GRIT, renomeia o id em todos os `.xtb` e grava o texto do JSON no pt-BR e en-GB (acrescenta a entrada quando o `.xtb` não tem a antiga, caso de `chromium_strings`); os outros idiomas mantêm a tradução antiga sob o id novo. Flags `--space JSON` e `--no-space`; o JSON entra no hash da série (`inner.sh`).

Traduções pt-BR extras: essas mensagens não têm `.xtb` (o Helium só traz inglês), então apareciam em inglês no pt-BR. `build/strings_ptbr_extra.json` mapeia nome IDS → texto pt-BR (com `<ph name="X"/>` para placeholders); o script calcula com o grit da árvore o id do texto inglês já trocado e acrescenta `<translation>` em `generated_resources_pt-BR.xtb` se o id ainda não existir (mensagens com texto inglês igual a uma já traduzida pelo Chromium reaproveitam a tradução existente). Placeholders divergentes geram aviso e a mensagem fica sem tradução. Variantes por plataforma (`if expr`) recebem o mesmo texto (alvo Linux). Cobertura: aparência/comportamento, layout, atalhos, menus de guia, importador e as strings próprias de guias fixadas (36 nomes desde 14/10/2026, quando saíram as de serviços, setup, atalho de copiar URL, MRU, abas ao lado da ativa e Shift+clique direito; antes eram 120, com 105 traduções novas no espelho). Outros idiomas continuam em inglês nessas mensagens.

Exclusões (continuam com o nome Google; regex `_EXCLUDE_AFTER` do script): Chrome Web Store/Webstore, Chrome OS/ChromeOS/ChromiumOS (já excluídos por palavra colada), ChromeVox, Chromebook, Chromecast, Chrome Enterprise, Chrome Browser Cloud Management, Chrome Remote Desktop, Chrome Cleanup, Chrome Labs, Chrome DevTools, Chrome Apps/apps (plataforma de apps), Chrome Dino, Chrome Canary/Beta/Dev, Chrome Updater, Chrome for Testing, Chrome Nearby. Efeito colateral: "o app Chromium" (mensagens sobre o app mobile) também fica de fora pela regra de "app". `<ex>`, nomes de `<ph>`, atributos (`desc`, `meaning`), URLs `chrome://` e texto em minúscula não são tocados. Em inglês, "a Chrome" vira "an aerographene".

Uso e testes:

```
python3 build/branding_strings.py --src <árvore> --check --list   # lista e conta, sem escrever
AERO_TEST_SRC=<árvore ou espelho com chrome/ components/ tools/grit> python3 build/test_branding_strings.py
```

O teste de integração carrega os grds com o grit real (chromium_strings, generated_resources, components_chromium_strings; pt-BR e en-GB) antes e depois da troca e exige que nenhuma tradução se perca (635 de 635 em chromium_strings pt-BR; com o grd novo e o xtb antigo cai para 170) e que em pt-BR passem a ter tradução exatamente as mensagens do JSON que não tinham. O espelho precisa dos patches da série aplicados aos grd/grdp para cobrir as mensagens do Helium.

Não coberto: aparência real no navegador, locales além de pt-BR/en-GB (a lógica é a mesma), `.xtb` de `extensions/` e `ui/` (não estavam no espelho), mensagens de grds fora da lista (ex.: `content/`, `chrome/browser/resources` com grd próprio), strings dentro de HTML/TS/C++ fixas. `.desktop`/WM class: `docs/PACKAGING.md`.

Esquema das páginas internas: `patches/aerographene/branding-scheme.patch` muda o valor de `content::kHeliumUIScheme` (de `helium/core/override-chrome-protocol.patch`) e as três cópias literais (`url_fixer.cc`, `builtin_provider.cc`, `tab_search_item.ts`) para `aerographene`; a omnibox mostra `aerographene://settings`, e digitar `aerographene://` ou `chrome://` funciona. `content/public/common/url_constants.h` é incluído por quase toda a árvore: mudar a constante recompila muito. URL `chrome://`/`aerographene://` passada na linha de comando abre a página nova guia: não é efeito do Helium, é a regra do upstream (`chrome/browser/ui/startup/url_util.cc:42-87`, `ValidateLaunchUrlWebUnsafe` só aceita esquemas web-safe, `file:`, `about:blank` e o reset de configurações) para impedir que lançadores externos abram páginas privilegiadas. Mantida. Mudar os `.grd` invalida o cache de recursos/strings (reconstrói muitos objetos de `//chrome`).

## host do runner (Cezanne, Ubuntu 24.04 bare metal desde 10/10/2026)

- acesso administrativo: `ssh claude@cezanne` (sudo); os runners rodam como `dasher` em `~/actions-runner-{1,2,3}`. Cache em `~/aerographene-build` (com `out/Default`) e `~/aerographene-ccache`, restaurados do WSL2: a primeira build no host novo teve 99,7% de acerto no ccache e terminou em ~20 min.
- o smoke (`build/smoke.sh`) roda no host, fora do container: exige as libs gráficas do Chromium instaladas no Ubuntu (atk, atk-bridge, cups, asound, gbm, cairo, pango, Xcomposite/Xdamage/Xfixes/Xrandr, atspi, xkbcommon, nss). Instaladas em 10/10/2026 depois de a run 38029467766 falhar só no smoke.
- após reboot, os runners podem ficar com sessão antiga no GitHub ("A session for this runner already exists") e o job fica na fila; se passar de ~3 min, `gh run cancel` + `gh run rerun` resolve.
- acompanhar runs: `gh run watch`/`gh run view`; ferramentas locais do dono (runwatch, aero-top) ficam fora do repo.
