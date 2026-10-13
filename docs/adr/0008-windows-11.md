# build para Windows 11 (v0.3)

Status: proposto em 12/10/2026. Nada implementado, nenhum build disparado. Investigação só de leitura (fontes abaixo; `src` do Cezanne lido por ssh).

Escopo do SCOPE.md v0.3: Windows 11, x64, processo `aerographene.exe` (item 9). Este ADR escolhe como compilar, o que da série precisa de versão Windows e como empacotar. ARM64 fica fora. Windows 10 entrou em 13/10/2026 (ver adendo).

## fatos verificados

- Requisitos oficiais do Chromium no Windows (`main`): x86-64 com 8 GB de RAM (mais de 16 GB muito recomendado), 100 GB livres em NTFS, Windows 10 ou mais novo, Visual Studio com workload "Desktop development with C++", Windows 11 SDK e Debugging Tools. O SDK exigido é 10.0.28000.2270 em `main`; a versão do 154 não foi conferida. https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/windows_build_instructions.md
- ungoogled-chromium-windows (https://github.com/ungoogled-software/ungoogled-chromium-windows) não faz cross-compile: o `build.py`/`package.py` rodam em Windows nativo (Developer Command Prompt for VS, Python 3.11+, 7-Zip, Git), baixam clang/rust/node/ninja para Windows (`downloads.ini`) e geram zip + instalador. O CI usa `runs-on: windows-2022` hospedado do GitHub, em estágios encadeados (`build-x64.yml` → `reusable-build.yml` → ação `stage`, com `--ci`), porque um job tem limite de tempo; o estágio seguinte retoma `out/Default`. https://raw.githubusercontent.com/ungoogled-software/ungoogled-chromium-windows/master/.github/workflows/reusable-build.yml
- flags Windows do ungoogled (`flags.windows.gn`): `target_cpu="x64"`, `is_official_build=true`, `chrome_pgo_phase=2` (o `build.py` força `0` no modo tarball), `use_sysroot=false`, `ffmpeg_branding="Chrome"`, `enable_rust=true`, `symbol_level=0`. https://raw.githubusercontent.com/ungoogled-software/ungoogled-chromium-windows/master/flags.windows.gn
- helium-windows (https://github.com/imputnet/helium-windows, GPL-3.0) é derivado do ungoogled-windows. Os builds oficiais rodam em runners pagos de terceiros (patrocínio da Depot, "dentro de horas, não dias"); `package.py` monta instalador NSIS (`installer/helium.nsi`, entradas `mini_installer.exe`, `setup.exe`, `helium.packed.7z`) e zip. Usa siso (`use_siso=true`) e `symbol_level=1`. https://raw.githubusercontent.com/imputnet/helium-windows/main/package.py e `flags.windows.gn` no mesmo repo.
- Cross-compile Linux→Windows é suportado pelo Chromium (`target_os="win"`), mas com ressalvas: quem não é do Google precisa empacotar o SDK numa máquina Windows (`package_from_installed.py`) e apontar `DEPOT_TOOLS_WIN_TOOLCHAIN_BASE_URL`/`GYP_MSVS_HASH_*`; arquivos `.asm` são stubados e o Crashpad não reporta crash; usa clang-cl. https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/win_cross.md
- Nada disso está no fluxo atual: `build/inner.sh` usa o portablelinux (Docker, sysroot Linux), e o `-march` entra só em `current_cpu == "x64" && is_linux` (`build/config/compiler/BUILD.gn:1346` no `src` do Cezanne).
- Série atual (112 linhas em `patches/series`), pontos específicos de Linux, conferidos com `grep` nos patches:
  - `helium/linux/use-default-theme.patch` (`ui/linux/linux_ui_factory.cc`): descartar no Windows.
  - `aerographene/process-names.patch`: todo sob `BUILDFLAG(IS_LINUX)`; no Windows não faz nada (coerente com o SCOPE).
  - `aerographene/branding-desktop.patch`: `.desktop`, WM_CLASS, `shell_integration_linux.cc`; no Windows precisa do equivalente (AppUserModelID, ProgID/registro, ícone do exe).
  - `aerographene/branding.patch` toca `chrome_paths_linux.cc` (diretório de dados); no Windows o nome vem do `install_static` (marca, caminho em `%LOCALAPPDATA%`, chaves de registro) e exige parte nova.
  - `aerographene/theme-scheme.patch` toca `theme_service_aura_linux.cc`; no Windows a escolha do esquema escuro passa por outro caminho de tema.
  - `aerographene/theme-icons-window.patch` troca os glifos de minimizar/maximizar/fechar de `OpaqueBrowserFrameView`/`FrameViewLinux`. O Windows usa outro frame (`browser_frame_view_win.cc`/glass); `helium/ui/layout/vertical.patch` já mexe em `browser_frame_view_win.cc`, então há base, mas os botões "na toolbar, sem barra extra" (decisão do dono) precisam de trabalho no frame Windows.
  - `helium/core/crash-reporting-prefs.patch` já toca `chrome_crash_reporter_client_win.cc` (o Helium nasceu multiplataforma).
  - O restante (spaces, sidebar/pinned, command bar, peek, split, dado frio, ublock) é Views/WebUI/componentes e, em princípio, independe de SO. Hipótese até compilar.

## hipóteses (não verificadas)

- Tempo: o primeiro build completo no Windows é da ordem do Linux (cerca de 8 h no Cezanne); em runner hospedado de 4 vCPU seria bem mais, em vários estágios. Não medido.
- Disco: ~100 GB livres como no doc do Chromium; o `src` Linux do Cezanne ocupa 26 GB com `out/Default` de 16 GB (medido), mas Windows com símbolos/PDB e SDK pesa mais.
- Limites e preço de runners hospedados para repositório privado (minutos, multiplicador do Windows) não foram consultados.
- Redistribuir o SDK/VS empacotado (cross) pode ter restrição de licença da Microsoft: conferir antes.
- Que `chrome.exe` → `aerographene.exe` e a marca no `install_static` bastem com branding.patch + patch novo: não verificado; o Helium renomeia para `helium.exe` e serve de referência.

## opções

1. Runner Windows nativo, base helium-windows/ungoogled-windows. Prós: caminho testado por dois projetos, mesmo toolchain do upstream, gera instalador/zip, PGO oficial Windows (`chrome_pgo_phase=2`; existência do perfil para 154 a conferir). Contras: segundo pipeline e manutenção de patches `windows/` por versão (clang, rust, node, SDK); precisa de máquina Windows. Custo: alto na montagem (dias), build completo de horas em máquina boa.
   - 1a. VM/WSL-fora, ou Windows instalado numa das máquinas do dono como runner self-hosted (`windows`, `intense`). Prós: cache persistente, custo zero em minutos. Contras: ocupa a máquina; no Cezanne conflita com o Linux (mesmo host, exclusão mútua do ADR 0004); o Comet Lake (4 threads) é lento demais.
   - 1b. Runner hospedado do GitHub (`windows-2022`) em estágios, como o ungoogled. Prós: sem hardware. Contras: repositório privado consome minutos; estágios e cache de `out/` entre jobs; só o dono dispara (ADR 0004 continua valendo).
2. Cross-compile no Cezanne (Linux→Windows, clang-cl + SDK empacotado). Prós: um host, ccache e ninja já existentes, sem Windows no runner. Contras: caminho não usado por ungoogled nem Helium; Crashpad stubado, SDK precisa de uma máquina Windows uma vez e de licença a conferir; o `inner.sh` e a árvore portablelinux (sysroot, tarball podado) não têm o lado Windows; risco alto e `out` separado (ADR 0009 trata disco).
3. Não fazer build Windows; usar os binários do Helium. Prós: zero custo. Contras: perde a série própria; descartado, é o objetivo do escopo.

## recomendação

Opção 1a: workflow separado (`build-windows.yml`, `workflow_dispatch` apenas), runner self-hosted Windows 11 próprio, base helium-windows (GPL-3.0, mesmo Chromium 154.0.8037.97 do Helium 0.18.3.1) em vez do ungoogled-windows, por já refletir a árvore do Helium que a série usa. Se não houver máquina Windows disponível, 1b com estágios como fallback. Cross-compile (opção 2) só se o dono exigir um host único, após prova de conceito.

Empacotamento: zip portátil primeiro (menor risco, análogo ao `.tar.zst`); instalador NSIS do Helium só depois, na mesma v0.3 se o zip validar. Sem auto-update, como no Linux. Windows 11 x64 apenas.

## passos para executar na v0.3

1. Decidir a máquina Windows (dono) e confirmar disco ≥150 GB livre, RAM ≥16 GB.
2. Montar o ambiente: VS com C++, SDK da versão exigida por 154 (conferir `build/vs_toolchain.py`), Python, 7-Zip, Git, Developer Mode, `LongPathsEnabled`.
3. Clonar helium-windows na tag do 154.0.8037.97 e reproduzir o build deles sem nossa série (fumaça: `chrome.exe` abre). Registrar tempo e disco reais; isso fecha as hipóteses acima.
4. Portar a série: aplicar `patches/series` em cima; separar em `patches/series` (comum) e uma lista Windows que exclui `helium/linux/use-default-theme`, `process-names`, `branding-desktop` e troca `branding`, `theme-scheme`, `theme-icons-window` por versões Windows. Pré-checagem estática da AGENTS.md antes de qualquer build.
5. Patches novos: marca no `install_static` e nome `aerographene.exe`, ícone/AppUserModelID, botões da janela no frame Windows.
6. `flags.windows.gn` próprio: ThinLTO, ICF, PGO com perfil Windows, `symbol_level=0`; `-march`/CPU conforme ADR 0003 (x86-64-v3 só se o alvo for Cezanne/Comet Lake; Win11 exige hardware moderno).
7. Smoke test no Windows 11 real (abre, perfil novo, spaces, uBlock) e `docs/BASELINE.md` separado para Windows (não comparar com Linux).
8. Atualizar `docs/BUILD.md`, `patches/README.md` e o ADR 0004 (segundo runner, exclusão mútua) quando a decisão for aceita.

Risco aceito: segundo pipeline dobra a manutenção a cada rebase de versão do Chromium.

## adendo 13/10/2026: Windows 10 e 11

Decisão do dono: suportar Windows 10 e 11 x64, por terem a mesma base. Revoga "Windows 10 fica fora" deste ADR e o "Windows 11 apenas" do empacotamento. Regra: não depender de nada exclusivo do Windows 11 (APIs, manifesto, instalador, requisitos de hardware). Piso Windows 10 1809, por causa do ConPTY no terminal. Teste real só no Windows 11; Windows 10 fica suportado, não testado. O `-march` continua pelo ADR 0003, sem supor hardware de Windows 11.
