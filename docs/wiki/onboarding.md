# onboarding (aerographene://setup)

página de primeiro uso. Abre uma vez por perfil (space) novo, no lugar da página nova aba, e deixa ajustar o que o navegador de fato oferece. Tudo é opcional e tudo pode ser mudado depois nas configurações.

## quando abre

- perfil novo (`Profile::IsNewProfile()`: o navegador ainda não foi encerrado desde que o perfil foi criado), sem URL na linha de comando e sem `--no-first-run`. O teste está em `StartupBrowserCreatorImpl::DetermineStartupTabs`, no `first-run-off.patch`, depois do ramo de anônimo/convidado/pós-crash, que sai antes: janela anônima e de convidado nunca abrem a página (a própria WebUI também recusa perfil off-the-record, como `aerographene://notes`).
- some para sempre ao concluir: a pref de perfil `aerographene.onboarding_completed` (boolean, padrão `false`) vira `true` em "finish" e em "skip, use defaults". Com ela `true` a página não abre no startup.
- perfil que já existia antes desta versão não é novo, então não vê a página. Quem fecha a aba sem concluir também não a vê de novo no próximo início (o perfil deixou de ser novo); a página continua acessível digitando `aerographene://setup`.
- a FRE nativa do Chromium continua desligada (`IsFirstRunEligibleProcess()` devolve `false`).

## passos

Os oito passos do mockup aprovado (`theming/mockups/perfis-onboarding/03-onboarding`), numa página só com índice à esquerda; `j`/`k` movem, `enter` avança.

- 00 hello: "light. fast. pretty."; "start" vai ao passo 01, "skip, use defaults" conclui sem mudar nada.
- 01 theme: um cartão por tema que `ListThemes` devolve (`default`, `pixelized` e os temas válidos da pasta de temas). Grava a pref `aerographene.theme`, a mesma de configurações > aparência; o tema vale no próximo início (a página avisa). Não há cartão "system": esse tema não existe.
- 02 defaults: buscador (modelo de search engines; só entradas pré-preenchidas, não extensões nem personalizados) e "tornar o aerographene o navegador padrão" (`shell_integration::DefaultBrowserWorker`; a chave fica desligada e travada quando o sistema não permite definir por aqui, e ligada e travada quando já é o padrão). A loja de extensões é só texto: a extensão chromium-web-store vem embutida e não tem opção.
- 03 o: notes: explica `o:` e liga "choose…" ao seletor de pasta, que grava `aerographene.notes.vault_path`, a mesma pref de `aerographene://notes`.
- 04 t: terminal e 05 command bar: só texto e um exemplo estático (nada executa). Ctrl+T abre a command bar vazia; Ctrl+L ou clique na barra abrem com o endereço atual. Sem controle: não há opção de atalho.
- 06 privacy: crash reports é só texto ("none are sent": o upload fica desligado pelo `disable-crash-reporter` do ungoogled, `patches/README.md`); search suggestions é uma chave de verdade (`search.suggest_enabled`); uBlock Origin é só texto ("bundled as a built-in extension": `ublock-install-as-component`).
- 07 import: "import…" abre `chrome://settings/importData` numa aba nova (o importador existente, que inclui Chrome, Firefox e o importador do Arc da série) e a página continua aberta; "finish" conclui. Não há lista de perfis nem caixas de seleção: o importador de configurações é quem enumera.

Concluir marca a pref e leva a mesma aba à nova aba.

## regras de implementação

- nada de rede: CSP `default-src 'none'`, `script-src`/`style-src`/`img-src 'self'`, `connect-src 'none'`. Sem fonte nem imagem externas; o wordmark (`wordmark.svg`, só texto, sem ícone) vem do pacote. A tipografia é `JetBrains Mono` se estiver instalada no sistema, senão `DejaVu Sans Mono`/monospace (a fonte não é empacotada no Linux).
- sem `innerHTML` (Trusted Types do WebUI).
- as mensagens do `SetupHandler` só valem se vierem do frame principal comitado em `chrome://setup/`; tema e buscador são validados contra as listas do navegador (a página nunca manda caminho nem URL); mensagem malformada vinda da própria página rejeita o callback (`bad_request`) em vez de deixar a promessa pendente; `setSearchEngine` aceita o buscador atual (no-op); o seletor de pasta exige gesto do usuário.
- recursos: `chrome/browser/resources/aero_setup/{setup.html,setup.css,setup.js,wordmark.svg}`, ids `IDR_AERO_SETUP_*` no `browser_resources.grd`.

## estado e limites

- série aplica com `--fuzz=0` e os `.cc` novos/alterados passam `-fsyntax-only` com as flags de `out/Default` (ver `patches/README.md`); a página passa `tests/onboarding/run.sh` com backend falso no Chrome headless.
- não verificado: a página no navegador real (CSP e Trusted Types do WebUI, o handler C++, o seletor de pasta, definir como padrão de verdade, abrir a importação); o disparo no startup num perfil novo criado pela interface de spaces (o código assume que o caminho de abrir janela de um perfil novo passa por `DetermineStartupTabs`); Windows (a chave de navegador padrão e o seletor não foram exercitados).
- decisão sobre perfil já existente: não mostrar. Se o dono quiser mostrar uma vez para quem atualiza, é trocar `IsNewProfile()` por outra condição.

## resumo para agentes

- host `setup` (`chrome://setup`, mostrado como `aerographene://setup`): `AeroSetupUIConfig`/`AeroSetupUI` em `chrome/browser/ui/webui/aero_setup/`, `SetupHandler` com mensagens `getInfo`, `getThemes`, `setTheme`, `getSearch`, `setSearchEngine`, `setSuggest`, `pickVault`, `getDefaultBrowser`, `setDefaultBrowser`, `openImport`, `complete` (todas com id de callback; resposta por `cr.webUIResponse`, como `aero_notes`).
- pref `aerographene.onboarding_completed` (`prefs::kAerographeneOnboardingCompleted`, registrada em `browser_prefs.cc`, Linux e Windows); URL em `chrome::kChromeUISetupURL`.
- disparo: `first-run-off.patch` em `DetermineStartupTabs`: `IsNewProfile()` e sem URL de linha de comando e sem `--no-first-run` e pref `false`; anônimo, convidado e pós-crash saem antes.
- patches: `onboarding-setup.patch` (página, handler, pref, URL, registro, grd, BUILD.gn) antes de `first-run-off.patch` (disparo) em `patches/series`.
- só ligar a controles que existem: tema (`aerographene.theme`), buscador (`TemplateURLService`), sugestões (`search.suggest_enabled`), pasta de notas (`aerographene.notes.vault_path`), navegador padrão (`DefaultBrowserWorker`), importação (`chrome://settings/importData`). Crash reports, uBlock e loja de extensões são texto; não criar toggle sem efeito.
- ao acrescentar um passo ou controle: confirmar no repositório que o recurso existe, atualizar `tests/onboarding/` (mock e teste) e esta página.
- teste: `tests/onboarding/run.sh <dir aero_setup> [chrome-headless-shell]` (backend falso; não prova CSP nem o handler C++).
- não testado no navegador real.
