# build x86-64-v2 + AVX para a Ivy Bridge (v0.3)

Status: proposto em 12/10/2026. Nada implementado, nenhum build disparado. Complementa o ADR 0003 ("a Ivy Bridge fica sem build até existir um segundo alvo v2+AVX").

## fatos verificados

- Ivy Bridge (Core de 3ª geração) tem SSE4.2, POPCNT, PCLMUL, AES, AVX, F16C, RDRAND e FSGSBASE; não tem AVX2, BMI1/2 nem FMA. Conferido com `clang 23.1.1 -march=ivybridge -dM -E` (macros definidas: `__AVX__`, `__F16C__`, `__FSGSBASE__`, `__PCLMUL__`, `__POPCNT__`, `__RDRND__`, `__SSE4_2__`; sem `__AVX2__`, `__BMI__`, `__FMA__`). gcc dá o mesmo conjunto. O nível x86-64-v2 (SSE4.2, POPCNT, SSSE3) mais AVX/F16C é, na prática, `-march=ivybridge`; `-march=x86-64-v2 -mavx` deixaria F16C/RDRAND/PCLMUL de fora (hipótese de ganho pequeno; não medido).
- A linha de base do Chromium 154 é SSE3: `build/config/compiler_cpu_abi.gn:58` (`-msse3` em x64) e `build/config/win/BUILD.gn:123` (comentário "Chrome currently requires SSE3"), conferido no `src` do Cezanne. O `base/cpu.cc` detecta até SSE4.2 e AVX por tempo de execução e o código com dispatch (Skia, libyuv, ffmpeg, V8, zlib etc.) escolhe o caminho; a Ivy Bridge usa o caminho AVX.
- O `-march` aerographene não é arg GN: `build/inner.sh` injeta `cflags/ldflags/rustflags` em `build/config/compiler/BUILD.gn` (linhas 1345–1350 no `src` atual), a partir de `MARCH` em `build/config.sh` (`x86-64-v3`). O `MARCH` entra no hash da série (`.aero-patches.hash`) e no hash do ccache.
- PGO: o `args.gn` atual usa `chrome_pgo_phase=2` com o perfil oficial `chrome-linux-8037-…profdata` (`docs/BUILD.md`). O perfil é do Google, gerado para o baseline dele.
- Recursos medidos no Cezanne (ssh, só leitura): `src` 26 GB, `out/Default` 16 GB, ccache 5,4 GB (teto 40 GB), disco do host 218 GB com 126 GB livres. O runner tem 6 cores/12 threads e ~15 GB de RAM; builds são exclusivas pelo grupo de concurrency `build` (ADR 0004); `out/Default` é único e compartilhado pelos três runners.
- `-march` é no x64 só para `is_linux` (patch por `inner.sh`), então um alvo Windows não herda a flag.

## hipóteses (não verificadas)

- ThinLTO/PGO: trocar o `-march` não invalida o perfil (o profdata casa por hash de CFG do código-fonte, não por ISA), mas muda o código gerado e as decisões de inline; ganho/perda de PGO com v2+AVX não medido. A cache de objetos do ccache muda (flag entra no hash): trocar `MARCH` recompila tudo (tempo não medido; referência: build completa fria ~8 h, build com ccache cheio ~20 min no mesmo `MARCH`).
- Código escrito com `__AVX2__` condicional (ex.: partes do V8/Skia) é escolhido em tempo de compilação; com `-march=ivybridge` cai no caminho SSE/AVX, e `-march=x86-64-v3` com binário rodando na Ivy Bridge dá SIGILL. Por isso não há atalho: o binário v3 não roda na Ivy.
- Desempenho esperado da Ivy Bridge: CPU antiga e sem FMA; a regra de 2% do SCOPE vale contra a linha de base *desse* hardware, não contra o Cezanne. A linha de base existente é do Comet Lake e não serve.

## opções

1. Segunda build no mesmo runner, `MARCH=ivybridge`, `out` separado (`out/IvyBridge`) e ccache próprio. Prós: reusa `build.sh`/`inner.sh`; um parâmetro em `config.sh`; sem hardware novo. Contras: `out` + ccache extras (~16 GB + ~6 GB; cabe nos 126 GB livres, mas `src` é um só e o re-patch troca `BUILD.gn`: cada alternância de `MARCH` re-patcheia e recompila a árvore, ver "cache" em `docs/BUILD.md`); build exclusiva (concurrency `build`) dobra o tempo de CI por release; um segundo ccache (ou o mesmo com chave diferente) é necessário para não evictar o v3.
   - 1a. `src` único, `out` por `MARCH` e ccache compartilhado de 40 GB. Menos disco, alternância mais cara.
   - 1b. segunda árvore `src` (+26 GB, +re-download) para evitar re-patch. Mais disco, builds independentes.
2. Substituir v3 por v2+AVX para todos. Prós: um pacote. Contras: regride Comet Lake/Cezanne (AVX2/BMI/FMA), vai contra o ADR 0003 e a regra de 2%. Rejeitada.
3. Compilar na própria Ivy Bridge. Prós: nenhum. Contras: CPU antiga e sem RAM suficiente para ThinLTO/Chromium. Rejeitada.
4. Sem build Ivy; usar ungoogled/Helium (baseline SSE3) nela. Prós: custo zero. Contras: o objetivo da v0.3 não é cumprido; sem a série própria. Fallback.

## recomendação

Opção 1 com 1a: parâmetro `MARCH=ivybridge` (mais `AERO_OUT`/nome do pacote `…-ivybridge`) acionado por input de `workflow_dispatch` do `build.yml`, `out/Ivy`, ccache em diretório próprio e `max_size` ajustado; ThinLTO igual, PGO oficial mantido (medir com e sem). Só rodar depois do alvo v3 estável e fora das janelas de build v3; nunca em paralelo (concurrency `build`). Pacote `.tar.zst` separado (`aerographene-<ver>-ivybridge-linux.tar.zst`); PKGBUILD continua v3 (Arch/CachyOS).

## passos para executar na v0.3

1. Em `build/config.sh` aceitar `MARCH` por env (padrão `x86-64-v3`); em `build/inner.sh` separar `out/` por alvo (hoje `out/Default` fixo, e `smoke.sh`/pacote leem esse caminho): mudança em `build/` só depois do dono liberar, fora deste ADR.
2. Pré-checagem estática da AGENTS.md; então um build de diagnóstico no runner, com `rustflags` conferindo `-Ctarget-cpu=ivybridge` (nome aceito pelo rustc).
3. Confirmar no log do `gn gen` que `-march=ivybridge` entrou e que `-msse3` vem junto (hipótese: o `-march` do config vem depois do `-msse3` do `compiler_cpu_abi` e prevalece; checar a ordem numa linha de `ninja -t commands`).
4. Verificação no hardware: o binário abre na Ivy Bridge (smoke), `grep` de instruções AVX2 no binário (`objdump -d | grep -c ymm`+`vfmadd`: não deve haver FMA/BMI) e checagem de `chrome://version`.
5. Medir com `bench/harness.py --quick --tabs 10` na Ivy contra Helium e ungoogled na mesma máquina; regra de 2% contra essa linha de base; anotar em `docs/BASELINE.md`.
6. Atualizar `docs/BUILD.md` (segundo out/ccache e disco), `patches/README.md` e o ADR 0004 (concurrency com dois alvos, tempo de CI), e o ADR 0003 (retirar "sem build").

Risco aceito: duas variantes dobram o tempo de CI por release e o espaço de cache; a Ivy Bridge pode ficar sem PGO se o perfil oficial se mostrar pior (medir).
