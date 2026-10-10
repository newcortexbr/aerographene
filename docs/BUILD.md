# build

Fluxo do item 2 do `SCOPE.md`: ungoogled-chromium `154.0.8037.97-1` (Chromium 154.0.8037.97, o mesmo do Helium 0.18.3.1) pelo fluxo oficial do `ungoogled-chromium-portablelinux`, mais a série própria em `patches/series` e as flags do ADR 0003.

## arquivos

- `build/config.sh`: tag fixada do ungoogled/portablelinux e o alvo `-march`.
- `build/build.sh`: roda no host (runner). Requer só `git` e `docker`. Clona o portablelinux na tag (com o submódulo ungoogled), gera a imagem `chromium-builder:trixie-slim` do próprio portablelinux e a camada `aerographene-builder` (+ `zstd`, `patch`), e chama `build/inner.sh` no container.
- `build/inner.sh`: no container, usa as funções de `portablelinux/scripts/shared.sh`: download do tarball, pruning, patches ungoogled + portablelinux, série aerographene, `-march`, domain substitution, `args.gn`, toolchain, `gn gen`, `ninja chrome`, pacote `.tar.zst`.
- `build/flags.gn`: flags próprias, aplicadas por cima de `ungoogled-chromium/flags.gn` e `flags.linux.gn`; a última definição de cada chave vence.
- `.github/workflows/build.yml`: gatilhos `workflow_dispatch` e `push` em `main` com mudança em `build/**`, `patches/**` ou no workflow. Nunca `pull_request` (ADR 0004).

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
- ThinLTO (`use_thin_lto`, `thin_lto_enable_optimizations`), ICF (`use_icf`), `symbol_level=0`, `is_official_build=true`; sem `-O3`.
- jobs: padrão `auto` = `nproc` dentro do container na hora da build (os runners dividem 5..12 CPUs dinamicamente); número explícito em `JOBS`/input `jobs` sobrepõe. O log mostra o valor e o `MemAvailable`. Sem teto por RAM, por decisão do dono: com ~13 GB e 12 jobs há risco de OOM (compilações pesadas e o link ThinLTO do `chrome`); se ocorrer, rodar com `jobs` menor.
- RAM (~14 GB): `concurrent_links` não pode ser definido com ThinLTO (assert do GN), o Chromium calcula pela RAM. O link do `chrome` com ThinLTO é o pico de memória; se estourar, a saída seria swap no WSL2 ou limitar `--thinlto-jobs`.
- chaves Google (ADR 0006): lidas de secrets opcionais `GOOGLE_API_KEY`, `GOOGLE_DEFAULT_CLIENT_ID`, `GOOGLE_DEFAULT_CLIENT_SECRET`; ausentes, ficam os valores vazios do ungoogled. Não aparecem no log.
- labels do runner: `[self-hosted, linux, intense]`, suposição. A API de runners da org exige permissão de admin, então os labels exatos não foram confirmados.
- produto: o pacote se chama `aerographene-<AERO_VERSION>-<tag>-<sha>-x86_64_linux.tar.zst` (versão do produto de `build/config.sh`, tag ungoogled, SHA do repo) e tem um symlink `aerographene` → `chrome`. Ícones e nome do binário ficam para depois; versão e strings: seção "branding" abaixo.

## release e pacote

Item 12 do `SCOPE.md`. A versão `vX.Y.Z` do aerographene (v0.x.x enquanto não houver release estável; primeira `v0.1.0`) é independente da do Chromium. Fonte única: `AERO_VERSION` em `build/config.sh`; `patches/aerographene/branding-version.patch` (`kVersion` em `chrome/common/aero_version.h`) e `pkgver` do PKGBUILD acompanham à mão, e o `inner.sh` aborta se o header divergir do `config.sh`. Subir a versão só recompila `chrome_main_delegate.cc` e `version_ui.cc` (+ link), não a árvore. Para subir a versão: mudar os três, a tag do `release` e o `.SRCINFO`.

1. rodar o workflow `build` e anotar o `run_id`.
2. disparar `release` (`workflow_dispatch`) com `run_id` e `tag` (`vX.Y.Z`): baixa o artifact `aerographene-linux-x86_64`, renomeia para `aerographene-X.Y.Z-x86_64_linux.tar.zst`, gera `SHA256SUMS` e cria a release como draft. Publicar à mão depois de conferir.
3. `packaging/arch/PKGBUILD` consome esse tarball (instala em `/opt/aerographene`, symlink `/usr/bin/aerographene`, GPL3). Com a release publicada: ajustar `pkgver`, rodar `updpkgsums` e `makepkg --printsrcinfo > .SRCINFO`. Hoje os sha256 são `SKIP`. O repo é privado, então baixar o asset exige token.

