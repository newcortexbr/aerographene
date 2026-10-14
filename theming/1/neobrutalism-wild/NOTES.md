# neobrutalism wild (proposta, só design)

mockups estáticos 1440×900 de uma leitura mais ousada do tema neobrutalism: `index-dark.html/.png` e `index-light.html/.png`. Autocontidos, sem rede, conteúdo fictício. Sem patch, sem aprovação do dono.

## escolhas

- abas tortas (rotação ±1–3°), cada uma de uma cor chapada; aba ativa maior, levantada, com "pé" que cola no painel; prefixos `o:` e `t:` em etiqueta invertida.
- logo e botão `+` como adesivos girados; omnibox grossa (4px) com pílula de estado e atalho; botões de navegação em blocos com sombra sólida.
- faixa de blocos coloridos sob a barra (sinalização); fundo com listras diagonais finas.
- nova aba: saudação gigante (168px, uma linha preenchida, outra só contorno), sol listrado, cartões rotacionados, widget de fixados, adesivos, fita de texto na base.
- sombras duras sem blur, bordas de 4–6px; sem raio (exceto avatar e sol).
- usabilidade: barra de abas/endereço em posição e ordem normais; só a decoração gira. Pendente: abas ao lotar (rotação deve parar ou reduzir), foco de teclado, hover, texto sobre cores a 14px.

## paleta

- compartilhadas, dark / light: rosa #ff2e93 / #ff4fa3, lima #d7ff1e / #b6ff00, ciano #00e5ff / #27d3ff, amarelo #ffe600 / #ffd400, laranja #ff6a1a / #ff7a2e.
- dark: fundo #0b0b10, traço e texto #ffffff, chrome #16161d, aba neutra #26262f.
- light: fundo #fff3d6, traço e texto #0b0b10, chrome e omnibox #ffffff.
- texto sobre cor saturada sempre #0b0b10. Contraste não medido.

## render

Chromium headless shell 1234 (Playwright local), 1440×900. Inspecionados visualmente.
