# metro-v2

pele do navegador no idioma visual do Windows 10 (2015–2017). mesma composição da print atual; só mudam cor, fonte, borda, forma de controle e ícone. status: mockup aprovado pelo dono em 2026-10-14; ainda não é patch.

## tokens

dark / light:

- frame e sidebar: `#1f1f1f` / `#f2f2f2`
- painel: `#2b2b2b` / `#e6e6e6`
- página: `#000000` / `#ffffff`
- linha: `#3c3c3c` / `#d6d6d6`
- texto: `#ffffff` / `#000000`; secundário `#c8c8c8` / `#333333`; terciário `#a8a8a8` / `#4a4a4a`
- botão: `#333333` / `#cccccc`; seleção `#3e3e3e` / `#cccccc`; hover `#333333` / `#e0e0e0`
- campo: fundo `#000000` / `#ffffff`, borda 2px `#666666` / `#7a7a7a`
- destaque: `#0072cb` / `#0063b1` (branco sobre destaque passa AA nos dois)
- link: `#4cc2ff` / `#0063b1`

formas: cantos retos (raio 0) em campos, botões, abas, chips e avatar; botão principal chapado na cor de destaque; aba ativa com fundo de seleção e barra de destaque de 3px à esquerda; favicon em quadrado colorido.

contraste: `contrastes.txt` (gerado por `assets/sheet.py`). todos os pares de texto passam AA (4,5:1); bordas de campo passam 3:1.

## fonte

Selawik (Microsoft, SIL OFL 1.1), substituta métrica livre da Segoe UI. arquivos e licença em `assets/fonts/` (`selawkl` light, `selawk` regular, `selawksb` semibold, `selawkb` bold; woff2 e ttf).

- UI: 13px regular; títulos de painel 15px light; ênfase em semibold.
- pilha: `Selawik, 'Segoe UI', sans-serif`.
- monoespaçada: `Noto Sans Mono` (kbd), sem troca.

## ícones

45 SVGs em `assets/icons/`, fonte única em `assets/icons.py` (`ICONS`, função `svg`). grade 20x20, traço 1,3px, cantos retos, `currentColor`; só `star-fill` e `more` são sólidos. folhas de conferência: `icons-dark.png`, `icons-light.png`.

grupos:

- janela: side, back, fwd, reload, home, stop, min, max, restore, close
- omnibox: search, tune, link, lock, star, star-fill, shield, user, more, more-h, down, ext
- abas: plus, chevron-down, chevron-right, pin, speaker, mute, tabs, folder, history, bookmark, print, zoom, incognito
- conteúdo: globe, doc, term, chat, gear, edit, trash, check, info, warn

## regenerar

```bash
cd assets && python3 build.py && bash render.sh && python3 sheet.py
```

## para virar patch (pendências)

- conferir na árvore os ColorIds reais antes de mapear os tokens.
- tokens próprios para aba ativa (barra de 3px), pinned e chip.
- peso e família da fonte global; empacotar Selawik como recurso do navegador.
- ícones: converter SVG para vector icons do Chromium; conferir cobertura dos 45 contra os ids existentes.
- cor por space exige patch de Views.
- cantos retos: conferir `ChromeLayoutProvider` e controles nativos.
