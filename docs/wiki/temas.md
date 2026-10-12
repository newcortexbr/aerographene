# temas

como o aerographene carrega temas, onde trocá-los e como criar o seu.

> com pressa ou vai pedir para um agente fazer? pule para o [resumo para agentes](#resumo-para-agentes) no final: ele tem tudo que uma IA precisa para gerar um tema válido.

## as três camadas

o visual é montado em três camadas, aplicadas nesta ordem (a última vence):

1. tema embutido: `default` ou `pixelized`, compilados no navegador. Definem cores, raio dos cantos, fonte e ícones. São escuros por natureza; não há alternância claro/escuro.
2. `theme.json`: arquivo de tokens de cor lido no início, sem recompilar. Sobrescreve as cores do tema embutido.
3. tema de extensão do Chrome (`manifest.json` com `theme`): se instalado, o tema embutido sai de cena e vale o tema da extensão. Serve para imagens de fundo, que os tokens não cobrem.

o incógnito ignora as camadas 1 e 2 e fica no escuro padrão do Chromium.

## o que cada camada controla

- cores do navegador (frame, abas, barra, omnibox, menus, nova aba): camadas 1, 2 e 3.
- cores das páginas internas (histórico, configurações, segurança): camadas 1 e 2, via `chrome://theme/colors.css`.
- raio dos cantos: só a camada 1. `default` usa 4px em controles, menus e diálogos (3px em chips); `pixelized` usa 0 (2px em chips).
- fonte: só a camada 1. `pixelized` usa JetBrains Mono 12px (cai para `Monospace` se não estiver instalada); `default` usa a fonte do sistema.
- ícones: só a camada 1. `pixelized` troca os ícones vetoriais por versões em pixel.
- imagem de fundo do frame e da nova aba: só a camada 3.

## trocar o tema embutido

ainda não há seletor na interface. A escolha é a pref de perfil `aerographene.theme`, com valor `"default"` (padrão) ou `"pixelized"`.

1. feche o navegador.
2. abra `~/.config/aerographene/Default/Preferences` (JSON numa linha só).
3. adicione ou edite a chave no nível de cima:

```json
{"aerographene": {"theme": "pixelized"}}
```

ou seja, junte `"aerographene":{"theme":"pixelized"}` ao objeto existente sem apagar o resto. Com `jq`:

```bash
f=~/.config/aerographene/Default/Preferences
jq '.aerographene.theme = "pixelized"' "$f" > "$f.new" && mv "$f.new" "$f"
```

4. abra o navegador. Toda troca de tema exige reiniciar.

## trocar só as cores (`theme.json`)

o navegador lê, uma vez por processo, `${XDG_CONFIG_HOME:-~/.config}/aerographene/theme.json`. Para usar outro caminho, passe `--aerographene-theme=/caminho/theme.json`; a flag pode ir em `~/.config/aerographene-flags.conf` (uma flag por linha).

```json
{
  "mode": "dark",
  "tokens": {
    "frame": "#0A0A0A",
    "toolbar": "#111111",
    "text": "#F2F2F2",
    "accent": "#6CB6FF"
  }
}
```

- cores em `#RRGGBB` ou `#RRGGBBAA` (o último par é a opacidade).
- `mode` é opcional e o padrão é `"dark"`. Como os temas embutidos são escuros, use `"dark"`: tokens com `"light"` não são aplicados.
- só os tokens presentes mudam; o resto vem do tema embutido.
- arquivo ausente ou inválido: nada muda e o navegador abre normalmente. Chave desconhecida é ignorada.
- mudou o arquivo, reinicie o navegador.
- para desligar a camada sem apagar o arquivo: `--disable-features=AerographeneThemeTokens`.

### tokens

navegador:

- `frame`, `frame_inactive`: fundo da janela com foco e sem foco.
- `toolbar`: barra de ferramentas, aba ativa e barra de favoritos.
- `toolbar_text`, `toolbar_icon`: texto e ícones da barra.
- `tab_text`: texto da aba ativa.
- `tab_background`: fundo das abas inativas.
- `tab_background_text`, `tab_background_text_inactive`: texto das abas inativas, com a janela com foco e sem foco.
- `tab_hover`: aba sob o cursor.
- `hover`: realce de botões sob o cursor.
- `separator`: linhas divisórias.
- `focus_ring`: contorno de foco do teclado.
- `selection`, `selection_text`, `selection_text_dim`: item selecionado em listas e resultados.
- `menu`, `menu_text`: menus de contexto.

barra de endereço e command bar:

- `omnibox`, `omnibox_hover`, `omnibox_border`: campo, campo sob o cursor e borda.
- `omnibox_text`, `omnibox_text_dim`: texto principal e secundário.
- `omnibox_results`, `omnibox_results_hover`: lista de sugestões e sugestão sob o cursor.

nova aba:

- `ntp`, `ntp_text`: fundo e texto.

sistema (também alimentam as páginas internas e as cores derivadas do Chromium):

- `base`: fundo de página.
- `surface`: cartões e painéis.
- `text`, `text_dim`: texto principal e secundário.
- `accent`, `on_accent`: cor de destaque (links, controles ligados) e o texto sobre ela.
- `outline`: contorno de controles (campos, checkbox).

### de onde partir

- `theming/chrome-themes/pixelized/theme.json`: as cores do `pixelized`.
- `theming/chrome-themes/nebula/theme.json`: azul profundo.
- `theming/chrome-themes/high-contrast/theme.json`: preto com destaque amarelo.

copie um deles para `~/.config/aerographene/theme.json` e ajuste.

## imagem de fundo (tema de extensão)

tokens não carregam imagens. Para pôr uma imagem no frame e na nova aba, use um tema de extensão do Chrome:

1. crie uma pasta com `manifest.json` (`"manifest_version": 3` e um objeto `theme` com `images` e `colors`) e as imagens. Exemplo completo em `theming/chrome-themes/nebula/`.
2. `chrome://extensions` → modo de desenvolvedor → carregar sem compactação → a pasta.

com tema de extensão ativo, raio, fonte e ícones voltam ao padrão do Chromium, porque são da camada 1. Para remover o tema: `chrome://settings/appearance` → redefinir.

## criar um tema embutido novo

desde a v0.2 o tema é dado: a struct `ThemeData` (`chrome/browser/themes/aerographene_theme.h`, em `patches/aerographene/theme-builtin.patch`) reúne nome, esquema (claro/escuro), raios (`radius`, `radius_small`), fonte (`font_family`, `font_size_px`), pacote de ícones compilado (`icons_base`: `default` ou `pixelized`), variante compilada do desenho (`style`) e os tokens de cor. `default` e `pixelized` são instâncias dela em `aerographene_theme.cc`; raio, fonte, esquema, ícones, mockups e páginas internas leem esses campos.

um tema embutido novo é mais uma instância em `aerographene_theme.cc` (e o nome em `GetBuiltinTheme`); exige recompilar. Ícones e `style` só aceitam os pacotes/variantes compilados. Ler temas do disco (`~/.config/aerographene/themes/<nome>/theme.json`) para a mesma struct ainda não existe.

leia `docs/BUILD.md` antes; a build completa leva horas.

## problemas comuns

- nada mudou: confira se reiniciou, se o JSON é válido (`jq . theme.json`) e se `mode` é `"dark"`.
- mudou só parte: alguns elementos usam ids que nenhum token cobre ainda. Abra uma issue dizendo qual.
- página interna com cor antiga: recarregue a página; ela lê `chrome://theme/colors.css`.

---

## resumo para agentes

contexto denso para uma IA gerar um tema do aerographene. Copie esta seção inteira para o seu agente.

```text
AEROGRAPHENE THEME SPEC (v0.1, Linux)
Browser: aerographene, Chromium 154 fork. Themes are dark by nature; no light/dark toggle.

LAYERS (applied in order, last wins):
1. builtin theme, profile pref "aerographene.theme" = "default" | "pixelized".
   Controls colors + corner radius + font + icons. Needs restart.
   Set it with the browser CLOSED, in ~/.config/aerographene/Default/Preferences (single-line JSON):
   jq '.aerographene.theme = "pixelized"' Preferences > P.new && mv P.new Preferences
2. tokens file: ${XDG_CONFIG_HOME:-~/.config}/aerographene/theme.json
   or --aerographene-theme=/path (can go in ~/.config/aerographene-flags.conf, one flag per line).
   Read once at startup; restart to apply. Colors only. Overrides layer 1 colors.
   Disable: --disable-features=AerographeneThemeTokens
3. Chrome extension theme (manifest.json "theme"), loaded unpacked at chrome://extensions.
   Replaces layer 1 (radius/font/icons fall back to Chromium). Only way to add images.
Incognito ignores layers 1 and 2.

theme.json FORMAT:
{"mode": "dark", "tokens": {"<token>": "#RRGGBB" | "#RRGGBBAA", ...}}
- "mode" optional, default "dark". MUST be "dark" (builtin themes are dark; "light" tokens are not applied).
- Unknown keys ignored. Missing/invalid file = no change. Only listed tokens change.

TOKENS (all optional):
frame, frame_inactive            window background, focused/unfocused
toolbar                          toolbar + active tab + bookmarks bar
toolbar_text, toolbar_icon
tab_text                         active tab text
tab_background                   inactive tab background
tab_background_text              inactive tab text (window focused)
tab_background_text_inactive     inactive tab text (window unfocused)
tab_hover                        tab under cursor (usually low alpha, e.g. #FFFFFF0D)
hover                            button hover (low alpha)
separator                        divider lines (low alpha)
focus_ring                       keyboard focus outline
selection, selection_text, selection_text_dim   selected list/result row
menu, menu_text                  context menus
omnibox, omnibox_hover, omnibox_border          address field
omnibox_text, omnibox_text_dim
omnibox_results, omnibox_results_hover          suggestion list
ntp, ntp_text                    new tab page
base                             page background (also internal pages)
surface                          cards/panels
text, text_dim                   primary/secondary text
accent, on_accent                accent (links, toggles) and text on it
outline                          control outlines (inputs, checkboxes)
base/surface/text/accent/on_accent also drive Chromium-derived colors and internal pages
(history, settings) via chrome://theme/colors.css.

REFERENCE PALETTE ("default" builtin):
frame #04070E, toolbar #080D19, toolbar_text #EAF2FF, toolbar_icon #A9B8D0,
tab_text #EAF2FF, tab_background #04070E, tab_background_text #A9B8D0,
tab_background_text_inactive #6B7790, omnibox #0A1020, omnibox_border #6CB6FF42,
omnibox_results #070C18, omnibox_results_hover #141F34, focus_ring #6CB6FF,
selection #141F34, hover #78AAFF1F, tab_hover #FFFFFF0D, separator #8CB4FF29,
menu #070C18, ntp #04070E, base #04070E.

RULES FOR A GOOD THEME:
- Keep frame/tab_background/ntp/base close to each other (darkest), toolbar/omnibox/menu one step lighter.
- Text contrast >= 4.5:1 against its background (text vs base, tab_text vs toolbar, menu_text vs menu).
- Use alpha (#RRGGBBAA) for hover, tab_hover, separator, omnibox_border.
- accent should be readable on base; on_accent readable on accent.
- Output a single valid JSON object. No comments.

EXAMPLES in repo: theming/chrome-themes/{pixelized,nebula,high-contrast}/theme.json
```
