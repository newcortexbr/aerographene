# checklist de fidelidade v0.1 (fase 0)

escopo: elementos visuais dos mockups R-r01a/b, M-r01a/c, E, F e dos guias default/pixelized aplicáveis à v0.1 (docs/SCOPE.md, decisões de 11/10/2026). Fora: notas, terminal/board, mcode, miao.
pacote comparado: `aerographene-0.1.0-154.0.8037.97-1-6289423` (6289423 = merge do PR 23). Capturas em `/tmp/fid0-out/shots/<tema>-<modo>-<cena>.png`, painéis em `/tmp/fid0-out/diff/`, métricas em `/tmp/fid0-out/diff/results.json`.
formato: `N. elemento. mock: valor do HTML/CSS do mockup. cap: valor medido na captura. D: status. P: status.` D = default, P = pixelized. Status: bate, diverge, nv (não verificado), exc (exceção aceita no SCOPE; não conta como divergência).
mockups default: `theming/1/R-r01a-home-sidebar`, `R-r01b-notas-topbar`, `M-r01a/c`; pixelized: `theming/design-language/pixelized/R-r01a/b`. Não há mockup pixelized de menus, split ou peek.

## limites de medição (valem para todos os itens)

- a tela do host é 1366x768: a janela fica 1366x740 (mockups 1440x900). Posições à direita e ao centro são comparadas por âncora, não por pixel absoluto.
- o mockup topbar R-r01b é a cena de notas (fora do escopo): só barra de abas, navegação e linha de pinned entram na comparação.
- spaces não existem no pacote; "Pessoal" não pode ser semeado. Favicons dos pinned semeados (png locais) não apareceram nos botões (globo/ponto): itens de favicon ficam nv.
- hover, foco de teclado, animação e menus de pinned/pasta/space (M-r01b/d/e), split (E) e peek (F) não foram capturados (nv).

## toolbar (modo sidebar; capturas `*-sidebar-home`)

