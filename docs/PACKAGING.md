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

Páginas internas (WebUI) usam `chrome://theme/colors.css`, gerado do ColorProvider, então também recebem os tokens. Desligar: `--disable-features=AerographeneThemeTokens`. Custo: uma leitura de arquivo pequeno (até 64 KiB) na primeira montagem de cores; medir contra a linha de base (regra de 2%). Não testado em navegador.
