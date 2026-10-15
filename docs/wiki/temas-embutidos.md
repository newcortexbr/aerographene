# temas embutidos

os oito temas compilados no aerographene e como escolher um.

## lista

- `default` e `pixelized`: desde a v0.2.
- `metro-v2`, `e-ink-gb`, `graphite`, `classical`, `e-ink` e `cli`: novos na v0.3.3, definidos como `ThemeData` em `patches/aerographene/theme-builtin-approved.patch`.
- todos escuros; não há alternância claro/escuro.
- sem fontes empacotadas: `e-ink-gb` pede Pixelify Sans e `graphite` pede Doto; sem a fonte instalada o sistema usa a reserva (Consolas no Windows).

## como usar

- troca em `chrome://settings/appearance`; vale após reiniciar. O onboarding (`aerographene://setup`) também oferece o tema.
- os oito nomes são reservados: importar um `.aerotheme` ou `--import-theme` com um desses nomes (sem diferenciar caixa) é recusado.
- `theme.json` e tema de extensão seguem valendo por cima do embutido; ver [temas](temas.md).

## estado

- compilado na build Linux avx2 verde (run 38676659389, commit `fc39b55`); smoke de CI tira print por tema.
- não verificado visualmente no navegador; Windows não testado.
- lacuna: a mensagem de erro de nome reservado (`IDS_SETTINGS_AEROGRAPHENE_THEME_IMPORT_ERROR_RESERVED`) só existe em inglês.

## resumo para agentes

- oito embutidos: default, pixelized, metro-v2, e-ink-gb, graphite, classical, e-ink, cli; todos dark only.
- código em `theme-builtin-approved.patch`; nomes reservados em `settings-theme-import.patch` e `theme-repo.patch`.
- sem fonte empacotada: não afirmar que Pixelify Sans/Doto aparecem.
- não afirmar verificação visual no navegador; só compilação e smoke de CI.
