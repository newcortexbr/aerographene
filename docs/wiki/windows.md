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
- D3c (13/10/2026): notas no Windows com leitura confinada (lista, leitura, busca, imagens, vigia); escrita responde "não suportado" (a página mostra "escrita ainda não disponível neste sistema"). Repositório de temas confinado. Detalhe em "confinamento (D3c)" abaixo. Terminal: ConPTY + Job Object (D3e, `terminal-win.patch`; ver [terminal](terminal.md)), compila mas não foi executado no Windows.

- D4 (14/10/2026): `chrome` e `mini_installer` linkam no Cezanne (`aerographene.exe` 5,3 MB, `chrome.dll` 337 MB, `mini_installer.exe` 136 MB, todos `PE32+ x86-64`; ThinLTO, sem PGO). Args sem mudança (`build/win/args.gn`, `safe_browsing_mode=0`). Patches para isso: `windows-ungoogled-prefs` e `windows-safe-browsing-dummy` (trechos do ungoogled-chromium-windows 154) e correção `wstring` em `notes-b5` (`vault_watcher.cc`). Não executado no Windows.

## alvos de CPU e pacote (`build/win/build.sh`, 15/10/2026)

mesmos alvos do Linux (ADR 0009): `avx2` = `x86-64-v3`, `avx1` = `ivybridge` (`MARCH` no env sobrescreve). Os dois usam o mesmo `out/Win` em sequência: o disco do Cezanne não comporta dois (`out/Win` completo ~15 GB, 46 GB livres em 15/10/2026); trocar de alvo recompila tudo.

