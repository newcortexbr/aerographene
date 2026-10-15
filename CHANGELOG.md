# Changelog

Newest first. Releases: https://github.com/newcortexbr/aerographene/releases

## v0.3.4 (unreleased, branch `v0.3.4`)

- each built-in theme draws its own active-tab marker (bar, dot, lozenge, inversion); the blue gradient stays in `default` only
- new tab page follows the colors, radii and fonts of the active theme
- Pixelify Sans, Doto, Selawik and Noto Serif (SIL OFL 1.1) bundled in the Linux packages; Doto only in graphite titles
- internal pages (settings, history, downloads, extensions, bookmarks) take colors, radius, font and toggles from the active theme
- settings menu icons, buttons and toggles follow the theme palette outside the default theme
- settings cards and pill buttons take the theme radius outside the default theme
- classical lozenge and graphite dot get their own room in the tab; mono themes end long tab titles with an ellipsis
- pixelized new tab greeting in Pixelify Sans
- version 0.3.4 in the binary and package names
- chromium-web-store without a permanent service worker
- theme smoke test opens the pages for real and adds sidebar shots

## v0.3.3 (2026-10-15)

Published as a normal release: https://github.com/newcortexbr/aerographene/releases/tag/v0.3.3

- Linux avx2 packages: Arch (`.pkg.tar.zst`), `.deb`, `.rpm` and `.tar.zst`
- Windows 10/11 zips for avx2 and avx1 (cross-compiled, not tested on a real machine)
- eight built-in themes (six new), dark only; importing a theme with a reserved name is refused
- Pixelify Sans and Doto are not bundled; a fallback font is used
- all v0.3 features are in the package

## v0.3.2 (not published on its own, merged into v0.3.3)

- first-use page `aerographene://setup`, shown once per new space
- Ctrl+Tab switcher with thumbnails, most-recently-used order
- Ctrl+N creates a note on the notes page
- spaces: avatar menu, picker and new-space steps redesigned; "profile" reads as "space"
- Helium services, its setup page and out-of-scope extras removed; shortcuts documented in one page
- settings redesigned: rounded cards, larger toggles, light and dark follow the theme
- optional selective `-O3` build input

## v0.3.1 (pre-release, 2026-10-14)

- notes page `aerographene://notes` over a folder of Markdown files (vault); `o:` in the command bar
- terminal board `aerographene://terminal`; `t:` in the command bar
- Ctrl+T opens the command bar centered in the window
- settings redesigned (appearance only)
- Google as default search engine; Chrome Web Store extension installs
- Windows 10/11 cross-compile on the Linux runner
- `cpu=avx1` build input (x86-64-v2 + AVX) and native package scripts (`.pkg.tar.zst`, `.deb`, `.rpm`)

## v0.3.0 (pre-release, 2026-10-13)

- v0.3 base: see v0.3.1 for the user-facing features

## v0.2.1

- orphaned `.install-*` folders in the theme folder are removed at startup
- pixelized theme: square checkbox and radio on internal pages
- theme folders with non-ASCII names work under a `C` locale

## v0.2

- internal pages (history, settings, security) follow the theme
- theme picker in settings, local theme folder and `.aerotheme` import
- site cache deleted after 30 days, cookies kept
- benchmark against Helium, Thorium, Chrome and ungoogled: no metric worse than Helium

## v0.1.0 (2026-10-12)

- Linux x86-64-v3 build with `.tar.zst` release and PKGBUILD
- sidebar with a pinned grid, folders and drag-to-folder; topbar mode with a pinned row
- centered command bar with per-type icons
- peek (popups and `target=_blank`) and split view
- spaces as profiles, one window each
- two built-in themes: default and pixelized
- cold data for history, favicons, sessions and downloads (30 days)
- uBlock Origin (MV2) built in and on by default; Arc importer for pinned items
- readable process names