1. altura da toolbar. mock: 44px. cap: 44px (pinned começa em y=46). D: bate. P: bate.
2. fundo da toolbar. mock D: gradiente rgba(10,16,30,.9)->rgba(5,9,18,.9), medido #080e1b; P: #111111. cap: D #080d19, P #111111. D: bate. P: bate.
3. borda inferior 1px da toolbar. mock: rgba(140,180,255,.16) (#1e283f no D; branco 14% no P). cap: sem linha (y=43/44 igual ao fundo). D: diverge. P: diverge.
4. glifos de navegação e toggle. mock D: octógonos de traço 1.5 butt/miter (reload chanfrado); P: bitmap 16x16. cap: D usa o reload circular padrão do Chromium; P usa bitmap do tema. D: diverge. P: bate.
5. posição dos botões à esquerda. mock: centros x=27, 58, 91, 123 (toggle, voltar, avançar, recarregar). cap: x=23, 62, 99, 135 (pitch maior). D: diverge. P: diverge.
6. largura da URL. mock: 640px, centralizada na janela. cap: 640px (x 363..1002 em 1366). D: bate. P: bate.
7. altura da URL. mock: 30px (y 7..37). cap D: 34px (y 6..39). D: diverge. P: nv.
8. fundo da URL. mock D: gradiente rgba(14,22,42,.7)->rgba(5,9,19,.82), médio #0d1422; P: #181818. cap: D #0a1020 chapado, P #131313. D: diverge. P: diverge.
9. contorno da URL. mock D: inset 1px rgba(108,182,255,.26); P: inset 1px --line (#383838). cap: sem contorno (P só tem anel branco 2px de foco automático). D: diverge. P: diverge.
10. texto da URL. mock: 13px, centralizado, --text2 (#A9B8D0); P: mono 12px. cap: alinhado à esquerda, claro (#eaf2ff), fonte Noto; texto "Pesquise no No Search ou digite o URL". D: diverge. P: diverge.
11. ícones dentro da URL. mock: ajustes do site à esquerda, copiar link à direita, sem estrela (SCOPE). cap: lupa à esquerda; no site comum, info + estrela à direita (estrela proibida). D: diverge. P: diverge.
12. botões de janela na toolbar. mock: min/max/fechar com glifos do tema (SCOPE). cap: três botões presentes à direita, na toolbar, sem barra extra. D: bate. P: bate.
13. glifos dos botões de janela. mock: i-min/i-max/i-close do pacote do tema. cap: glifos Chromium padrão; estilo do tema não distinguível. D: nv. P: nv.
14. avatar do space. mock: quadrado 28x28 raio 4, contorno 1px --line. cap: ícone de conta circular. D: diverge. P: diverge.
15. botão de menu. mock D: três pontos verticais; P: três pontos horizontais. cap: D vertical, P horizontal. D: bate. P: bate.
16. botões extras na toolbar. mock: nenhum além de avatar/menu (download e extensões ficam no rodapé da sidebar). cap: escudo e extensões na toolbar; P também mostra grade. D: diverge. P: diverge.

## sidebar (modo sidebar)

17. largura da sidebar. mock: 240px. cap: 240px (divisor em x=239). D: bate. P: bate.
18. borda direita da sidebar. mock: 1px --line (#1b2438). cap: linha #48494c (cinza do frame do Chromium). D: diverge. P: diverge.
19. fundo da sidebar. mock D: gradiente rgba(8,14,28,.94)->rgba(4,7,14,.96) (#080e1c -> #050912); P: #111111. cap: D #04070e chapado; P #0a0a0a. D: diverge. P: diverge.
20. padding horizontal da sidebar. mock: 12px (conteúdo x 12..228). cap: 6px (aba ativa x 6..233). D: diverge. P: diverge.
21. grade de pinned. mock: 4 colunas, células 40x40, gap 4, raio 4, contorno 1px --line, fundo rgba(255,255,255,.02) (P #111). cap: uma linha de 6 botões 34x30, pitch 38, raio ~8. D: diverge. P: diverge.
22. favicon do pinned. mock: 20px. cap: globo/ponto placeholder (favicons semeados não carregaram; "favicons vêm dos sites" é exceção do SCOPE). D: exc. P: exc.
23. marcador de pinned vivo. mock D: quadrado 6x6 --accent (#6cb6ff) a 3px do canto superior direito, raio 1; P: branco, raio 0. cap: ausente. D: diverge. P: diverge.
24. pinned fechado esmaecido. mock (proposta): opacity .62, borda tracejada. cap: ponto central. D: nv. P: nv.
25. linha do space "Pessoal". mock: ícone de pasta --accent + rótulo + chevron para baixo, linha de 32px sem caixa. cap: ausente (spaces não implementados no pacote). D: diverge. P: diverge.
26. linha de pasta "Trabalho". mock: 32px, ícone de pasta --accent, rótulo --text2, chevron à direita. cap: chevron à esquerda, ícone cinza, rótulo branco. D: diverge. P: diverge.
27. rótulos da pasta em P. mock P: mono 12px, caixa alta, letter-spacing .08em. cap: Noto, caixa normal. letter-spacing é exceção do SCOPE; mono e caixa alta não. D: bate. P: diverge.
28. divisor entre pinned e abas. mock: 1px --line, margem 10px. cap: ausente. D: diverge. P: diverge.
29. altura e espaçamento das abas. mock: 32px, gap 4 (pitch 36). cap: pitch 32 (y 160, 192, 224). D: diverge. P: diverge.
30. conteúdo da aba. mock: favicon 16px em x=20, texto 13px em x=44. cap: favicon em x=14, texto em x=36. D: diverge. P: diverge.
31. aba ativa: fundo e contorno. mock D: gradiente rgba(108,182,255,.14)->rgba(10,16,32,.78), contorno 1px topo e lados; P: bloco #0a0a0a, contorno branco 1px, faixa dither Bayer à direita. cap: D #080d19 chapado sem contorno; P #111111 sem contorno e sem dither. D: diverge. P: diverge.
32. aba ativa: indicador. mock D: barra --accent 2px no topo, inset 8px; P: nenhum. cap: nenhum. D: diverge. P: bate.
33. tamanho da aba ativa. mock: 216x32 (x 12..228). cap: 228x30 (x 6..233, y 210..239). D: diverge. P: diverge.
34. botão fechar da aba. mock: 22x22 raio 3, visível em todas as abas. cap: X só na aba ativa/hover. D: diverge. P: diverge.
35. rótulo e glifo da nova aba. mock: "+ Nova aba" como linha, acento --accent no "+". cap: "+ Nova guia" esmaecida (tradução padrão do Chromium). D: diverge. P: diverge.
36. rodapé da sidebar. mock: divisor 1px, download e extensões a ~23px da base; miao (fora do escopo). cap: divisor e os dois ícones a ~26px da base. D: bate. P: bate.
37. glifo de extensões no rodapé. mock D: quebra-cabeça de traço; P: grade bitmap. cap: D quebra-cabeça, P grade bitmap. D: bate. P: bate.

## modo topbar (capturas `*-topbar-home`; mockup R-r01b só nas faixas de abas, nav e pinned)

38. altura total do chrome. mock: 120px (pastas 40 + abas 36 + nav 44). cap: 118px. D: bate. P: bate.
39. linha de pinned e pastas acima das abas. mock: pastas e pinned 30x30 na primeira linha (SCOPE v0.1). cap: pinned viram miniaturas na própria linha de abas; a linha abaixo da navegação só tem o ícone de grade. D: diverge. P: diverge.
40. ordem das faixas. mock: pinned/pastas, abas, navegação. cap: abas, navegação, linha de grade. D: diverge. P: diverge.
41. tamanho da aba. mock: 196x30, raio 4. cap ativa: 198x28 (x 516..713). D: bate. P: bate.
42. separador vertical entre abas. mock: 1px --line, oculto ao lado da ativa e no hover. cap: separadores presentes. D: bate. P: bate.
43. aba ativa no topbar. mock D: gradiente + indicador accent 2px; P: bloco dither. cap: fundo chapado #080d19 (D) e #111 (P), sem indicador/dither. D: diverge. P: diverge.
44. botão de nova aba. mock: "+" após a última aba. cap: "+" após a última aba. D: bate. P: bate.
45. URL no topbar. mock: 560px centralizada, 30px. cap: ~555px, 34px. D: diverge. P: diverge.
46. fundo da faixa de navegação. mock D: rgba(6,10,20,.82) sobre --bg (#070d1a); P: #181818 na URL, #111 na faixa. cap: D #080d19, P #111111. D: bate. P: bate.
47. fundo da faixa de abas. mock D: #040811; P #111111. cap: D #04070e, P #0a0a0a. D: bate. P: diverge.

## nova aba (home; capturas `*-home`)

48. wallpaper D. mock: gradiente azul-preto com nebulosa, ondas e estrelas, estático (SCOPE: sem animação). cap: mesmo fundo estático; média #142243 (mock #111c37), mae 18,8 na região. D: bate. P: nv.
49. wallpaper P. mock: dither 1-bit Bayer 8x8, pixel 2, média #252525. cap: wallpaper azul do default (média #152243), mae 53,1. D: nv. P: diverge.
50. animação do wallpaper. mock: drift 26s. cap: estático. SCOPE exige estático. D: exc. P: exc.
51. relógio. mock: 13px, letter-spacing .32em, --text2; SCOPE: fonte 7-Segment (OFL). cap: Noto, espaçamento largo, sem 7-Segment. D: diverge. P: diverge.
52. saudação. mock: 76px, peso 200, letter-spacing -.02em; D com glow 0 0 40px rgba(108,182,255,.35); P sem glow e com fundo #0a0a0a por trás. cap: tamanho e peso equivalentes ("boa noite."); sem fundo sólido no P. D: bate. P: diverge.
53. glow da saudação. mock D: text-shadow azul. cap: não distinguível. D: nv. P: nv.
54. clima. mock: "24° parcialmente nublado". cap: ausente. SCOPE: clima opt-in, desligado por padrão. D: exc. P: exc.
55. mensagem do dia. mock: rótulo 11px caixa alta + frase 15px peso 300. cap: data "DOMINGO, 11 DE OUTUBRO" no lugar. D: diverge. P: diverge.
56. campo de busca. mock: 420x44, raio 4, fundo rgba(8,14,28,.55) (P #181818), contorno --line. cap: 420x43 (x 592..1011), contorno fino, fundo escuro. D: bate. P: bate.
57. texto e atalho da busca. mock: "Buscar ou abrir um endereço" 14px + kbd "Ctrl+K". cap: "Abrir um endereço", sem kbd. D: diverge. P: diverge.
58. botão Personalizar. mock: canto inferior direito, 32px, raio 4, ícone de engrenagem. cap: ausente. D: diverge. P: diverge.
59. posição vertical da pilha. mock: relógio em y=307 de 900 (34%). cap: y=285 de 740 (38%). D: nv. P: nv.

## menus (capturas `*-menu-aba`, `*-menu-3pontos`; mock M-r01c e M-r01a só no default)

60. fundo do menu. mock: rgba(7,12,24,.96) sem blur (exceção: menus sem blur, quase opaco); P: #111111. cap: D #070c18, P #111111. D: exc. P: nv.
61. largura do menu de aba. mock: 247px. cap: 414px. D: diverge. P: nv.
62. largura do menu de três pontos. mock: 254px (itens 240). cap: ~424px. D: diverge. P: nv.
63. altura dos itens. mock: 32px, padding 6px do flutuante. cap: pitch 32px. D: bate. P: nv.
64. contorno e raio do menu. mock: inset 1px --line, raio 4, sombra 0 12 40 rgba(0,0,0,.5). cap: sem contorno nem raio visíveis; moldura preta de sombra. D: diverge. P: nv.
65. ícones e atalhos nos itens. mock: ícone 16px --accent na esquerda, atalho --text2 12px na direita. cap: ícones em poucos itens, atalhos presentes. D: diverge. P: nv.
66. itens do menu de aba. mock: Nova aba à direita, Recarregar, Duplicar, Fixar aba, Silenciar aba, Fechar aba, Fechar outras abas, Fechar abas à direita. cap: 15 itens (visualização dividida, grupo, copiar URL, lista de leitura, Hibernar...). D: diverge. P: nv.
67. itens do menu de três pontos. mock: Nova aba, Nova janela, Spaces, Histórico, Personalizar página, Zoom. cap: menu padrão do Chromium com 17+ linhas. D: diverge. P: nv.
68. destaque do item. mock: hover rgba(120,170,255,.12) e barra accent à esquerda; P: bloco branco texto preto. cap: realce plano sem barra. D: diverge. P: nv.
69. menu de pinned, pasta e space (M-r01b/d/e). mock: variações do mesmo componente. cap: não capturado. D: nv. P: nv.

## command bar, split e peek

70. command bar (palette 600px, topo 190px, campo 40px, resultado 50px). cap: não capturado nesta fase. D: nv. P: nv.
71. clique na URL abre a command bar (SCOPE). cap: não exercitado. D: nv. P: nv.
72. split view (E-r01a/b). cap: não capturado. D: nv. P: nv.
73. peek (F-r01a/b). cap: não capturado. D: nv. P: nv.

## tipografia e forma gerais

74. família e tamanho base. mock D: "Noto Sans", 13px/1.2. cap: Noto Sans 13px nos rótulos. D: bate. P: nv.
75. fonte mono em P. mock P: mono 12px nos rótulos de pasta, aba, URL e botão. cap: Noto em todo o chrome. D: bate. P: diverge.
76. raio das superfícies. mock D: 4px (3px em itens internos); P: 0 em campo e botão. cap: botões e pinned com raio ~8; URL P com anel arredondado. D: diverge. P: diverge.
77. letter-spacing do chrome nativo. mock: .08em (P) e rótulos .14em. SCOPE: sem letter-spacing no chrome nativo. D: exc. P: exc.
78. ícones de traço. mock D: 16px, stroke 1.5, butt/miter, octógono no lugar de círculo. cap: ícones Chromium padrão nos botões de nav e menu. D: diverge. P: nv.
79. ícones bitmap 16-bit. mock P: 3 tons, contorno 1px. cap: toggle, reload, grade e extensões em bitmap. D: nv. P: bate.
80. foco de teclado. mock: outline 2px --accent, offset 2px. cap: anel branco 2px na URL do P (foco automático da NTP); sem verificação por teclado. D: nv. P: nv.

## comandos

```bash
# captura (abre 4 navegadores em sequência, um por tema x modo; porta CDP 9333; encerra só o PID aberto)
python3 theming/fidelity/capture.py --pkg /home/dasher/.cache/aero-bench/pkg-6289423/x --out /tmp/fid0-out
# diff por região (mockups em theming/ do checkout principal, não rastreados)
python3 theming/fidelity/diff.py --shots /tmp/fid0-out/shots --out /tmp/fid0-out/diff --mock-root /home/dasher/projects/browser/theming
```
