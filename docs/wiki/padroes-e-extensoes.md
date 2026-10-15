# padrões de primeiro uso e extensões

## primeiro uso

- perfil novo abre `aerographene://setup` uma vez (ver [onboarding](onboarding.md)). A tela de primeiro uso nativa do Chromium (seletor de perfil) segue desligada, também com `--force-first-run`.
- origem: `patches/aerographene/first-run-off.patch` (`IsFirstRunEligibleProcess()` devolve `false`). A tela `chrome://setup` e os serviços do Helium (`helium/core/onboarding-page.patch`, `helium/core/services-prefs.patch`) saíram da série em 14/10/2026; o pacote helium-onboarding não é mais baixado.
- o onboarding próprio é `onboarding-setup.patch` (página) mais o disparo em `first-run-off.patch`.

## buscador

- Google é o buscador padrão de perfil novo. Perfil existente não muda: a escolha fica em prefs.
- origem: o ungoogled troca a entrada `google` por "No Search"; `patches/aerographene/defaults-f4.patch` restaura a entrada original.

## loja de extensões

- a extensão [NeverDecaf/chromium-web-store](https://github.com/NeverDecaf/chromium-web-store) (MIT) vem instalada como extensão componente, como o uBlock Origin. Versão 1.5.5.4, `.crx` fixado por sha256 em `build/inner.sh` (`cws_ver`, `cws_sha`); id `ocaahdebbfolfmndjeplogmgcagdmblk`.
- ela adiciona o botão "Add to Chrome" nas páginas da Chrome Web Store e baixa o `.crx`.
- `extension-mime-request-handling` já vale `always-prompt-for-install` por padrão, então o navegador oferece instalar o `.crx` em vez de salvá-lo. Para desligar: `--extension-mime-request-handling=download-as-regular-file`.
- o service worker dela não fica permanente: `patches/aerographene/webstore-lazy.patch` tira de `scripts/background.js` o listener `onStartup`, o alarme de checagem de updates (60 min) e a atualização do selo a cada instalação/remoção. Sem esses gatilhos, o worker só acorda por uso: página da Chrome Web Store (content script e mensagens externas), popup, menu de contexto, evento de download ou de instalação de extensão. Efeito esperado: nenhum renderer extra nem ~16-18 MiB em repouso (a confirmar por build e PSS).
- consequência: não há mais checagem automática de updates de extensões fora da loja nem selo vermelho; "Update all" (popup e menu de contexto do botão) segue manual. O alarme que perfis antigos guardam se limpa na primeira vez que dispara.
- extensão de componente não pode ser removida pela interface. Ela tem privilégio de componente (sem a redução que o uBlock recebe); ver `patches/README.md`.

## atualizar a versão da extensão

1. escolha a release em https://github.com/NeverDecaf/chromium-web-store/releases, baixe `Chromium.Web.Store.crx` e calcule o sha256.
2. troque `cws_ver` e `cws_sha` em `build/inner.sh`; a versão entra no hash da série, então a árvore é re-patcheada.
3. se a `key` do manifest mudar, o id muda: atualize `kChromiumWebStoreComponentId` no patch (id = sha256 da chave DER, 32 hex, a-p).

## estado

Patch aplica com `--fuzz=0` e os alvos afetados compilam no overlay; `webstore-lazy.patch` só passou em dry-run `--fuzz=0` sobre o `background.js` do runner e `node --check`, sem build nem medição de PSS. Não testado no navegador (instalação real de uma extensão da Chrome Web Store pendente).

## resumo para agentes

- primeiro uso: `first-run-off.patch` desliga a FRE nativa e abre `chrome://setup` em perfil novo; a página é do aerographene (`onboarding-setup.patch`, ver `onboarding.md`), sem `components/helium_services` (prefs `helium.services.*`), sem helium-onboarding.

- buscador: `defaults-f4.patch` restaura `google` em `prepopulated_engines.json`.
- loja: componente `third_party/chromium_web_store`, baixado por `build/inner.sh` (`cws_ver`/`cws_sha`), registrado em `ComponentLoader::AddChromiumWebStore`.
- worker lazy: `webstore-lazy.patch` (CRLF) remove onStartup/alarme/updateBadge de `background.js`; ao subir a versão da extensão, reconferir se o patch ainda aplica e se surgiram novos gatilhos de startup.
- mime: `IsOffstoreInstallAllowed` trata a flag ausente como `always-prompt-for-install`.
- não testado no navegador real.
