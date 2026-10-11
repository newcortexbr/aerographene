# aerographene

Navegador desktop de uso pessoal, com builds públicas disponíveis. Sidebar-first, inspirado no Arc. Foco em leveza: abertura rápida, pouca RAM, pouco disco e baixa densidade visual.

## Language

**Space**:
Contexto de navegação isolado que corresponde a um perfil do navegador. Cada space ocupa uma janela própria; trocar de space troca a janela no mesmo lugar e tamanho. Um space pode ser aberto à parte em outra janela, mas nunca existe em duas janelas ao mesmo tempo.
_Avoid_: perfil (na UI), workspace

**Pinned**:
Aba fixada de um space, exibida na grade de pinned, separada das abas abertas. Pinned e favorito são o mesmo elemento.
_Avoid_: favorito, bookmark (como conceito separado)

**Pinned fechado**:
Pinned sem aba viva no momento; tem indicador visual próprio. Fechar a aba de um pinned ou descarregá-la (menu de contexto) leva a esse estado; clicar nele abre do zero.

**Grade de pinned**:
Área da sidebar onde ficam os pinned. Cada pinned ocupa uma ou mais células na horizontal; a grade se rearranja quando a sidebar é redimensionada.

**Largura do pinned**:
Número de células horizontais que um pinned ocupa (padrão 1, só o favicon). O usuário muda arrastando a borda; com mais largura aparece o rótulo.

**Rótulo do pinned**:
Texto editável exibido ao lado do favicon quando a largura permite.

**Pasta**:
Linha que ocupa toda a largura da grade de pinned e, ao abrir, revela uma gaveta com a grade dos pinned que contém.
_Avoid_: grupo

**Aba aberta**:
Aba viva na sidebar que não é pinned.

**Command bar**:
Ponto de entrada universal: busca na web, URLs, abas abertas, pinned, histórico e comandos. Cada resultado tem um ícone do seu tipo.

**Comando**:
Ação do navegador executada pela command bar, marcada com `[/]`.

**Split view**:
Duas ou mais abas lado a lado na mesma janela, criadas arrastando uma aba sobre a página.

**Peek**:
Janela leve e temporária que abre popups e links com `target=_blank` sem criar aba aberta. Pode ser promovida a aba.

**Modo sidebar**:
Layout padrão, com abas verticais na sidebar.

**Modo tabs normais**:
Layout alternativo, com abas horizontais no topo, mantendo a mesma linguagem visual.

**Dado frio**:
Dado do perfil sem uso há mais que o prazo configurável (histórico, favicons e miniaturas, sessões antigas, registro de downloads e dados de sites). Sai do armazenamento quente e é catalogado, continuando pesquisável; comprimido só onde a compressão rende (texto do histórico fica sem compressão, decisão do dono em 11/10/2026).

**Prazo de frio**:
Número de dias sem uso após o qual um dado vira dado frio. Configurável; padrão 30 dias.

**Exceção de frio**:
Lista de sites cujos dados nunca esfriam, como provedores de conta (Google, Proton, Microsoft). Cookies também nunca esfriam.

**Reidratação**:
Volta de um dado frio de um site ao estado normal quando o usuário acessa esse site.
_Avoid_: descompressão (na UI)

**Versão**:
Número `vX.Y.Z` do aerographene: X = release, Y = feature, Z = bugfix. É independente da versão do Chromium por baixo.

## Flagged ambiguities

- "Favoritos" e "pinned" eram dois formatos; foram unificados num elemento só (pinned) com largura variável, e a grade substitui a lista.
- "Agrupar os processos de um perfil": decidido que é só nomear (Linux); processos continuam separados por site. No Windows fica `aerographene.exe`.
