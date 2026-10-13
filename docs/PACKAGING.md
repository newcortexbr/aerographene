# empacotamento (Arch)

## initial_preferences

`packaging/arch/initial_preferences` é instalado em `/opt/aerographene/initial_preferences`; o Chromium o lê ao lado do binário.

- vale só para perfis novos; perfis existentes não mudam.
- valores atuais (confirmados nos patches):
  - `helium.completed_onboarding` = true (`patches/helium/core/onboarding-page.patch`). Pula a página de onboarding; `helium.services.user_consented` continua false.
  - `helium.browser.new_tab_next_to_active` = true (`open-new-tabs-next-to-active-tab-option.patch`; padrão do patch é false).
- botões da barra (`helium.browser.show_*_button`) já têm padrão true nos patches, então ficam de fora.

### não confirmados (fora do arquivo)

- memory saver: nenhum patch registra o pref; o nome upstream não foi verificado aqui.
- crash reporting: `helium.crash_reporting.mode` é pref de local state (`crash-reporting-prefs.patch`), não de perfil; não se sabe se `initial_preferences` o alcança. Valores do enum não verificados.
- smoke test no pacote ainda não feito: nenhuma build instalada validou que as chaves são aplicadas.

## wrapper /usr/bin/aerographene

`packaging/arch/aerographene-wrapper` (755) substitui o symlink; o binário real fica em `/opt/aerographene/aerographene`. O `.desktop` (`Exec=aerographene %U`) segue válido.

Flags, uma por linha, `#` e linhas vazias ignorados, lidas nesta ordem (a segunda vem depois, então prevalece em conflito):

1. `/etc/aerographene-flags.conf`
2. `${XDG_CONFIG_HOME:-$HOME/.config}/aerographene-flags.conf`

Depois executa o binário com as flags e os argumentos recebidos. Limite: uma flag por linha, sem expansão de aspas ou variáveis (`--flag=a b` vale literal).

Exemplos para isolar patches de desempenho:

```
# ~/.config/aerographene-flags.conf
--enable-features=NomeDaFeature1,NomeDaFeature2
--disable-features=NomeDaFeature3
```

Atenção: o Chromium usa só a última ocorrência de `--enable-features`/`--disable-features`; junte tudo numa linha por flag.

## o que o Chromium 154 já oferece (verificado em 154.0.8037.97)

- policies: o build não-Chrome lê `/etc/chromium/policies` (`components/policy/core/common/policy_paths.cc:21`); nenhum patch da série muda esse caminho. Policies `recommended/` servem para defaults que alcançam perfis existentes; o pacote ainda não instala nenhuma.
- `chrome://theme/colors.css?sets=ui,chrome` já existe (`chrome/browser/ui/webui/theme_source.cc:121`): páginas WebUI recebem as cores do ColorProvider como variáveis CSS. Um mixer de tokens de tema alimentaria essas páginas sem patch extra de CSS.
- atalhos customizáveis: não há suporte no `accelerator_table` do 154 para Linux; continuam exigindo patch.

## tema por manifest (teste rápido, sem rebuild)

`theming/chrome-themes/pixelized/manifest.json` traduz as cores do `theming/design-language/pixelized.md` para um tema Chrome (MV3, só `theme`). Para testar: `chrome://extensions` → modo desenvolvedor → carregar sem compactação → a pasta. Cobre frame, toolbar, abas, omnibox e NTP; não cobre raio, padding, fonte, dither, ícones nem a rampa de estado. Não testado em navegador ainda; aprovação visual é do dono.

## temas de teste do item 8 (sem rebuild)

- `theming/chrome-themes/nebula/`: gradiente nebuloso azul-preto com estrelas (`images/ntp.jpg`, gerada por IA, 1672×941) no frame e na nova aba.
- `theming/chrome-themes/high-contrast/`: preto alto contraste, destaque amarelo.
- cada pasta tem `manifest.json` (tema Chrome; carregar sem compactação em `chrome://extensions`) e `theme.json` (tokens do patch `theme-tokens`, copiar para `~/.config/aerographene/theme.json`). O `theme.json` cobre também páginas internas; o manifest cobre a imagem.
- não testados em navegador; aprovação visual é do dono.