Não testado: `makepkg` completo e `namcap` (não há release ainda).

## branding: versão e strings da UI

Versão: `patches/aerographene/branding-version.patch` cria `chrome/common/aero_version.h` (`aero::kVersion = "0.1.0"`, header estático em `non_code_constants`, incluído só por `chrome_main_delegate.cc` e `version_ui.cc`; não toca BRANDING nem `base/version_info`, que são incluídos em toda a árvore e forçariam recompilação total a cada bump), e usa em `--version` (`aerographene 0.1.0 (Chromium 154.0.8037.97)`), `--product-version`, chrome://version e Sobre (`0.1.0 (Chromium 154.0.8037.97)` no campo de versão). Não altera mensagens GRIT nem HTML (diferente do `add-helium-versioning.patch`, que muda a mensagem `IDS_SETTINGS_ABOUT_PAGE_BROWSER_VERSION` e perderia as traduções). `GetVersionNumber()`, UA e extensões continuam em 154.0.8037.97.

Strings: `build/branding_strings.py` roda no `inner.sh` depois dos patches e antes do `gn gen` (parte do hash da série; o original de cada arquivo tocado vai para `.aero-applied/strings-orig` e é restaurado antes do `patch -R` do re-patch incremental). Troca "Chrome"/"Chromium"/"Google Chrome" por "aerographene" no texto das mensagens dos grds raiz `chrome/app/{chromium_strings,generated_resources}.grd`, `components/components_{chromium_,}strings.grd`, `extensions/strings/extensions_strings.grd`, `ui/strings/ui_strings.grd` e suas partes `.grdp`.

Ids: o id GRIT é o fingerprint do texto inglês (+ `meaning`), então mudar o texto sem mexer nos `.xtb` derrubaria todas as traduções para inglês. O script calcula o id antigo e o novo com o próprio grit da árvore (`grd_reader.Parse` de um grd sintético com as mensagens, `clique.GetId()` = `grit.extern.tclib.GenerateMessageId`), reescreve nos `.xtb` de cada idioma o id e troca o nome literal na tradução. É reproduzível porque usa o código do grit, não uma cópia do fingerprint. Limites: tradução sem o nome literal (idiomas que transliteram) só ganha o id novo e mantém o nome antigo; mensagens com `use_name_for_id` ou `translateable="false"` só têm o texto trocado; ids que colidem após a troca mantêm a primeira entrada do xtb (12 casos no espelho, `duplicadas descartadas`). Se um dia a árvore já estiver com texto novo e xtb antigo (execução interrompida entre as escritas), não há como recuperar: recriar a árvore. A escrita é xtb antes do grd, cada arquivo por rename atômico.

Exclusões (continuam com o nome Google; regex `_EXCLUDE_AFTER` do script): Chrome Web Store/Webstore, Chrome OS/ChromeOS/ChromiumOS (já excluídos por palavra colada), ChromeVox, Chromebook, Chromecast, Chrome Enterprise, Chrome Browser Cloud Management, Chrome Remote Desktop, Chrome Cleanup, Chrome Labs, Chrome DevTools, Chrome Apps/apps (plataforma de apps), Chrome Dino, Chrome Canary/Beta/Dev, Chrome Updater, Chrome for Testing, Chrome Nearby. Efeito colateral: "o app Chromium" (mensagens sobre o app mobile) também fica de fora pela regra de "app". `<ex>`, nomes de `<ph>`, atributos (`desc`, `meaning`), URLs `chrome://` e texto em minúscula não são tocados. Em inglês, "a Chrome" vira "an aerographene".

Uso e testes:

```
python3 build/branding_strings.py --src <árvore> --check --list   # lista e conta, sem escrever
AERO_TEST_SRC=<árvore ou espelho com chrome/ components/ tools/grit> python3 build/test_branding_strings.py
```

O teste de integração carrega os grds com o grit real (chromium_strings, generated_resources, components_chromium_strings; pt-BR e en-GB) antes e depois da troca e exige o mesmo número de mensagens com tradução (635 de 635 em chromium_strings pt-BR); com o grd novo e o xtb antigo cai para 170.

Não coberto: aparência real no navegador, locales além de pt-BR/en-GB (a lógica é a mesma), `.xtb` de `extensions/` e `ui/` (não estavam no espelho), mensagens de grds fora da lista (ex.: `content/`, `chrome/browser/resources` com grd próprio), strings dentro de HTML/TS/C++ fixas, `.desktop` e WM class. Mudar os `.grd` invalida o cache de recursos/strings (reconstrói muitos objetos de `//chrome`).