- `-march`: o script acrescenta, na `config("compiler_cpu_abi")` de `build/config/compiler/BUILD.gn` da árvore Windows, um bloco marcado `# aerographene-win` só para `current_cpu == "x64" && is_win`: `cflags += [ "/clang:-march=<m>" ]` (clang-cl) e `rustflags = [ "-Ctarget-cpu=<m>" ]`. O link ThinLTO (lld-link) usa o `target-cpu` gravado em cada função do bitcode. A toolchain host Linux não recebe `-march`. Rodar de novo troca o bloco (idempotente), escrevendo por temporário + `mv`.
- `out/Win/.aero-cpu` guarda o alvo do último `gn gen`; `ninja` e `pack` recusam se não bater.
- `ninja` roda no `aerographene-builder:v2` com `--ulimit nofile=65536:65536`, `flock /tmp/aero-win-ninja.lock` e `nice -n 19`; recusa se houver run em andamento no GitHub (`gh run list -s in_progress`; `AERO_WIN_FORCE=1` ignora). Montagem `ciopfs` (vs_files) exigida: depois de reboot, rodar `gen` de novo.
- pacote (`pack`): extrai `out/Win/chrome.7z` (lista oficial de arquivos do `chrome.release`), renomeia `Chrome-bin` para `aerographene/`, acrescenta `out/Win/fonts/` ao lado do `aerographene.exe` e gera `<dist>/<cpu>/aerographene-win-<cpu>.zip`, `mini_installer-<cpu>.exe` e `SHA256SUMS`. `<dist>` padrão: `~/aerographene-win/dist` (fora de `out/`, sobrevive à próxima build). O nome final do asset é dado na release. Referência de tamanho (D4, sem `-march`): `chrome.7z` 497 MB, `mini_installer.exe` 136 MB; o zip ainda não foi medido.
- `fonts\` entrou no `chrome.release` (`windows-branding.patch`, commit `fc39b55`): o `mini_installer` passa a instalar JetBrains Mono como o zip. Compilado, instalador não executado no Windows.
- correção skcms (`629b31b`): `/clang:-march=x86-64-v4` repetido após `/arch:AVX512` no skia (`skcms_TransformSkx`); os zips avx2 e avx1 saem de `build/win/build.sh` com `-march`.

```bash
# no Cezanne, com o repo na versão desejada e a árvore com a série aplicada
cd <repo>
build/win/build.sh avx2            # prepare + gn gen + ninja chrome mini_installer + pack
build/win/build.sh avx1            # depois, no mesmo out/Win
# passos isolados: build/win/build.sh <cpu> gen | ninja [alvos...] | pack
# env: AERO_WIN_SRC (padrão ~/aerographene-win/src4), AERO_WIN_TOOLCHAIN_DIR (~/win-toolchain),
#      AERO_WIN_DIST, AERO_WIN_JOBS (10)
```

## atualizar a árvore para a série atual

a árvore em uso é `~/aerographene-win/src4` (as `src`, `src2`, `src3` são tentativas antigas). Ela não tem `.aero-applied`: foi montada pelo script descartável `~/aerographene-win/mksrc4.sh` (hardlink da árvore do CI, links quebrados nos arquivos da série, `patch -R` da série do CI, série nova aplicada). Para uma série nova (ex.: v0.3 com versão 0.3.3):

1. esperar a build Linux da mesma série terminar (a árvore do CI passa a ter `.aero-applied` com ela).
2. montar uma árvore nova `src5` com o mesmo procedimento do `mksrc4.sh`, trocando `P` pela pasta `patches/` do repo na versão desejada (copiar o script; ele recusa destino existente). Não escrever através de hardlink.
3. conferir `--fuzz=0` da série e que nenhum arquivo tocado ficou com link compartilhado (o script imprime).
4. `AERO_WIN_SRC=~/aerographene-win/src5 build/win/build.sh <cpu>`. Se o disco não couber, mover `out/Win` da `src4` para a `src5` antes (`mv`, mesmo fs) e só então apagar a `src4`.

alternativa sem árvore nova: reverter na `src4` a série antiga (`patch -R` na ordem inversa, com a cópia da série usada na D4) e aplicar a nova; mais rápido, mas sem registro `.aero-applied` fica fácil errar a série de origem.

## branding Windows (D3d)

`aerographene/windows-branding.patch` (último da série) + `build/win/apply_assets.sh` (chamado por `prepare.sh`, passo 9):

- identidade (`install_static`): produto `aerographene`; dados do usuário em `%LOCALAPPDATA%\aerographene\User Data` (o tema já lê `%LOCALAPPDATA%\aerographene\theme.json`); registro `Software\aerographene`; AppUserModelID derivado de `base_app_id = aerographene` (`aerographene`, `aerographene.<perfil>`); ProgIDs `AerographeneHTM`/`AerographenePDF`; GUIDs de Active Setup e do ativador de toast próprios. CLSID/IID do elevation service e do tracing ficam (presos ao IDL).
- executável `aerographene.exe` (o BUILD, `reorder_imports`, as constantes de nome, o instalador e o mini_installer foram renomeados juntos); `chrome.dll` e `chrome_elf.dll` ficam. VERSIONINFO: nome, empresa, copyright do BRANDING e `OriginalFilename=aerographene.exe`.
- `.ico`: `branding/win/aerographene.ico` (16 a 256 px, gerado dos PNG de `branding/png` com ImageMagick) sobre `chromium.ico`, `chromium_doc.ico`, `chromium_pdf.ico` e `app_list.ico`. Incógnito e isolado seguem os do upstream.
- botões da barra de título: glifos do tema ativo (`AerographeneIconPainter`), iguais no Windows 10 e 11 (sem Mica nem cantos exclusivos do 11). Pixelized usa o bitmap 16x16 do tema.
- JetBrains Mono (SIL OFL 1.1, v2.304, Regular e Bold, `branding/fonts/jetbrains-mono/` com `OFL.txt`, sha256 do zip `6f6376c6...f7bbf`): fica em `<exe>\fonts\`, registrada como fonte privada do processo do navegador (`AddFontResourceExW`, `FR_PRIVATE`) quando o tema tem fonte (pixelized). Sem os arquivos, Consolas.
- theme-scheme: não existe `ThemeServiceWin`; o `ThemeService::GetBrowserColorScheme` da classe base (patch `theme-scheme`) já vale no Windows.
- limites: a fonte privada vale para a UI Views do processo do navegador; páginas web (renderers) e o WebUI não a enxergam (precisariam de `@font-face`). Se o Skia/DirectWrite do Chromium enxerga uma fonte `FR_PRIVATE` não foi verificado (não há Windows de teste). `mini_installer` e instalador (D5) ainda não foram compilados.

## confinamento (D3c)

vale para a vault de notas (`aero_notes/vault_reader.cc`) e para o repositório de temas (`aerographene_theme_repo.cc`), só no ramo `IS_WIN`; Linux sem mudança de comportamento. APIs desde o Vista (`GetFinalPathNameByHandleW`, `GetFileInformationByHandleEx`, `CompareStringOrdinal`), nada exclusivo do Windows 11.

- caminho percorrido componente a componente a partir da raiz; cada diretório fica aberto sem `FILE_SHARE_DELETE` até o fim da operação, então nada já conferido pode ser renomeado, apagado ou trocado por junção nesse intervalo.
- cada componente abre com `FILE_FLAG_OPEN_REPARSE_POINT` e é recusado se for reparse point name surrogate (`IsReparseTagNameSurrogate`: symlink, junção, ponto de montagem), tag lida por `GetFileInformationByHandleEx(FileAttributeTagInfo)`: mais estrito que o Linux, que segue symlink que fica dentro da vault. Placeholders de nuvem (OneDrive, Dropbox) são aceitos na vault (leitura de arquivo não hidratado não verificada). A raiz da vault (escolha do usuário) pode ser junção e é seguida uma vez; a pasta do repositório de temas não pode.
- vault: o caminho final (`GetFinalPathNameByHandleW`, `VOLUME_NAME_DOS`) de cada componente aberto tem de ser o caminho final do diretório pai segurado + `\` + nome. Assim, trocar o alvo de uma junção (inclusive a raiz) entre um passo e outro não redireciona a leitura: o componente aberto por caminho completo não prova ser filho do pai e é recusado.
- só arquivo comum em disco (`FILE_TYPE_DISK`, sem `DIRECTORY`/`DEVICE`), com teto de tamanho antes e durante a leitura.
- o nome final (`GetFinalPathNameByHandleW`, normalizado) tem de ser igual ao pedido sem caixa: apelido 8.3 (`NOTAS~1`) é recusado. Comparação sem caixa como o NTFS (`CompareStringOrdinal`).
- recusados antes de abrir: `:` (ADS), `<>"/\|?*`, controle, ponto ou espaço final, nomes reservados (`CON`, `PRN`, `AUX`, `NUL`, `COM0-9`, `LPT0-9`, também `¹²³`, `CONIN$`, `CONOUT$`, `CLOCK$`, com ou sem extensão e com espaço antes do ponto). No tema essas regras entram em `IsValidThemeName` (tema chamado `CON` é inválido no Windows).
- raiz/repositório precisa ser `X:\...`: UNC (`\\servidor\`), `\\?\` e `\\.\` recusados. Unidade de rede mapeada com letra não é detectada.
- listagem da vault enumera pelo handle aberto (`GetFileInformationByHandleEx(FileIdBothDirectoryInfo)`), não por caminho; reparse points name surrogate (tag em `EaSize`) e nomes que o Win32 não reabre iguais não aparecem; falha da enumeração diferente de `ERROR_NO_MORE_FILES` vira erro, não lista parcial.
- tema: instalar não substitui junção/arquivo com o nome do tema (`kIoError`); varredura e busca sem caixa ignoram reparse points. A base `%LOCALAPPDATA%\aerographene` acima do repositório não é conferida.
- não suportado no Windows: escrita da vault (salvar, criar, renomear, apagar), `kVaultWriteSupported = false`. Caminhos acima de `MAX_PATH` falham (sem `\\?\` interno).

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
9. ativos Windows (`apply_assets.sh`).
10. `.tlb` (MIDL) e `.bin` (mc) podados de `third_party/win_build_output` e `chrome/app/etw_events`: baixados do gitiles do Chromium na tag de `chrome/VERSION`, cada blob conferido pelo id git da listagem da árvore. No Linux o `midl.py`/`rc` só copiam esses arquivos.
11. `third_party/lzma_sdk/bin/host_platform/7za` (CIPD `infra/3pp/tools/7z/linux-amd64`, versão do `DEPS`), sha256 fixado por versão; usado pelo `mini_installer`.

arquivo novo sempre entra por temporário + `mv`, então nada é escrito através de hardlink do CI.

## problemas conhecidos

- `use_sysroot=false` (do `flags.windows.gn` do ungoogled) quebra o cross: vale também para a toolchain host Linux, que passa a pedir glib via `pkg-config` do host. O sysroot Debian da árvore serve.
- desde 14/10/2026 a série inteira aplica com `--fuzz=0` (com `--ignore-whitespace`, como o CI): `keyboard-shortcuts` e `crash-reporting-prefs` saíram da série e `ublock-install-as-component`/`toolbar-button-prefs` foram regenerados sobre a árvore com domain substitution. Sem `crash-reporting-prefs`, `chrome_crash_reporter_client_win.cc`, `chrome_elf.def` e `components/crash` ficam como no upstream; o upload continua desligado pelo `disable-crash-reporter` do ungoogled. Patches novos devem aplicar com `--fuzz=0`.
- `base_unittests` não compila (substituição de domínios do ungoogled em `rtl_unittest.cc`); só testes.
- `lld-link: warning: ignoring unknown argument '-Wl,--icf=all'`: flag ICF de ELF chegando ao link Windows; tratar em D4.
- o ninja do `out/Win` roda dentro do `aerographene-builder:v2` (node, tsc etc. do container; montar `~/aerographene-win` no mesmo caminho) com `--ulimit nofile=65536:65536`: com o limite padrão os objetos bluetooth WinRT falham com "Too many open files".
- binários pré-gerados podados no tarball (`.tlb` do MIDL, `.bin`/`.BIN` do mc em `third_party/win_build_output` e `chrome/app/etw_events`): repostos pelo passo 10 do `prepare.sh`. Se o ninja já tinha rodado a ação mc antes, a cópia em `out/Win/gen/.../eventlog_messages.*` fica velha: mover para fora e rodar o ninja de novo.
- deps só-Windows do `DEPS` (`microsoft_dxheaders`, `microsoft_webauthn`, `microsoft_multimedia_redirection`) vêm por git no commit exato do `DEPS`, fora do script (D4, 13/10/2026); `widevine/cdm/win` e `wix` são `src_internal` e não fazem falta ao `chrome`/`mini_installer`.

## resumo para agentes

- cross Linux→Windows no Cezanne: árvore própria por `cp -al` da árvore do CI, saída `out/Win`; não tocar `out/Default`, `out/Avx1` nem a árvore do CI; nunca escrever através de hardlink.
- preparo: `AERO_WIN_TOOLCHAIN_DIR=<dir do zip> build/win/prepare.sh <src>`; idempotente, confere hash de tudo, rodar de novo após reboot (ciopfs). Depois `gn gen out/Win` e `ninja`.
- args em `build/win/args.gn`; RLZ resolvido por `patches/aerographene/windows-disable-rlz.patch` (série única).
- série única Linux+Windows (dono, 13/10/2026); D3b feita (guardas `IS_LINUX || IS_WIN`, POSIX sob `#if`, ramo Win32 equivalente); próximas D3c–D3e no plano.
- testes D3b no Linux: alvo temporário `aero_ui_tests` (overlay, fora da série), 42/42; `TerminateKillsWholeGroup` exige init que colhe zumbis (`docker run --init`).
- D3d: branding no `windows-branding.patch` (nomes `aerographene`/`aerographene.exe`, dados em `%LOCALAPPDATA%\aerographene`, ícones do tema nos botões da janela, JetBrains Mono em `<exe>\fonts`); `.ico` e fontes entram por `build/win/apply_assets.sh`.
- notas no Windows: leitura confinada ativa (D3c, `kVaultReadSupported` true), escrita não (`kVaultWriteSupported` false → "unsupported"). Patch `aerographene/windows-confine.patch` (fim da série) concentra o ramo Win32 da vault e do repositório de temas; testes Windows em `vault_reader_win_unittest.cc` e `aerographene_theme_repo_unittest.cc` (`Windows*`), escritos mas não executados (sem Windows no host).
- D4: `ninja -C out/Win chrome mini_installer` passa (14/10/2026); falta smoke test no Windows 11. Ninja no container com `--ulimit nofile=65536:65536` e `flock /tmp/aero-win-ninja.lock`.
- build completa e pacote: `build/win/build.sh <avx2|avx1> [all|gen|ninja|pack]`; um `out/Win` por vez (disco), `-march` via bloco `# aerographene-win` na `compiler_cpu_abi` (só `is_win`); pacotes em `~/aerographene-win/dist/<cpu>/`. Árvore atual: `~/aerographene-win/src4`. Fontes faltam no `mini_installer` (`chrome.release`).
- o zip do toolchain é licenciado: nunca commitar, copiar para o repo ou publicar.
