#!/bin/bash
# aerographene: build no host (runner). Idempotente; cache em $AEROGRAPHENE_WORKDIR.
# Requer no host: git, docker. Tudo o mais roda no container do portablelinux.
# Env: AEROGRAPHENE_WORKDIR (padrão $HOME/aerographene-build), JOBS (padrão auto = nproc no container),
#      AEROGRAPHENE_CCACHE (1 padrão, 0 desliga), AEROGRAPHENE_CCACHE_DIR (padrão $HOME/aerographene-ccache),
#      AEROGRAPHENE_CCACHE_SIZE (padrão 40G),
#      AEROGRAPHENE_PGO (1 padrão, 0 desliga), GOOGLE_API_KEY,
#      GOOGLE_DEFAULT_CLIENT_ID, GOOGLE_DEFAULT_CLIENT_SECRET (opcionais).
set -euo pipefail

AERO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
. "${AERO_ROOT}/build/config.sh"

WORK="${AEROGRAPHENE_WORKDIR:-$HOME/aerographene-build}"
PL_DIR="${WORK}/portablelinux"
CCACHE_HOST="${AEROGRAPHENE_CCACHE_DIR:-$HOME/aerographene-ccache}"
mkdir -p "${WORK}/home" "${WORK}/dist" "${CCACHE_HOST}"

for bin in git docker; do
    command -v "$bin" >/dev/null || { echo "erro: '$bin' não encontrado no host" >&2; exit 1; }
done

echo "== recursos: $(nproc) CPUs; $(free -g | awk '/Mem:/{print $2" GB RAM"}'); disco livre em ${WORK}: $(df -h --output=avail "${WORK}" | tail -1)"

# 1. portablelinux + submódulo ungoogled-chromium fixados na tag
if [ ! -d "${PL_DIR}/.git" ]; then
    git clone --branch "${UC_TAG}" --depth 1 --recurse-submodules --shallow-submodules "${PL_REPO}" "${PL_DIR}"
else
    cur="$(git -C "${PL_DIR}" describe --tags --exact-match 2>/dev/null || true)"
    if [ "${cur}" != "${UC_TAG}" ]; then
        git -C "${PL_DIR}" fetch --depth 1 origin tag "${UC_TAG}"
        git -C "${PL_DIR}" checkout -f "${UC_TAG}"
        git -C "${PL_DIR}" submodule update --init --depth 1
        rm -f "${PL_DIR}/build/src/.downloaded.stamp"  # força re-unpack com a nova versão
    fi
fi

# 2. imagem do builder: a do portablelinux + zstd, patch, ccache (mudar a tag :vN ao mudar a camada)
if ! docker image inspect chromium-builder:trixie-slim >/dev/null 2>&1; then
    if docker buildx version >/dev/null 2>&1; then
        (cd "${PL_DIR}/docker" && DOCKER_BUILDKIT=1 docker build -t chromium-builder:trixie-slim -f build.Dockerfile .)
    else
        # sem BuildKit: copia o contexto e troca COPY --chmod/--chown por COPY + RUN (upstream intacto)
        rm -rf "${WORK}/docker-ctx" && cp -r "${PL_DIR}/docker" "${WORK}/docker-ctx"
        sed -i -E 's#^COPY --chmod=([0-9]+) --chown=([^ ]+) ([^ ]+) (.+)$#COPY \3 \4\nUSER root\nRUN chown -R \2 \4 \&\& chmod -R \1 \4\nUSER \2#' "${WORK}/docker-ctx/build.Dockerfile"
        sed -i -E 's#^COPY --chmod=([0-9]+) ([^ ]+) (.+)$#COPY \2 \3\nUSER root\nRUN chmod -R \1 \3\nUSER builder#' "${WORK}/docker-ctx/build.Dockerfile"
        grep -q -- '--chmod' "${WORK}/docker-ctx/build.Dockerfile" && { echo "erro: --chmod restante no Dockerfile" >&2; exit 1; }
        (cd "${WORK}/docker-ctx" && docker build -t chromium-builder:trixie-slim -f build.Dockerfile .)
    fi
fi
if ! docker image inspect aerographene-builder:v2 >/dev/null 2>&1; then
    docker build -t aerographene-builder:v2 - <<'EOF'
FROM chromium-builder:trixie-slim
USER root
RUN apt-get -y update && apt-get -y install zstd patch ccache && rm -rf /var/lib/apt/lists/*
USER builder
EOF
fi

# 3. build dentro do container
docker run --rm -i \
    -u "$(id -u):$(id -g)" \
    -e HOME=/work/home \
    -e JOBS="${JOBS:-auto}" \
    -e AEROGRAPHENE_CCACHE="${AEROGRAPHENE_CCACHE:-1}" \
    -e AEROGRAPHENE_CCACHE_SIZE="${AEROGRAPHENE_CCACHE_SIZE:-40G}" \
    -e AEROGRAPHENE_PGO="${AEROGRAPHENE_PGO:-1}" \
    -e GOOGLE_API_KEY -e GOOGLE_DEFAULT_CLIENT_ID -e GOOGLE_DEFAULT_CLIENT_SECRET \
    -e AERO_SHA="$(git -C "${AERO_ROOT}" rev-parse --short HEAD 2>/dev/null || echo local)" \
    -v "${WORK}:/work" \
    -v "${CCACHE_HOST}:/ccache" \
    -v "${AERO_ROOT}:/aero:ro" \
    aerographene-builder:v2 bash /aero/build/inner.sh

ls -l "${WORK}/dist"
