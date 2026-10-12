# roteiro de teste de uso real (v0.1 → v0.2)

Para o dono executar com clique e teclado; o agente não toma o mouse. Rodar nos 4 combos (default/pixelized × sidebar/topbar) com o pacote da release, perfil novo (`--user-data-dir=/tmp/teste-<combo>`). Anotar por item: ok, falha (com o que aconteceu) ou não testado. Falhas viram issue ou entrada em `docs/NOITE-*.md`.

## spaces (ADR 0005)

1. criar um segundo space pelo avatar/seletor de perfil.
2. trocar de space pelo avatar: a janela troca no mesmo lugar e tamanho.
3. tentar abrir o mesmo space em duas janelas: deve focar a existente.
4. abrir um space à parte em outra janela.
5. pinned e abas de um space não aparecem no outro.
6. fechar e reabrir o navegador: cada space volta com seus pinned.

## pinned e pastas

1. fixar uma aba pelo menu de contexto da aba (item "fixar" visível, com ícone).
2. clique direito num pinned: abrir, fechar, mover para pasta, renomear, desafixar.
3. criar pasta pelo menu de contexto da barra; renomear; excluir (pinned voltam para o nível de cima).
4. arrastar pinned (aberto e fechado) para uma pasta: entra no fim e a pasta abre.
5. abrir/fechar pasta no topbar e conferir a mesma gaveta aberta/fechada na sidebar.
6. fechar a aba de um pinned: vira pinned fechado (tracejado); clicar reabre do zero.
7. sidebar: arrastar a borda para redimensionar; a grade se rearranja; largura do pinned mostra o rótulo.

## command bar

1. clique na URL e Ctrl+L abrem o painel.
2. digitar texto: aparecem busca, URL, abas abertas, pinned, histórico, cada um com ícone do tipo.
3. comando `[/]`: listar e executar um.
4. Esc fecha; Enter abre; setas navegam.

## peek

1. link com `target=_blank` abre em peek (70% x 85%, centrado), sem criar aba.
2. `window.open` (popup) abre em peek.
3. promover o peek a aba.
4. fechar o peek com Esc/clique fora.

## split view

1. arrastar uma aba sobre a página cria split.
2. redimensionar a divisória; fechar um lado.
3. três abas em split, se suportado.

## NTP e páginas internas

1. nova aba: relógio, saudação, campo foca a omnibox; Personalizar abre configurações de aparência.
2. chrome://history, chrome://settings, segurança/privacidade seguem o tema ativo (raio, cores, contorno).
3. trocar tema e reiniciar: as páginas mudam junto.

## dado frio

1. com perfil com histórico antigo (ou prazo reduzido), conferir que histórico/favicons frios continuam pesquisáveis na command bar e no histórico.
2. downloads antigos continuam listados.
