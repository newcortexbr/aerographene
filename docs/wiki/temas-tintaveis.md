# temas tintáveis (proposta)

o usuário escolhe 2 ou 3 cores por tema e todos os outros tokens saem delas. Estado: proposta com especificação e protótipo em JavaScript, fora do repo (pasta de design do dono, `theming/design-language/tint/`). Não há patch, pref nem código no Chromium; o dono ainda não aprovou as receitas.

## ideia

- limite do dono (14/10/2026): nunca mais que 3 controles de cor.
- como o tema por cor-semente do Chrome, mas com receita própria por tema e correção de contraste. Espaço de cor OKLCH.
- todos os temas aprovados são `full` (derivação completa):
  - 2 cores (`base` e `accent`): default, metro-v2, e-ink (chroma limitado), e-ink-gb (rampa sempre de 4 tons), classical.
  - 3 cores (`bg`, `fg`, `accent`): graphite e cli. No cli as 16 cores ANSI não são giradas por matiz: só o L delas é corrigido contra o fundo.
- forma, raio, fonte, ícones, wallpaper e sombras não mudam. Foco = accent e atenção (âmbar) continuam como regra do tema.

## garantias propostas

- texto 4,5:1 e contornos de controle e foco 3:1, com correção automática movendo o L do token de frente.
- par de cores quase igual (distância OKLab < 0,08): aviso `par-impossivel` e a segunda cor volta ao L aprovado do tema.
- testado só no protótipo (`node tint-test.mjs`): o par/trio padrão reproduz os tokens aprovados, e 320 combinações aleatórias por tema e modo não reprovaram nenhum par de texto ou contorno. Não verificado no Chromium.

## como entraria no navegador (proposta, não feita)

- pref de perfil `aerographene.tint` (por space, já que space é perfil, ADR 0005), um patch futuro `theme-tint` depois de `theme-tokens`/`theme-repo`.
- porta da receita para C++ (`aerographene_tint.{h,cc}`, gerada de `receitas.js`) e entrada no `AddAerographeneThemeTokensMixer`: tokens do tema embutido → tokens do tint → `theme.json`.
- `user_color` = accent do tint para os `ColorId` que os tokens não cobrem; troca de pref pelo caminho de `NotifyThemeChanged`, sem reiniciar.
- UI em `chrome://settings/appearance`, abaixo do seletor de tema: 2 ou 3 seletores, preview, avisos, "restaurar cores do tema", importar/exportar JSON curto.
- riscos anotados: ordem dos mixers, `user_color` ativar o Customize Chrome do upstream (duas fontes de cor), paridade JS e C++ (teste unitário com os pares do teste do protótipo), tema de extensão desliga o tint.

## em aberto

- aprovação das receitas e das cores derivadas; claro do default é só espelho; accent perto de erro/ok no cli não é bloqueado; contraste com textura (classical) e com traço pixelado (e-ink-gb) não coberto; porta para C++ não feita.

## resumo para agentes

- não existe nada no repo nem no Chromium; não afirmar que o navegador tem tint.
- se for implementar: pref `aerographene.tint`, mixer estendido, `user_color`, UI em appearance; paridade com o protótipo é critério de aceite; máximo 3 cores.
- temas e status: ver [temas](temas.md).
