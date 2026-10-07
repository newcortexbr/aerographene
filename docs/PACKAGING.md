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
