# tools

gera os assets da galeria de temas e do seletor de tema do site.

```bash
bash tools/build-gallery.sh          # regenera tudo
DL=/caminho/design-language bash tools/build-gallery.sh   # mockups em outro lugar
```

- fonte única: `themes.src.json` (temas, status, tokens dark/light, fontes, textos da galeria).
- entrada: prints reais do navegador em `$SHOTS/<tema>.png` (`"!arquivo"` no `themes.src.json`); mockups antigos em `theming/design-language` só se usar `DL`.
- saída: `assets/gallery/*.webp`, `assets/fonts/*.woff2` (subset latino, licenças OFL junto), `themes.json`, `themes.css`, `tools/contrastes.txt`.
- o script sai com erro se algum par texto/fundo dos tokens ficar abaixo de AA (4.5:1).
- tema novo (por exemplo cli/tui): trocar `status` de `soon` para `proposal`/`approved`, informar os prints e tokens em `themes.src.json` e rodar o script.
- requer Python 3 com Pillow e fontTools (+ brotli). Sem rede.
