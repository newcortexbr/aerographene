# pacotes

como instalar o aerographene (Arch, Debian/Ubuntu, Fedora ou tarball) e como os pacotes são gerados.

## o que a release traz

cada release (draft até o dono publicar) tem, por alvo de CPU, quatro arquivos com o mesmo conteúdo:

- `avx2-linux--aerographene-vX.Y.Z.tar.zst`: tarball compilado (x86-64-v3, o padrão).
- `avx2-arch--aerographene-vX.Y.Z.pkg.tar.zst`: pacote Arch.
- `avx2-debian--aerographene-vX.Y.Z.deb`: Debian/Ubuntu.
- `avx2-fedora--aerographene-vX.Y.Z.rpm`: Fedora e derivados.
- `SHA256SUMS` cobre todos; `avx2-arch--namcap.txt` é o relatório do `namcap` sobre o pacote Arch.

para CPUs sem AVX2 (Ivy Bridge, Sandy Bridge) existe o mesmo conjunto com `-avx1-` no nome (build `-march=ivybridge`, [ADR 0009](../adr/0009-build-ivy-bridge.md)). Os dois alvos usam o mesmo nome de pacote: instale só um.

## instalar

```bash
sha256sum -c SHA256SUMS --ignore-missing

# Arch
sudo pacman -U avx2-arch--aerographene-vX.Y.Z.pkg.tar.zst
# Debian / Ubuntu (apt resolve as dependências)
sudo apt install ./avx2-debian--aerographene-vX.Y.Z.deb
# Fedora
sudo dnf install ./avx2-fedora--aerographene-vX.Y.Z.rpm
```

remover: `sudo pacman -R aerographene`, `sudo apt remove aerographene` ou `sudo dnf remove aerographene`. Seu perfil em `~/.config/aerographene` não é tocado.

## o que é instalado

- `/opt/aerographene/`: o navegador (`chrome`, `aerographene` -> `chrome`, recursos, `locales`), `chrome-sandbox` com setuid root (4755), `initial_preferences`.
- `/usr/bin/aerographene`: wrapper que lê flags de `/etc/aerographene-flags.conf` e de `~/.config/aerographene-flags.conf` (uma por linha).
- `/usr/share/applications/aerographene.desktop` e `aerographene-theme-import.desktop` (abre `.aerotheme`), `/usr/share/mime/packages/aerographene.xml`, ícones em `hicolor/<n>x<n>/apps/` e `mimetypes/`, `/usr/share/licenses/aerographene/LICENSE`.
- dependências por distro (nomes em `packaging/arch/PKGBUILD` e `packaging/nfpm.yaml`): bibliotecas GTK 3, NSS, ALSA, CUPS, X11, Mesa/GBM etc.; fontes sugeridas: JetBrains Mono para o tema pixelized.

## como são gerados

nada é recompilado: tudo parte do tarball da build.

1. `packaging/build-native.sh <tarball> <avx2|avx1> <X.Y.Z> [saída]` roda `makepkg` com `packaging/arch/PKGBUILD` num container `archlinux:base-devel` (usuário não-root). O PKGBUILD é o mesmo usado a mão; o tarball local entra como fonte (sem download) e seu sha256 é conferido.
2. A árvore do `.pkg.tar.zst` vira a lista de arquivos do nfpm (`packaging/nfpm.yaml`, imagem `goreleaser/nfpm` fixada por digest): `.deb` e `.rpm` saem com os mesmos arquivos, modos, wrapper, desktop, MIME e ícones.
3. `.github/workflows/release.yml` (dispatch do dono, inputs `run_id`, `tag`, `cpu`) chama o script e cria ou completa a release em draft. Nunca publica.
4. `packaging/test-install.sh <dir> <cpu> <X.Y.Z>` instala, roda `aerographene --version`, confere `ldd` e remove em containers `archlinux`, `ubuntu:24.04` e `fedora`.

## limites conhecidos

- o `.deb` e o `.rpm` foram testados em Ubuntu 24.04 e Fedora atual; outras versões (Debian 12, Ubuntu 22.04, openSUSE) não.
- `chrome-sandbox` setuid: sem ele o Chromium usa user namespaces do kernel.
- sem repositório apt/dnf/pacman: atualização é baixar o pacote novo.
- GUI não testada nesses containers (só `--version` e `--headless`).

## resumo para agentes

- assets por cpu: ``<avx2|avx1>-<linux|arch|debian|fedora>--aerographene-vX.Y.Z.<tar.zst|pkg.tar.zst|deb|rpm>`` + `SHA256SUMS`; sempre draft.
- fonte única da árvore instalada: `packaging/arch/PKGBUILD` (+ wrapper, desktop, MIME, `initial_preferences`); deb/rpm derivam do pacote Arch via `packaging/nfpm.yaml` (cabeçalho e dependências; `contents:` é gerado). Mudou arquivo instalado: mude só o PKGBUILD.
- dependências de deb/rpm ficam em `overrides` do `nfpm.yaml`; Arch no `depends` do PKGBUILD.
- gerar: `bash packaging/build-native.sh <tar.zst> <cpu> <X.Y.Z> <dir>` (precisa de docker e rede); testar: `bash packaging/test-install.sh <dir> <cpu> <X.Y.Z>`.
- não rodar na máquina local de benchmark; usar o Cezanne (`/tmp/aero-pkg`) com nenhum build ativo.
- `PKGBUILD` lê `AERO_PKGVER` e `AERO_TARBALL_SHA256` do ambiente; sem eles baixa o asset `avx2` da release.
- `release.yml` roda em `ubuntu-latest` (não executa código de fork; ADR 0004).
