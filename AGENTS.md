# AGENTS.md

## projeto e contratos

- aerographene: navegador Linux x86-64-v3, série própria de patches sobre ungoogled-chromium, com partes do Helium e foco em desempenho. Licença GPL-3.0.
- este repositório contém patches, scripts Bash, harness Python e mockups; não contém a árvore completa do Chromium nem um aplicativo Node.js.
- antes de implementar produto, leia `docs/SCOPE.md` e `CONTEXT.md`; consulte `docs/adr/` para decisões de base, CPU, CI, spaces e sync.
- ao retomar trabalho, leia `docs/NOITE-20261005.md`: a seção de sequência acordada complementa os retratos históricos de estado. Confirme branch, arquivos e runs atuais antes de agir.

## mapa do repositório

- `patches/series`: ordem dos patches ativos; `patches/README.md`: origem, licença, dependências e patches não portados.
- `patches/helium/`, `patches/brave/`, `patches/aerographene/`: patches importados e próprios.
- `build/`: configuração, flags GN e preparação/compilação via portablelinux em Docker.
- `.github/workflows/`: build, diagnóstico de cache e release.
- `bench/`: harness Python, download de navegadores e páginas sintéticas; resultados locais fora do git.
- `packaging/arch/`: PKGBUILD, metadados e desktop entry.
- `theming/1/`: estudos HTML/PNG; `DECISIONS.md` registra feedback e aprovação. Arquivos locais podem ainda não estar rastreados.

## build e comandos

- antes de alterar build/cache/empacotamento, leia `docs/BUILD.md`, `build/inner.sh` e o workflow correspondente.
- dependências do host de build: `git` e `docker`; o restante é preparado no container pelo script. Não há instalação npm nem servidor de desenvolvimento definido.
- comando canônico no runner: `bash build/build.sh`; jobs e PGO vêm dos inputs de `.github/workflows/build.yml`.
- compilação completa fica no runner Cezanne (Ubuntu 24.04 bare metal desde 10/10/2026; antes WSL2), labels `self-hosted`, `linux`, `intense`; não iniciar Chromium na máquina local Comet Lake.
- os três runners compartilham host e cache, confirmado pelo diagnóstico `cache-sharing-check`. Preserve `out/Default`; symlinks entre runners não são necessários.
- mantenha exclusão mútua pelo grupo de concurrency `build`: builds simultâneas nesse cache não foram validadas.
- dispatch de build e publicação exigem pedido explícito; pushes em `main` que tocam build/patches/workflow também disparam compilação.

- antes de mandar patches ao runner, rode a pré-checagem estática da série: hunks bem formados, identificadores novos (`IDS_*`, `VIEW_ID_*`, prefs, features, constantes) declarados em algum patch ou confirmados no upstream, `.cc` novos em `BUILD.gn`, includes resolvidos. Build de 8h não é ferramenta de descoberta de erro.
- para confirmar correção de erro de compilação, compile só o alvo afetado (ex.: `ninja -C out/Default obj/<caminho>.o`) antes de pedir a build completa; a build oficial (ThinLTO, PGO) fica para validar o pacote.

## checagens e desempenho

- antes de medir, leia `bench/README.md` e `docs/BASELINE.md` para comandos, condições e limites.
- rodada rápida documentada: `python3 bench/harness.py --quick --tabs 10`.
- medir no Comet Lake com perfil `performance`, sem carga pesada paralela; não comparar diretamente com medições no runner do Cezanne.
- a linha de base existente tem limites: perfil novo não equivale a disco frio; Speedometer não está automatizado.
- regra do produto: nenhuma mudança piora mais de 2% a linha de base; isolar mudanças para atribuir efeitos.
- não há suíte genérica de testes/lint configurada na raiz. Defina checagens adequadas ao alvo; diferencie aplicação de patch, compilação, inicialização do pacote e medição de desempenho.
- build aprovada requer artefato gerado e smoke test; patch aplicado ou mockup aprovado não comprova funcionalidade no navegador.

## mudanças e mockups

- preserve origem/licença dos patches e confira dependências/ordem em `patches/series`; alterações persistentes pertencem à série, não apenas à árvore gerada do runner.
- siga as convenções dos arquivos vizinhos: scripts Bash com `set -euo pipefail`, patches no formato existente e Python do harness sem dependências externas desnecessárias.
- para trabalho visual, leia as últimas entradas de `theming/1/DECISIONS.md`; `SPECS.md` contém decisões históricas supersedidas.
- mockups usam conteúdo fictício: não executar comandos de terminais ilustrativos, acessar dados privados nem alegar integração real de notas/mcode.
- aprovação visual tem escopo: não estendê-la a outros estudos ou a contratos de integração.

## repositório público, README, release e wiki

- o repo `newcortexbr/aerographene` é público: tudo em `main` fica visível; nada de dados privados, caminhos pessoais ou segredos.
- ao entregar função nova ou mudar estado do projeto, atualize o README abaixo da linha "Content above was 100% human-written" (roadmap, docs, thanks). Nunca edite o texto humano acima dessa linha; única exceção autorizada pelo dono: o bloco de gráficos de benchmark no topo do README.
- vault (`~/vault`, MCP `vault`): registre fatos, decisões, runs e aprendizados duráveis sempre que puder, com o máximo de tags de assunto pertinentes, para achar depois.
- nomes de assets de release: `aerographene-vX.Y.Z-avx2-linux.tar.zst`, `-avx1-linux`, `-windows` etc.
- ao criar ou editar release, consulte no vault `agents/procedimentos/navegador-fork-formato-release.md` e siga o formato; se mudar o formato, atualize a nota.
- documente cada função nova em `docs/wiki/` (pt-BR, uma página por assunto, com seção final "resumo para agentes") e linke na seção docs do README.

## git e segurança

- branch padrão: `main`. Cada versão tem uma branch própria (`v0.2`, `v0.3`...) criada da `main`; ela é apagada depois do merge com testes verdes. Docs avulsas podem ir direto na `main`. Crie branch de trabalho a partir da base apropriada, preservando alterações locais do usuário.
- commits existentes usam prefixos descritivos como `ci:`, `build:`, `patches:` e `docs:`; faça commit/push apenas quando solicitado.
- antes de mudar CI, leia `docs/adr/0004-ci-runner-self-hosted.md`: só o dono dispara; nunca executar código de forks com `pull_request`/`pull_request_target` no self-hosted. PRs externos ficam fechados.
- release tem workflow próprio e gera draft; build não autoriza publicação.
- credenciais ficam fora do código e dos logs; para sync consulte o ADR 0006 sem ler ou expor valores de secrets.
