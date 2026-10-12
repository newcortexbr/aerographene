<p align="center">
  <img src="branding/ascii/wordmark-simple.svg" alt="aerographene" width="720">
</p>

<p align="center">
  <a href="https://github.com/newcortexbr/aerographene/commits/main"><img alt="commits" src="https://img.shields.io/github/commit-activity/t/newcortexbr/aerographene?label=commits&color=8a8f98&style=flat-square"></a>
  <a href="https://github.com/newcortexbr/aerographene/releases/latest"><img alt="release" src="https://img.shields.io/github/v/release/newcortexbr/aerographene?color=c9cdd3&style=flat-square"></a>
  <img alt="Linux x86-64-v3" src="https://img.shields.io/badge/Linux-x86--64--v3-2ea043?logo=linux&logoColor=white&style=flat-square">
  <img alt="Windows 11 coming soon" src="https://img.shields.io/badge/Windows%2011-coming%20soon-d29922?logo=windows11&logoColor=white&style=flat-square">
  <img alt="AVX1-only coming soon" src="https://img.shields.io/badge/AVX1--only-coming%20soon-d29922?style=flat-square">
  <a href="LICENSE"><img alt="GPL-3.0" src="https://img.shields.io/badge/license-GPL--3.0-8a8f98?style=flat-square"></a>
</p>

<p align="center">
  <img src="docs/img/default-sidebar.webp" alt="default theme, sidebar" width="49%">
  <img src="docs/img/default-topbar.webp" alt="default theme, topbar" width="49%">
  <img src="docs/img/pixelized-sidebar.webp" alt="pixelized theme, sidebar" width="49%">
  <img src="docs/img/pixelized-topbar.webp" alt="pixelized theme, topbar" width="49%">
</p>

# AEROGRAPHENE

## EN
Ungoogled-Chromium-based browser with a focus on not getting much heavier (on the disk) over time, with startup times aimed at similar/better than Helium.
V0.1 brings custom theming and general use with pinned items similar to Arc/Zen, coupled with folders to hide and show groups of pinned items. Also comes with a centered command bar and a very different design.
By v0.3, I aim to have it fully compatible with x86-v3 (current default) and x86-v2 for use in machines lacking AVX2, and to integrate Obsidian and terminals directly inside workspaces in the browser.

Made by dashwr, with giant help from Sonnet 5.5, Opus 5.5, 6.1 Sol and 6 Luna. Don't trust the code? Check it out yourself, it's licensed under GPL-3.0.

## PT
Navegador baseado em Ungoogled-Chromium, focado em não ficar muito mais pesado (no disco) com o tempo, e com tempo de início mirado em ser semelhante/melhor que o Helium.
V0.1 traz tematização personalizada e uso geral com itens fixados parecido com Arc/Zen, junto de pastas para mostrar e esconder grupos de itens fixados. Também acompanha uma barra de comando centralizada e um design diferentão.
Até a v0.3, quero ter compatibilidade total com x86-v3 (padrão atual) e x86-v2 para uso em máquinas sem AVX2, e integrar Obsidian e terminais diretamente dentro de áreas-de-trabalho no navegador.

Feito por dashwr, com ajuda gigante de Sonnet 5.5, Opus 5.5, 6.1 Sol e 6 Luna. Não confia no código? Verifique ele, é licensiado sob GPL-3.0.

### Content above was 100% human-written. Content below will be updated constantly by AI to reflect the browser's real roadmap and current capabilities, together with instructions and documentation links.

## roadmap

- ✅ v0.1: Linux x86-64-v3, released as [v0.1.0](https://github.com/newcortexbr/aerographene/releases/tag/v0.1.0)
  - ✅ sidebar with a pinned grid, folders and drag-to-folder
  - ✅ topbar mode with a pinned row and folders
  - ✅ centered command bar with per-type icons
  - ✅ peek (popups and `target=_blank`) and split view
  - ✅ spaces as profiles, one window each
  - ✅ two built-in themes: default and pixelized
  - ✅ cold data for history, favicons, sessions and downloads (30 days)
  - ✅ uBlock Origin (MV2) built in and on by default; Arc importer for pinned items
  - ✅ readable process names, `.tar.zst` release and PKGBUILD
  - ✅ baseline: faster startup than Helium, same-or-lower memory ([BASELINE](docs/BASELINE.md))
- 🚧 v0.2
  - ✅ internal pages (history, settings, security) follow the theme
  - ⬜ real-use test of spaces, command bar, peek and split view
  - ⬜ cold data for site storage
  - ⬜ theme picker in the UI
- ⬜ v0.3
  - ⬜ Windows 11 ([ADR 0008](docs/adr/0008-windows-11.md))
  - ⬜ x86-64-v2 + AVX build for CPUs without AVX2 ([ADR 0009](docs/adr/0009-build-ivy-bridge.md))
  - ⬜ Obsidian and terminals inside workspaces
- ⬜ later: Google Sync with own API keys ([ADR 0006](docs/adr/0006-google-sync-com-chaves-proprias.md))

## docs

the wiki lives in [`docs/wiki/`](docs/wiki/), in pt-BR.

- [temas](docs/wiki/temas.md): how themes load (built-in theme, `theme.json` tokens, extension themes), where to change them and how to make your own. Ends with a dense spec you can paste into your AI agent so it writes a valid theme for you.

for builders: [scope](docs/SCOPE.md), [build](docs/BUILD.md), [packaging](docs/PACKAGING.md), [decisions](docs/adr/), [patch origins](patches/README.md).

## thanks

aerographene stands on the shoulders of three projects. Thank you, immensely, to everyone who works on them.

### ungoogled-chromium

the base. Every aerographene build is ungoogled-chromium plus our patch series.

- taken as is: removal of Google services, telemetry and variations; `disable-ai`; Manifest V2 support (which keeps full uBlock Origin alive).
- changed: product name, icon and data directory (`~/.config/aerographene`); x86-64-v3 compiler target with ThinLTO and PGO; everything in the series below sits on top.

### Helium

the source of most of our ported work: 42 of the patches in [`patches/series`](patches/series) come from Helium.

- taken: infinite tab freezing, memory saver on by default, lazy session restore, low-power framerate flag, uBlock Origin installed as a component, vertical and compact layouts, centered address bar, split view, side panel, tab context menus, MRU tab cycling, keyboard shortcuts, Arc importer, onboarding and the custom internal-page protocol.
- changed: hunks rebased onto Chromium 154 without the rest of Helium's tree; `helium://` shown as `aerographene://`; the vertical layout trimmed (no tab search host, no corner refs) and given a compact toolbar width; uBlock defaults reconfigured and its toolbar icon themed; Helium's own services and sync left out.

### Thorium

the performance yardstick and the model for a few decisions.

- taken: Thorium is part of our benchmark baseline ([BASELINE](docs/BASELINE.md)); its approach of shipping builds with the maintainer's own Google API keys is the plan for sync ([ADR 0006](docs/adr/0006-google-sync-com-chaves-proprias.md)).
- changed: no Thorium code is in the tree; the sync plan adapts its key approach to an ungoogled base, which first needs a login test.

also thanks to Brave, for the three patches behind the Arc importer and MRU tab cycling.
