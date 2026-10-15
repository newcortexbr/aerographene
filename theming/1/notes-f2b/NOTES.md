# notas f2b: mockup do redesenho da página de notas

mockup HTML (sem patch, conteúdo fictício). Só a área da página muda; o chrome do navegador reproduz o estado atual (1600x872).

- `index.html`: estado com nota aberta; `index.html#vazio`: estado sem nota.
- `index.png` / `index-vazio.png`: render headless (chrome-headless-shell do Playwright, 1600x872).
- estrutura copiada do Obsidian (print de referência, fora do repositório): barra de modos/ações no topo da lateral, árvore com pastas recolhíveis e guias de recuo, abas das notas abertas, breadcrumb, título grande, rodapé com backlinks/palavras/caracteres, seletor da vault embaixo à esquerda.
- identidade do aerographene: paleta atual (`--bg #13151b`, `--panel #171a22`, `--line #2a2e3d`, `--accent #b69cff`), JetBrains Mono, cantos retos, rótulos em caixa alta, `+ pasta` desabilitado (backend só cria notas).

## diferenças em relação ao Obsidian

1. topo da lateral: três modos com rótulo de texto (arquivos / buscar / tags) e sublinhado accent, não só ícones; ações (+ nota, + pasta, ordenar, recolher) numa linha separada, com texto nos botões principais.
2. árvore: triângulos sólidos, pastas em lilás, extensão `.md` apagada, contagem de itens à direita, guias de recuo tracejadas; item ativo com barra accent de 2px na esquerda (como no patch atual).
3. abas das notas: retas, com linha accent no topo da ativa e ponto `●` para não salva; estado e botões salvar/renomear/apagar ficam na mesma faixa, à direita.
4. breadcrumb: prefixo `vault:` em accent, separadores `/` roxos, nome com extensão; alternador `editar ⇄ ler` à direita.
5. título: mono, 30px, com prefixo `#` em accent (some o ícone de livro); tags viram chips retos; títulos de seção mostram `##`; tarefas com caixa quadrada; linha ativa em Markdown cru com barra accent (live preview do editor B4).
6. rodapé: barra de status tipo editor (selo `EDIT` em accent, pasta atual, `← N backlinks` em azul, palavras, caracteres, linha:coluna, codificação), full-width, em vez da pílula flutuante no canto.
7. seletor da vault: caixa com rótulo `VAULT`, nome em accent e ícones de trocar/escolher pasta; atalhos (Ctrl+S/N/K) sobre ele.
8. estado vazio: cartão com atalhos (como hoje) mais lista de recentes.

limites: não valida nada no navegador real; ícones são SVG simples, não os finais; "recentes", modos buscar/tags, abas múltiplas, backlinks e L:C são propostas novas ainda sem backend/código.
