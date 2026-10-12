# aerographene: escopo

Estado: v0.1 implementada (ver "estado em 12/10/2026"). Glossário em `../CONTEXT.md`; decisões em `adr/`.

## v0.1 (Linux, x86-64-v3)

Ordem de construção:

1. medição: harness de abertura a frio e a quente, PSS total e Speedometer 3.1; linha de base com ungoogled-chromium, Helium, Thorium e Zen, medida no Comet Lake.
2. build no runner self-hosted (ADR 0004) com as flags do ADR 0003.
3. patches de desempenho trazidos do Helium: infinite-tab-freezing, memory-saving-by-default, lazy-session-restore, disable-ai, add-low-power-framerate-flag.
4. UI: modo sidebar com grade de pinned (largura arrastável, rótulo, pastas com gaveta) e modo tabs normais. Base: patches de layout do Helium (vertical, side-panel, centered-address-bar, multi-contents-view).
5. spaces como janelas (ADR 0005), cada um em no máximo uma janela.
6. command bar com ícones por tipo.
7. peek (popups e `target=_blank`) e split view por arrastar (patch split-view do Helium).
8. dois temas de teste (gradiente nebuloso azul-preto com estrelas; preto alto contraste) e tema/padding nas páginas internas.
9. nomes de processo no Linux: `aerographene: <space>`, `aerographene: gpu` etc. No Windows fica `aerographene.exe`.
10. dado frio de histórico, favicons/miniaturas, sessões e downloads, com prazo de 30 dias configurável (ADR 0007); cache de sites com mais de 30 dias é apagado.
11. extensões: uBlock Origin completo (MV2) embutido, com o patch MV2 do ungoogled e a instalação como componente do Helium; instalação pela Chrome Web Store. Importador do Arc.
12. distribuição: `.tar.zst` na GitHub release + PKGBUILD no repo. Sem auto-update.

Regra de desempenho: nenhuma mudança piora mais de 2% a linha de base; uma mudança por vez.

## estado em 12/10/2026 05:30

v0.1 implementada e empacotada; build do CI verde em d83fc39 (run 38195073580), release v0.1.0 em draft com o `.tar.zst` e SHA256SUMS.

1. feito; baseline da v0.1 (n=30, warm, perfil novo, 10 abas, PSS) em docs/BASELINE.md: aerographene 3,1 a 5,6% melhor que Helium em abertura e -1,6% de PSS; PSS +9,6% vs ungoogled (ponto de atenção). Speedometer não automatizado; perfil novo não equivale a disco frio.
2. feito: runner self-hosted, ThinLTO e PGO conforme ADR 0003/0004.
3. feito: patches do Helium ativos e compilando (110 entradas em patches/series).
4. feito: sidebar com grade de pinned, pastas com gaveta, menus de contexto e arrastar para pasta; modo topbar com linha de pinned e pastas.
5. feito (ADR 0005): space = perfil, uma janela por space, troca pelo avatar.
6. feito: command bar com ícones por tipo; clique na URL e Ctrl+L abrem o painel.
7. feito: peek com tamanho próprio e split view do Helium.
8. feito: temas default e pixelized seguindo os mockups com as exceções registradas abaixo; NTP em HTML/CSS. Fidelidade conferida por captura e diff (theming/fidelity/).
9. feito: process-names.
10. feito: dado frio de histórico, favicons, sessões e downloads (ADR 0007).
11. feito: uBlock embutido e ligado por padrão; MV2 do ungoogled; importador do Arc para pinned.
12. feito: PKGBUILD validado com makepkg contra o tarball de d83fc39; release em draft (publicar é decisão do dono).

Não verificado: uso real por clique e teclado de spaces, command bar, peek, split, menus de contexto e arrasto (fica para v0.2, roteiro de teste a preparar).

## depois

- v0.2: teste de uso real de spaces, command bar, peek e split view; reescrita das páginas internas (histórico, configurações, segurança); dado frio do storage de sites, com reidratação na navegação, exceções de frio e cookies nunca frios.
- v0.3: Windows 11 e build v2+AVX para a Ivy Bridge; Obsidian e terminais nos workspaces; Google Sync com chaves próprias (ADR 0006, decisão do dono em 12/10/2026, antes "depois da v0.3"); antes, testar o login sobre o ungoogled.
- fora: boosts (usar Stylus), anti-fingerprinting `noise/*`, zen-mode.

## decisões do dono (11/10/2026)

- item 8: os temas da v0.1 são o default e o pixelized (substituem nebula e high-contrast). Meta objetiva: seguir exatamente os mockups em `theming/design-language/` (default e pixelized).
- item 11: uBlock sempre ligado por padrão. Ícone da extensão acompanha o pacote de ícones do tema ativo.
- temas são claros ou escuros por natureza: cada tema define o próprio esquema e não há alternância claro/escuro nem "seguir o sistema". Os dois temas da v0.1 são escuros; o navegador abre no escuro.
- teste de uso real de spaces, command bar, peek e split view fica para a transição v0.1 → v0.2.
- fidelidade aos mockups (11/10/2026, decisão do dono): seguir R-r01a/b, M, E, F e os guias default/pixelized onde possível. Fora: notas, terminal/board, mcode e miao. Exceções aceitas: sem letter-spacing no chrome nativo (só em HTML); menus sem blur, fundo quase opaco; favicons vêm dos sites.
- barra de URL: ajustes do site e copiar link dentro da barra, numa das extremidades; sem estrela. Clique na URL abre a command bar (estilo Zen/Arc), dentro da v0.1.
- botões de janela (minimizar, maximizar/restaurar, fechar) ficam na própria toolbar, sem barra extra vazia, com glifos do pacote de ícones do tema ativo.
- página de nova aba: HTML e CSS puros, wallpaper estático (sem animação); clima opt-in, desligado por padrão.
- modo topbar na v0.1: abas normais com uma linha acima para pinned e pastas; o resto do R-r01b é refinamento.
- sem linha de space com ícone de pasta no topo da sidebar/topbar (diverge do mockup, decisão do dono 11/10): space é perfil do Chrome e se troca só pelo avatar/seletor de perfil. Pastas da linha do topbar e gavetas da sidebar são a mesma pasta de pinned (menu de contexto), com o mesmo estado aberto/fechado.

## em aberto

Nada no escopo. Riscos conhecidos: MV2 pode perder mais código em versões futuras do Chromium; chaves Google podem ser revogadas (ADR 0006).
