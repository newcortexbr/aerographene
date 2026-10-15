# configurações (chrome://settings)

o visual de `chrome://settings` e da página "Customise profile" (`chrome://settings/manageProfile`): estilo One UI, só aparência. Mesmo conteúdo, mesmas seções, opções, ordem e textos do Chromium; nada de template, TS, string ou asset foi mexido.

## como é

- cards bem arredondados (28px) sobre o fundo da página, sem sombra nem contorno;
- rótulo de seção pequeno e cinza acima do card (sem caixa alta, sem fonte mono);
- linhas de 56px (68px com duas linhas), padding de 22px, divisor fino entre linhas;
- toggle grande (~52x30), select e botões em pílula, preenchidos, sem borda; busca em pílula;
- lateral com item arredondado e ícone dentro de um disco colorido, uma cor por item;
- customise profile: campo de nome preenchido e arredondado; cores do tema e avatares em quadrados arredondados.

claro e escuro seguem o tema do navegador: superfícies saem de `color-mix` dos tokens do tema (`--cr-primary-text-color`, `--color-settings-webui-page-background`). Só as cores dos discos da lateral são fixas.

## como funciona

o patch é `patches/aerographene/settings-oneui.patch`, logo depois de `settings-f5.patch` (que ele sobrepõe). CSS puro:

- `settings_vars.css` define as variáveis `--oneui-*` (existem só em settings) e redefine `--cr-card-*` com `html:not(#a):not(#b)`, para vencer o bloco `html:not(#z)` do `colors.css` (raio/sombra do tema);
- `cr_toggle`, `cr_button`, `md_select_lit`, a busca da toolbar, o seletor de avatar e `theme_color` consomem `--oneui-*` com o valor anterior como fallback; histórico e outras páginas não mudam;
- `settings_section.css`, `settings_shared_lit.css`, `settings_menu.html` e `manage_profile.css` têm blocos próprios;
- os discos da lateral são `background` do `cr-icon` (glifo branco), a cor vem de `--oneui-disc` por id do item.

o One UI de settings ignora o raio do tema (`--aero-radius`): no `pixelized` os cards de settings também ficam arredondados.

## limites

- avatares do perfil continuam as imagens upstream (PNG), só com cantos arredondados; glifos geométricos exigiriam assets novos.
- o divisor entre linhas vai de borda a borda do card (sem recuo), pelo CSS atual das linhas.
- validado: aplica com `--fuzz=0`, os recursos entraram na build avx2 completa verde (run 38671160082 sobre `82a7bf3`, 15/10/2026) e screenshot headless; não testado no navegador completo.
- o visual substitui o do `settings-f5` (quadrado, raio do tema): ver [temas](temas.md).

## resumo para agentes

- patch: `aerographene/settings-oneui.patch` (depois de `settings-f5.patch` em `patches/series`), só CSS.
- nova aparência = variáveis `--oneui-*` em `settings_vars.css`; mudar raio, cores de superfície ou tamanho do toggle é editar lá.
- cr_elements compartilhados só usam `--oneui-*` com fallback: não quebram outras páginas; não remova o fallback.
- para vencer `colors.css` use `html:not(#a):not(#b)`; `html:not(#z)` empata em especificidade.
- aspas simples em CSS (o lint do build rejeita aspas duplas).
- não mexa em templates/TS para mudar só visual; ícones da lateral = `--oneui-disc` por id em `settings_menu.html`.
