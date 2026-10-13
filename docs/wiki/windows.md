# windows (cross-compile no Cezanne)

estado do build do aerographene para Windows 10 e 11 x64 (nada exclusivo do 11; piso 1809 por causa do ConPTY; testado só no 11) por cross-compile Linux→Windows no Cezanne (fatia D do `docs/PLANO-V0.3.md`). Ainda não existe navegador Windows: só a toolchain e alvos pequenos (`chrome_elf.dll`, `crashpad_handler.exe`) foram provados.

## decisão (dono, 13/10/2026)

uma só série de patches para Linux e Windows; Windows não perde função. Patches que tocam arquivos só-Linux continuam na série (aplicam e não compilam no Windows); funções nossas ganham implementação Windows (subfatias D3a–D3e no plano). Revoga a ideia anterior de série derivada sem `use-default-theme`, `process-names` e `branding-desktop`.

## o que já funciona

- árvore separada por hardlink da árvore do CI (sem `out/`), com a série completa aplicada, inclusive `aerographene/windows-disable-rlz.patch`.
- `build/win/prepare.sh` repõe sozinho, com hash conferido, o que o tarball do ungoogled/portablelinux não traz e extrai o toolchain VS 2026 + SDK 10.0.28000 em sistema de arquivos insensível a caixa (ciopfs).
- `gn gen out/Win` passa sem passo manual; `chrome_elf.dll` linka com lld-link (`PE32+ ... x86-64`).
- D3b: espaços (uma janela por space, troca no lugar), raio e fonte do tema, `--import-theme`, repositório de temas, tokens e import `.aerotheme` valem no Windows; o código compila no `out/Win` (objetos, sem link do `chrome`). Dados do tema no Windows: `%LOCALAPPDATA%\aerographene\theme.json` e `...\themes\` (provisório até a D3d). Fonte reserva do pixelized no Windows: Consolas.
- leitura de arquivos de tema no Windows (`theme.json`, `.aerotheme`, `theme.json` do repositório): `CreateFileW` com `FILE_FLAG_OPEN_REPARSE_POINT`; recusa pipe/console/dispositivo, symlink/junção e diretório (mais estrito que o Linux). Linux mantém `S_ISREG`, `O_NONBLOCK`, `lstat` e `O_NOFOLLOW`.
- notas (`chrome://notes`) registradas no Windows, mas sem leitura da vault: o leitor confinado Windows é a D3c; até lá a página mostra "leitura da vault ainda não disponível neste sistema". Terminal continua só Linux (D3e).

## o que não está no repositório

- o pacote do toolchain (`<hash>.zip`, VS e SDK da Microsoft) é software licenciado: fica só no host, nunca no git, artifact ou release.
- a árvore Windows, os downloads e a libfuse2 local ficam no host, fora do repo.

## como reproduzir no host

```bash
# 1. árvore: hardlink da árvore do CI (exceto out/), no mesmo sistema de arquivos.
#    nunca editar arquivo no lugar: só sed -i, patch ou cópia nova (quebram o link).
mkdir -p <win>/src && cd <árvore do CI>/src
for f in $(ls -A | grep -vx out); do cp -al "$f" <win>/src/; done
#    se a série do repo for diferente da aplicada no CI: quebrar o link dos arquivos que ela
#    toca (cp -p f f.new && mv f.new f), reverter .aero-applied (patch -R) e aplicar a série
#    nova como o CI (patch -p1 --ignore-whitespace).

# 2. preparar (idempotente; rodar de novo depois de reboot, para remontar o ciopfs)
AERO_WIN_TOOLCHAIN_DIR=<dir com o zip do toolchain> build/win/prepare.sh <win>/src

# 3. gerar e compilar (gn e ninja Linux do CI; args vêm de build/win/args.gn)
cd <win>/src && gn gen out/Win
nice -n 19 ninja -C out/Win -j8 chrome_elf
```

o `prepare.sh` faz, nesta ordem (cobre os erros 1, 2, 4, 5, 6, 7 e 8 da seção D do plano; o 3 virou patch):

