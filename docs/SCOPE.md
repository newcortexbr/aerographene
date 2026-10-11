# aerographene: escopo

Estado: fechado no grilling de 04/10/2026; aguardando confirmação do dono para começar a implementação. Glossário em `../CONTEXT.md`; decisões em `adr/`.

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

## estado em 05/10/2026 01:50

1. feito (docs/BASELINE.md).
2. parcial: infra e workflow prontos; primeiro build compilando (run 37263759580), não concluído.
3. parcial: 40 patches do Helium ativos e aplicando; compilação não verificada.
4. a 10: não iniciados (sidebar/grade parcialmente coberta pelos patches de layout do Helium, sem a grade de pinned própria).
11. parcial: MV2 vem do ungoogled; uBlock embutido desativado (faltam fontes third_party/ublock); importador do Arc portado.
12. parcial: build gera .tar.zst como artifact; sem release nem PKGBUILD.

## depois

- v0.2: teste de uso real de spaces, command bar, peek e split view; reescrita das páginas internas (histórico, configurações, segurança); dado frio do storage de sites, com reidratação na navegação, exceções de frio e cookies nunca frios.
- v0.3: Windows 11 e build v2+AVX para a Ivy Bridge.
- sync: Google Sync com chaves próprias (ADR 0006), depois da v0.3; antes, testar o login sobre o ungoogled.
- fora: boosts (usar Stylus), anti-fingerprinting `noise/*`, zen-mode.

## decisões do dono (11/10/2026)

- item 8: os temas da v0.1 são o default e o pixelized (substituem nebula e high-contrast). Meta objetiva: seguir exatamente os mockups em `theming/1/design-language/` (default e pixelized).
- item 11: uBlock sempre ligado por padrão. Ícone da extensão acompanha o pacote de ícones do tema ativo.
- teste de uso real de spaces, command bar, peek e split view fica para a transição v0.1 → v0.2.

## em aberto

Nada no escopo. Riscos conhecidos: MV2 pode perder mais código em versões futuras do Chromium; chaves Google podem ser revogadas (ADR 0006).
