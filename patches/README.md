# patches/

Patches portados do Helium (https://github.com/imputnet/helium, tag 0.18.3, commit `57a40ad82583d21787cff0500150539ce54c5960`, Chromium 154.0.8037.97) para a série do aerographene (ADR 0001, ADR 0002). Cada arquivo tem um cabeçalho de origem no topo (texto antes do primeiro `---`, ignorado por patch/quilt). O conteúdo do diff é o original. A ordem em `series` é a do Helium.

Os patches do Helium assumem a base do Helium: ungoogled-chromium (Helium mantém cópia em `patches/ungoogled-chromium/`) e os patches de `inox-patchset`, `iridium-browser` e `debian` já aplicados. O aerographene usa o ungoogled upstream como base (ADR 0001), então a versão do ungoogled tem de casar com a do Helium 0.18.3 (merge de 154.0.8037.57).

Estado: aplicação não verificada; será verificada no primeiro build (o Chromium não foi baixado). As dependências abaixo foram achadas por análise textual: um patch depende de outro anterior da série se suas linhas de contexto/remoção coincidem com linhas adicionadas pelo anterior, ou se usa arquivo criado por ele. É heurística; pode sobrar dependência de contexto e faltar alguma.

| patch | origem | licença | propósito | dependências (portadas) | risco |
|---|---|---|---|---|---|
| `helium/core/services-prefs.patch` | Helium `patches/helium/core/services-prefs.patch` | GPL-3.0 | prefs/componente helium_services; dependência de contexto de lazy-session-restore | - | 8/24 arquivos também tocados por outros patches portados; traz UI de settings (services_page) que o aerographene talvez não queira |
| `helium/core/onboarding-page.patch` | Helium `patches/helium/core/onboarding-page.patch` | GPL-3.0 | página de onboarding; dependência de contexto de lazy-session-restore (include em startup_browser_creator_impl.cc) | `helium/core/services-prefs.patch` | 9/26 arquivos também tocados por outros patches portados; muda o primeiro uso; avaliar rebasear o hunk de lazy-session-restore e remover |
| `helium/core/memory-saving-by-default.patch` | Helium `patches/helium/core/memory-saving-by-default.patch` | GPL-3.0 | Memory Saver ligado por padrão | - | 0/1 arquivos também tocados por outros patches portados |
| `helium/core/flags-setup.patch` | Helium `patches/helium/core/flags-setup.patch` | GPL-3.0 | infra de flags do Helium (helium_flag_entries.h) | - | 2/3 arquivos também tocados por outros patches portados |
| `helium/core/add-low-power-framerate-flag.patch` | Helium `patches/helium/core/add-low-power-framerate-flag.patch` | GPL-3.0 | flag para o limite de fps no modo economia de energia | `helium/core/flags-setup.patch` | 2/3 arquivos também tocados por outros patches portados |
| `helium/core/infinite-tab-freezing.patch` | Helium `patches/helium/core/infinite-tab-freezing.patch` | GPL-3.0 | congelamento de abas sem limite de tempo | - | 0/1 arquivos também tocados por outros patches portados |
| `helium/core/lazy-session-restore.patch` | Helium `patches/helium/core/lazy-session-restore.patch` | GPL-3.0 | restaura abas da sessão sob demanda (sem carregar tudo) | `helium/core/onboarding-page.patch` | 1/15 arquivos também tocados por outros patches portados; grande (680 linhas), toca startup/sessions |

## não portados

- `ungoogled-chromium/disable-ai.patch` e `ungoogled-chromium/extensions-manifestv2.patch`: já estão no ungoogled upstream (`patches/core/ungoogled-chromium/`); o Helium só os herda. Entram pela base.
- `noise/*` e `zen-mode*`: fora do escopo (docs/SCOPE.md).
- `ublock-reconfigure-defaults`, `ublock-helium-services`, `ublock-dns-uncloaking`, `ublock-show-in-settings`, `fixups-component-setup`: não são dependências de `ublock-install-as-component`; avaliar depois (fixups cuida da integração com a Chrome Web Store).
- O código do uBlock Origin em si vem de `deps.ini` (`[ublock_origin]`, `third_party/ublock`) e de scripts do Helium, fora de `patches/`; o build precisa baixá-lo.
- `brave/fix-component-content-settings-store`, e o restante de `helium/ui` (compact, toolbar-actions, horizontal-tabs, etc.): sem dependência achada.
- `brave/*` entram só como dependência: `tab-cycling-mru-impl` (UI) e `chrome-importer-files`/`custom-importer` (importador do Arc).