1. `build/ciopfs` (hook `ciopfs_linux`), sha1 de `build/ciopfs.sha1`; `libfuse.so.2` sem sudo via `apt-get download libfuse2t64` + `dpkg-deb -x` no cache.
2. runtime clang Windows `clang-win-runtime-library-<CLANG_REVISION>-<SUB>.tar.xz` (o mesmo que `tools/clang/scripts/update.py` baixa), sha256 fixado no script por versão.
3. `buildtools/linux64-format/clang-format` (no tarball é symlink do container), sha256 do `DEPS`.
4. `build/toolchain/win/rc/linux64/rc` (hook `rc_linux`), sha1 de `rc.sha1`.
5. `windows.0.52.0.lib` do crate `windows_x86_64_msvc` (podado): o vendor do Chromium não guarda checksum, então o `.crate` é conferido contra o sha256 fixado e o índice do crates.io, e `build.rs`/`src/lib.rs`/`Cargo.toml.orig` têm de ser iguais aos vendorizados.
6. toolchain: `build/vs_toolchain.py update --force` com `DEPOT_TOOLS_WIN_TOOLCHAIN=1`, `DEPOT_TOOLS_WIN_TOOLCHAIN_BASE_URL=$AERO_WIN_TOOLCHAIN_DIR` e `GYP_MSVS_HASH_<TOOLCHAIN_HASH do vs_toolchain.py>=<hash do zip>`.
7. arquivos com mtime no futuro: link quebrado e `touch` (senão o ninja regenera em laço).
8. `out/Win/args.gn` copiado de `build/win/args.gn` se não existir; recusa `use_sysroot=false`.

arquivo novo sempre entra por temporário + `mv`, então nada é escrito através de hardlink do CI.

## problemas conhecidos

- `use_sysroot=false` (do `flags.windows.gn` do ungoogled) quebra o cross: vale também para a toolchain host Linux, que passa a pedir glib via `pkg-config` do host. O sysroot Debian da árvore serve.
- quatro patches do Helium (`keyboard-shortcuts`, `ublock-install-as-component`, `crash-reporting-prefs`, `toolbar-button-prefs`) só aplicam com o fuzz padrão do `patch`, porque a domain substitution muda linhas de contexto; o CI aplica assim. Os patches próprios novos devem aplicar com `--fuzz=0`.
- `base_unittests` não compila (substituição de domínios do ungoogled em `rtl_unittest.cc`); só testes.
- `lld-link: warning: ignoring unknown argument '-Wl,--icf=all'`: flag ICF de ELF chegando ao link Windows; tratar em D4.
- compilar objetos do `chrome` no `out/Win` exige rodar o ninja dentro do `aerographene-builder:v2` (node, tsc etc. do container; montar `~/aerographene-win` no mesmo caminho) e falha em ações MIDL (`third_party/win_build_output/midl/...tlb` "needs to be generated from Windows first", podado no tarball). Contorno para checar compilação: comando do objeto via `ninja -t commands <obj>` com `mkdir -p` do diretório de saída. Bloqueio real para D4.
- deps só-Windows vazias no tarball (`microsoft_dxheaders`, `microsoft_webauthn`, `microsoft_multimedia_redirection`, `widevine/cdm/win`, `wix`) devem bloquear o `chrome` (D4).

## resumo para agentes

- cross Linux→Windows no Cezanne: árvore própria por `cp -al` da árvore do CI, saída `out/Win`; não tocar `out/Default`, `out/Avx1` nem a árvore do CI; nunca escrever através de hardlink.
- preparo: `AERO_WIN_TOOLCHAIN_DIR=<dir do zip> build/win/prepare.sh <src>`; idempotente, confere hash de tudo, rodar de novo após reboot (ciopfs). Depois `gn gen out/Win` e `ninja`.
- args em `build/win/args.gn`; RLZ resolvido por `patches/aerographene/windows-disable-rlz.patch` (série única).
- série única Linux+Windows (dono, 13/10/2026); D3b feita (guardas `IS_LINUX || IS_WIN`, POSIX sob `#if`, ramo Win32 equivalente); próximas D3c–D3e no plano.
- testes D3b no Linux: alvo temporário `aero_ui_tests` (overlay, fora da série), 42/42; `TerminateKillsWholeGroup` exige init que colhe zumbis (`docker run --init`).
- notas no Windows: `kVaultReadSupported` false até a D3c; nunca ler sem confinamento.
- o zip do toolchain é licenciado: nunca commitar, copiar para o repo ou publicar.
