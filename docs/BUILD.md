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
- se a série em `patches/` muda (hash do `series` + arquivos), a árvore é recriada a partir do tarball em cache e `out/` é preservado.
- `portablelinux/build/pgo`: perfil PGO baixado.
- `dist/`: o `.tar.zst` da última execução.

Para forçar do zero: apagar `portablelinux/build/src`.

## decisões

- PGO: o ungoogled fixa `chrome_pgo_phase=0` no `flags.gn` porque o perfil é um binário do Google que não vem no tarball (o gclient hook o baixaria). Não está no `pruning.list` e o arquivo está acessível (`chrome/build/linux.pgo.txt` → `chrome-linux-8037-1790747267-…profdata`, HTTP 200 em `storage.googleapis.com/chromium-optimization-profiles/pgo_profiles/`, verificado em 05/10/2026). Então o build baixa o perfil oficial e usa `chrome_pgo_phase=2`; se o download falha, cai para `0`. Os patches do ungoogled deixam parte do perfil desatualizada (só gera avisos). Desligável com `AEROGRAPHENE_PGO=0` ou o input `pgo` do workflow.
- `-march=x86-64-v3`: o GN do Chromium 154 não tem arg de `-march` para x86 (só `arm_arch`) nem `extra_cflags`. O `inner.sh` acrescenta `-march=x86-64-v3` (cflags, asmflags, ldflags, para o LTO) e `-Ctarget-cpu=x86-64-v3` (Rust) à `config("compiler_cpu_abi")` de `build/config/compiler/BUILD.gn`, só em `current_cpu == "x64" && is_linux`. Isso vale também para as ferramentas do host, que rodam no Cezanne (v3). Candidato a virar patch em `patches/` quando o dono da série quiser.
- ThinLTO (`use_thin_lto`, `thin_lto_enable_optimizations`), ICF (`use_icf`), `symbol_level=0`, `is_official_build=true`; sem `-O3`.
- RAM (~14 GB): `concurrent_links=1` e `ninja -j 4` (input `jobs`). O link do `chrome` com ThinLTO é o pico de memória; se estourar, baixar `jobs` não ajuda o link: a saída seria swap no WSL2 ou limitar `--thinlto-jobs`.
- chaves Google (ADR 0006): lidas de secrets opcionais `GOOGLE_API_KEY`, `GOOGLE_DEFAULT_CLIENT_ID`, `GOOGLE_DEFAULT_CLIENT_SECRET`; ausentes, ficam os valores vazios do ungoogled. Não aparecem no log.
- labels do runner: `[self-hosted, linux, intense]`, suposição. A API de runners da org exige permissão de admin, então os labels exatos não foram confirmados.
- produto: o pacote se chama `aerographene-<tag>-<sha>-x86_64_linux.tar.zst` e tem um symlink `aerographene` → `chrome`. Branding (nome do binário, ícones, strings) fica para depois.