## tema por tokens (`theme-tokens.patch`, sem rebuild)

O navegador lê no início `${XDG_CONFIG_HOME:-$HOME/.config}/aerographene/theme.json` (ou `--aerographene-theme=<path>`, que pode ir no `aerographene-flags.conf`). Mudou o arquivo, reinicie o navegador. Exemplo: `theming/chrome-themes/pixelized/theme.json`.

```
{"tokens": {"frame": "#0A0A0A", "toolbar": "#111111", "text": "#F2F2F2"}}
```

Cores `#RRGGBB` ou `#RRGGBBAA`. Tokens e ColorIds:

- `frame`, `frame_inactive`: `kColorFrameActive`, `kColorFrameInactive`.
- `toolbar`: `kColorToolbar`, fundo da aba ativa (frame ativo/inativo), `kColorBookmarkBarBackground`.
- `toolbar_text`: `kColorToolbarText`, `kColorBookmarkBarForeground`; `toolbar_icon`: `kColorToolbarButtonIcon`.
- `tab_text`: texto da aba ativa; `tab_background_text` e `tab_background_text_inactive`: texto da aba inativa com frame ativo/inativo; `tab_background`: fundo da aba inativa.
- `omnibox`, `omnibox_hover`, `omnibox_border`: `kColorLocationBarBackground[Hovered]`, `kColorLocationBarBorder`; `omnibox_text`, `omnibox_text_dim`: `kColorOmniboxText[Dimmed]`; `omnibox_results`, `omnibox_results_hover`: `kColorOmniboxResultsBackground[Hovered]`.
- `focus_ring`: `kColorFocusableBorderFocused`; `ntp`, `ntp_text`: `kColorNewTabPageBackground`, `kColorNewTabPageText`.
- `base`, `surface`, `text`, `accent`, `on_accent`: `kColorSysBase`, `kColorSysSurface`, `kColorSysOnSurface`, `kColorSysPrimary`, `kColorSysOnPrimary`; cores derivadas desses tokens também mudam.
- `text_dim`, `outline` (`webui-theme-colors.patch`): texto secundário e contorno de controle das páginas WebUI (`kColorSecondaryForeground`, `kColorSysOnSurfaceSubtle`…; `kColorSysOutline`, `kColorCheckboxOutline`…). Os tokens `base`, `surface`, `text`, `accent`, `on_accent`, `hover`, `separator`, `selection*`, `omnibox_border` e `omnibox_results_hover` também cobrem os ids derivados usados por histórico e configurações (fundo de página/card, link, controles, divisor, seleção).

Páginas internas (WebUI) usam `chrome://theme/colors.css`, gerado do ColorProvider, então também recebem os tokens. Desligar: `--disable-features=AerographeneThemeTokens`. Custo: uma leitura de arquivo pequeno (até 64 KiB) na primeira montagem de cores; medir contra a linha de base (regra de 2%). Não testado em navegador.

## nome e diretório de dados

