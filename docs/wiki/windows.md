# windows (cross-compile no Cezanne)

estado do build do aerographene para Windows 11 x64 por cross-compile Linux→Windows no Cezanne (fatia D do `docs/PLANO-V0.3.md`). Ainda não existe navegador Windows: só a toolchain e um alvo pequeno foram provados.

## o que já funciona (13/10/2026)

- árvore separada `~/aerographene-win/src` (cópia por hardlink da árvore base do CI, sem `out/`), toolchain VS 2026 + SDK 10.0.28000 extraído e montado em sistema de arquivos insensível a caixa (ciopfs).
- `gn gen out/Win` com `target_os="win"` passa (36219 alvos), depois de dois ajustes (abaixo).
- `ninja -C out/Win base` e `base_unittests` compila com clang-cl; `crashpad_handler.exe` e `chrome_elf.dll` linkam com lld-link e `file` mostra `PE32+ ... x86-64, for MS Windows`. O Rust std para `x86_64-pc-windows-msvc` é compilado da fonte pela própria build. `base_unittests` não compila (teste quebrado pela substituição de domínios do ungoogled).

## o que não está no repositório

- o pacote do toolchain (`b353c3b35e.zip`, VS e SDK da Microsoft) é software licenciado: fica só em `~/win-toolchain` no host, nunca no git, artifact ou release.
- a árvore Windows, a lib fuse2 local e os binários `gn`/`ninja` copiados ficam em `~/aerographene-win` no host.

## como reproduzir no host

```bash
# 1. árvore: hardlink da base (exceto out/), mesmo sistema de arquivos
mkdir -p ~/aerographene-win/src && cd <árvore base>/src
for f in $(ls -A | grep -vx out); do cp -al "$f" ~/aerographene-win/src/; done

# 2. ciopfs (hook do DEPS que o tarball não rodou) + libfuse2 local, sem sudo
cd ~/aerographene-win/src
curl -fsSL -o build/ciopfs https://storage.googleapis.com/chromium-browser-clang/ciopfs/$(cat build/ciopfs.sha1) && chmod +x build/ciopfs
(cd ~/aerographene-win/deb && apt-get download libfuse2t64 && dpkg-deb -x libfuse2t64_*.deb ../root)

# 3. extrair o toolchain (hash esperado em build/vs_toolchain.py: 3bfcb536c8)
export LD_LIBRARY_PATH=$HOME/aerographene-win/root/lib/x86_64-linux-gnu
export DEPOT_TOOLS_WIN_TOOLCHAIN=1 DEPOT_TOOLS_WIN_TOOLCHAIN_BASE_URL=$HOME/win-toolchain GYP_MSVS_HASH_3bfcb536c8=b353c3b35e
python3 build/vs_toolchain.py update --force   # gera build/win_toolchain.json

# 4. runtime clang para Windows (cópia real de llvm-build antes, para não escrever em hardlink do CI)
mv third_party/llvm-build third_party/llvm-build.hardlink-ci && cp -a third_party/llvm-build.hardlink-ci third_party/llvm-build
(cd third_party/llvm-build/Release+Asserts && curl -fsSL https://commondatastorage.googleapis.com/chromium-browser-clang/Win/clang-win-runtime-library-llvmorg-24-init-3796-g20e97c4b-27.tar.xz | tar xJ)

# 5. clang-format (symlink do container), rc e lib podada do crate windows: ver lista de erros em docs/PLANO-V0.3.md seção D

# 6. gerar e compilar (args em docs/PLANO-V0.3.md seção D)
~/aerographene-win/bin/gn gen out/Win
nice -n 19 ~/aerographene-win/bin/ninja -C out/Win -j8 base chrome_elf third_party/crashpad/crashpad/handler:crashpad_handler
```

depois de reiniciar o host o ponto de montagem ciopfs some: rode o passo 3 de novo (com `LD_LIBRARY_PATH`).

## problemas conhecidos

- `use_sysroot=false` (do `flags.windows.gn` do ungoogled) quebra o cross: vale também para a toolchain host Linux, que passa a pedir glib via `pkg-config` do host. Não usar; o sysroot Debian da árvore serve.
- RLZ: o ungoogled força `enable_rlz_support = false`, mas `chrome/installer/setup` e `rlz:rlz_id` ainda dependem de `rlz_lib` no Windows. Ajuste local só na árvore Win; `setup/uninstall.cc` ainda inclui headers do RLZ e vai falhar ao compilar `setup`: precisa de patch Windows (o helium-windows/ungoogled-windows tem um) na série Windows (D3).
- arquivos com mtime no futuro fazem o ninja regenerar em laço; `touch` nos arquivos editados resolve.
- a árvore é hardlink da do CI: nunca editar arquivo no lugar (`>`, editor que trunca); só `sed -i`/cópia nova, que quebram o link. Patches aplicados no CI aparecem aqui também.

## resumo para agentes

- cross Linux→Windows no Cezanne: árvore `~/aerographene-win/src` (hardlink da base, sem `out/`), saída `out/Win`; não tocar `out/Default`/`out/Avx1` nem a árvore base.
- env: `DEPOT_TOOLS_WIN_TOOLCHAIN=1`, `GYP_MSVS_HASH_3bfcb536c8=b353c3b35e`, `DEPOT_TOOLS_WIN_TOOLCHAIN_BASE_URL=~/win-toolchain`, `LD_LIBRARY_PATH=~/aerographene-win/root/lib/x86_64-linux-gnu` para o ciopfs.
- faltas do tarball resolvidas à mão: `build/ciopfs`, libfuse2, `clang-win-runtime-library`, `buildtools/linux64-format/clang-format`, `build/toolchain/win/rc/linux64/rc`, `windows.0.52.0.lib` do crate `windows_x86_64_msvc`; `gn`/`ninja` copiados para `~/aerographene-win/bin`.
- args: os do Linux sem `use_sysroot`, `use_vaapi`, `rtc_use_pipewire`, `pgo_data_path`, `cc_wrapper`; mais `target_os="win"`, `chrome_pgo_phase=0`, `enable_rlz=false`.
- o zip do toolchain é licenciado: nunca commitar, copiar para o repo ou publicar.
- deps só-Windows vazias no tarball (dxheaders, webauthn, multimedia_redirection, widevine win, wix) devem bloquear o `chrome`.
- próximo: série Windows (D3, inclui patch RLZ do setup), depois `chrome` + `mini_installer` (D4).