Com `aerographene/branding.patch` e `aerographene/branding-version.patch`, `--version` mostra `aerographene 0.1.0 (Chromium 154.0.8037.97)` (`--product-version` mostra `0.1.0`; chrome://version e a página Sobre mostram `0.1.0 (Chromium 154.0.8037.97)` no lugar do número de versão) e o perfil padrão fica em `${XDG_CONFIG_HOME:-$HOME/.config}/aerographene` (cache em `~/.cache/aerographene`), separado de um Chromium instalado; perfis antigos em `~/.config/chromium` não migram sozinhos (copiar ou usar `--user-data-dir`). O wrapper exporta `CHROME_DESKTOP=aerographene.desktop`. Policies continuam em `/etc/chromium/policies` e as strings da UI passam a dizer "aerographene" pela troca de `build/branding_strings.py` (ver `docs/BUILD.md`, seção branding). A versão do produto (`AERO_VERSION` em `build/config.sh`, esquema v0.x.x; primeira = 0.1.0) é independente da do Chromium (154.0.8037.97), que segue em UA, extensões e `PRODUCT_VERSION`. `pkgver` do PKGBUILD = `AERO_VERSION`, tag `v${pkgver}`, e `_chromium` fica separado.

## PKGBUILD (`packaging/arch/`)

Fluxo de release (cada passo exige pedido explícito do dono: dispatch de workflow, tag, publicação):

1. `build.yml` (dispatch; input `cpu`: `avx2` padrão, `avx1`) gera o artifact `aerographene-linux-x86_64` (avx2) ou `aerographene-linux-x86_64-avx1`.
2. `smoke.yml` valida o artifact.
3. `release.yml` (inputs `run_id`, `tag` vX.Y.Z, `cpu`) roda `packaging/build-native.sh` e cria a release em draft (ou acrescenta ao draft existente da mesma tag; recusa release já publicada) com `aerographene-vX.Y.Z-<cpu>-linux.{tar.zst,pkg.tar.zst,deb,rpm}`, `SHA256SUMS` e `namcap-<cpu>.txt`. Um dispatch por cpu.
4. Dono publica o draft. Nada aqui publica.

O pacote Arch sai do próprio `packaging/arch/PKGBUILD`, rodado em container `archlinux:base-devel` sobre o tarball local (nada é baixado): `build-native.sh` copia o tarball para o nome que o `source=` espera e passa `AERO_PKGVER` (versão da tag) e `AERO_TARBALL_SHA256` (conferido pelo makepkg). Sem essas variáveis o PKGBUILD continua utilizável à mão: baixa o asset `aerographene-vX.Y.Z-avx2-linux.tar.zst` da release e usa `SKIP`.

`.deb` e `.rpm`: nfpm (`goreleaser/nfpm:v2.48.0` fixado por digest) com `packaging/nfpm.yaml`. O script extrai o `.pkg.tar.zst` (modos preservados), gera o manifesto de arquivos e anexa a lista de `contents:` ao cabeçalho do YAML, então os três formatos têm a mesma árvore. Dependências por distro estão em `overrides:` do `nfpm.yaml`. Sem scripts de pós-instalação: os triggers de MIME, desktop e ícones do dpkg/rpm já atualizam os caches (no Arch, hooks do pacman).

Teste: `packaging/test-install.sh <dir> <cpu> <versão>` instala e remove em containers `archlinux`, `ubuntu:24.04` e `fedora:latest`. Resultado de 13/10/2026 no Cezanne com o artifact da run 38303973794 (v0.1.0 + série v0.2): ver `docs/wiki/pacotes.md` e a seção "teste dos pacotes" abaixo.

Fontes: o `LICENSE` é cópia local da raiz (`packaging/arch/LICENSE`), pois makepkg resolve fontes relativas ao diretório do PKGBUILD e a URL raw do repo privado falharia sem token. Se o `LICENSE` da raiz mudar, recopie.

depends (conferidos com `readelf -d aerographene` do pacote 46f2308, sem executar):
- NEEDED diretos: nss (nspr/nss3/nssutil3/smime3), glib2 via gtk3, atk/at-spi2-core (atk, atk-bridge, atspi), dbus, cups, expat, libxcb, libxkbcommon, alsa-lib, mesa (gbm), libx11, libxext, libxcomposite, libxdamage, libxfixes, libxrandr, cairo, pango, systemd-libs (libudev). Foram listados explicitamente; `libxss` e `gtk3` ficam do original (gtk é carregado por dlopen, não aparece em NEEDED).
- `xdg-utils`: inferência (abrir links/arquivos externos); não verificado no binário.
- `ttf-liberation`: inferência (fontes padrão); `hicolor-icon-theme`: o ícone vai em `hicolor/`.
- nomes de pacotes Arch não conferidos com `pacman`/namcap.

Sandbox: a partir do branch `fix/branding-gaps`, `build/inner.sh` copia `out/Default/chrome_sandbox` (alvo GN `sandbox/linux:chrome_sandbox`, data_dep do `chrome`) para `chrome-sandbox` no tarball (aviso, não erro, se faltar) e o PKGBUILD instala com `install -m4755` (root:root via fakeroot). O Chromium procura `<dir do binário>/chrome-sandbox` e só usa o helper setuid se o dono e o modo estiverem certos; sem ele, ou em tarballs antigos, o sandbox depende de user namespaces não privilegiados do kernel. O portablelinux não empacota o helper. Não testado em execução.

StartupWMClass: `aerographene` (nome do desktop file; padrão do binário desde `patches/aerographene/branding-desktop.patch`, ver abaixo). NÃO verificado: o app_id/WM_CLASS real só aparece com a janela aberta. Verificar: `xprop WM_CLASS` (X11), `swaymsg -t get_tree` ou `hyprctl clients` (Wayland); ajuste o valor se diferir.

Pendências:
- fontes auxiliares do PKGBUILD com `SKIP` (só o tarball tem sha256, passado por `build-native.sh`).
- ícone só 48x48 (`product_logo_48.png`, placeholder).
- nenhuma tag existe no repositório.
- `namcap` rodou (13/10/2026, `namcap-<cpu>.txt` na release): sem erro que bloqueie; avisos esperados de dependências não declaradas (libs Qt dos `libqt5_shim`/`libqt6_shim`, carregados por dlopen e opcionais) e setuid do `chrome-sandbox`.

### teste dos pacotes (13/10/2026)

Cezanne, containers, entrada: artifact da run 38303973794 (`aerographene-0.1.0-...-x86_64_linux.tar.zst`, v0.1.0 + série v0.2), pacotes gerados como `0.3.0` avx2 por `build-native.sh`; `packaging/test-install.sh` em `archlinux`, `ubuntu:24.04` e `fedora:latest`:

- instala (dependências resolvidas pelo gerenciador), `chrome-sandbox` 4755 root, `ldd chrome` sem faltas, `aerographene --version` = `aerographene 0.1.0 (Chromium 154.0.8037.97)`, `--headless --dump-dom about:blank` devolve DOM, remove sem sobrar arquivo do pacote.
- observado: ao rodar como root o navegador cria `/opt/aerographene/extensions` (vazio), que sobra após a remoção em qualquer formato; o teste avisa e não reprova.
- não testado: avx1 (sem artifact), interface gráfica, Debian/Ubuntu antigos, `pacman -U` fora de container limpo.

## ícones e identidade visual (`branding/`)

- fonte: `branding/make.py` gera os SVGs (`aerographene-mark.svg` com `currentColor`, `-black`, `-white`, e `aerographene-icon.svg`); `branding/render.sh` renderiza `branding/png/` (7 tamanhos 16–256 do ícone e do símbolo, mais 22 do símbolo, `aerographene-icon.ico` e `logo-name-22-*`). Usa `rsvg-convert` e ImageMagick (`magick`); os PNGs gerados ficam versionados porque o build não depende dessas ferramentas.
- símbolo: quadrado 90×90 com o canto superior esquerdo cortado a 30° (único ângulo); a aba cortada fica deslocada 9 unidades na normal do corte (vão fixo). A lasca do "A" do PNG antigo não existe mais.
- ícone do app: fundo `#060b18` (derivado de `--bg` `#04070e`, um pouco mais claro para destacar em painéis escuros), raio 22%, contorno `#8cb4ff` a 22%, símbolo em `--accent` `#6cb6ff`. Motivo: o azul é o único sinal de identidade da linguagem de design; azul sobre quase-preto tem contraste alto, o que sustenta 16 px. Símbolo a 72% da área.
- `branding/src/logo-{black,white}.png`: cópia do logotipo raster provisório (`theming/design-language/assets/`); alimenta `product_logo_name_22*` (escalado para caber em 97×22 / 194×44, centralizado).
- legibilidade (renderizações vistas, 16/32/128 px): em 128 e 32 o corte e o vão são nítidos; em 16 o vão vira uma linha de ~1 px antialiasada, ainda visível, e a silhueta (quadrado com canto cortado, azul sobre escuro) se reconhece. Não testado em tema claro de bandeja nem em lançador real.

### substituição no build

`build/apply_branding_assets.sh <src> [branding]` roda em `build/inner.sh` depois dos patches/domain substitution e antes do `gn gen`. Copia só se o conteúdo mudou (mtime preservado) e aborta se um destino sumiu ou não tem o tamanho do upstream 154.0.8037.97. Não é patch: PNG binário não entra na série. Os arquivos não são tocados por patches, então o re-patch incremental não os reverte; a recriação da árvore os reaplica.

Mapa (destino em `chrome/app/theme/`, tamanho original conferido na tag 154.0.8037.97; lidos por `chrome_unscaled_resources.grd`, `theme_resources.grd`, `chrome/BUILD.gn:2016` e `chrome/installer/linux/BUILD.gn:404-410`):

- `chromium/linux/product_logo_{24,48,64,128,256}.png` (mesmos tamanhos); 64/128/256 são `IDR_PRODUCT_LOGO_*`, 48 vai para `out/Default/product_logo_48.png`.
- `chromium/product_logo_{16,24,48,64,128,256}.png`: `*_SHORTCUTS` e caminho não-Linux.
- `chromium/product_logo_22_mono.png` (22×22, `IDR_STATUS_TRAY_ICON`): símbolo branco.
- `default_100_percent/chromium/{,linux/}product_logo_{16,32}.png` (16², 32²) e `default_200_percent/chromium/product_logo_{16,32}.png` (32², 64²): `IDR_PRODUCT_LOGO_16/32`.
- `default_{100,200}_percent/chromium/product_logo_name_22{,_white}.png` (97×22 / 194×44): `IDR_PRODUCT_LOGO_NAME_22[_WHITE]`.
- `chromium/product_logo.svg` (256×256): `IDR_PRODUCT_LOGO_SVG`, substituído pelo SVG do ícone.
- `components/resources/default_{100,200}_percent/chromium/product_logo{,_white}.png` (171×32 / 342×64, `IDR_PRODUCT_LOGO[_WHITE]`, cabeçalho de chrome://version) pelo logotipo com nome (`logo-name-32-{black,white}-{1,2}x.png`, gerado de `branding/src/logo-*.png` por `render.sh`), e `favicon_product.png` (16² / 32², `IDR_PRODUCT_FAVICON`) pelo ícone.
- `ui/webui/resources/images/chrome_logo_dark.svg` (24×24): anel branco do Chrome que o `cr-toolbar` (history, downloads, extensions, settings) mostra no tema escuro; trocado por `aerographene-mark-white.svg`. No tema claro o `cr-toolbar` usa `chrome://theme/current-channel-logo` = `IDR_PRODUCT_LOGO_32`, já no mapa.

Fora do mapa: `product_logo_animation.svg`; `win/` (`*.ico`, `tiles/`) e `mac/` (`app.icns`, `AppIcon.appiconset`), que não entram numa build Linux; `chromeos/`. `branding/png/aerographene-icon.ico` já está pronto (16–256) para uma eventual substituição de `win/chromium.ico`, mas esse arquivo tem só 16×16 originalmente e não foi mapeado.

### pacote e desktop entry

- `build/inner.sh` põe `icons/hicolor/<n>x<n>/apps/aerographene.png` (16, 24, 32, 48, 64, 128, 256) no tarball; o `PKGBUILD` instala cada um em `/usr/share/icons/hicolor/<n>x<n>/apps/aerographene.png`. Tarballs gerados antes desta mudança não têm `icons/` e quebram o `package()`.
- `aerographene.desktop` mantém `Icon=aerographene`.

### WM_CLASS / StartupWMClass

`shell_integration_linux.cc:426-468` (154.0.8037.97) deriva a classe de `chrome::GetDesktopName()` (`chrome/common/channel_info_posix.cc:121-153`): `CHROME_DESKTOP` se definida, senão o padrão embutido. `aerographene-wrapper` exporta `CHROME_DESKTOP=aerographene.desktop`; sem o wrapper (binário executado direto) o padrão do upstream era `chromium-browser.desktop` (WM_CLASS `chromium-browser`/`Chromium-browser`, observado no teste do pacote 0.1.0). `patches/aerographene/branding-desktop.patch` troca o padrão para `aerographene.desktop` e o ícone de `GetIconName()` para `aerographene`, então com ou sem wrapper o nome da instância é `aerographene` (igual ao `StartupWMClass=aerographene`; o Wayland usa o mesmo valor como app_id) e a classe X11 é `Aerographene`. `--class` não é necessário. Não verificado em execução (sem build): conferir com `xprop WM_CLASS` / `hyprctl clients` e, se o shell casar só pela classe, trocar para `StartupWMClass=Aerographene`.
