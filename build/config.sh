# versões fixadas do build (sourced)
AERO_VERSION="0.3.3"             # versão do produto aerographene (v0.x.x; sem release estável ainda); igual a branding-version.patch e PKGBUILD
UC_TAG="154.0.8037.97-1"          # ungoogled-chromium e portablelinux; Chromium 154.0.8037.97 (Helium 0.18.3.1)
PL_REPO="https://github.com/ungoogled-software/ungoogled-chromium-portablelinux.git"
# alvo de CPU (ADR 0009): avx2 = x86-64-v3 (out/Default, padrão); avx1 = ivybridge (out/Avx1).
# MARCH pode ser sobrescrito por env; out/ e o cache do ccache são separados por alvo.
AERO_CPU="${AERO_CPU:-avx2}"
case "${AERO_CPU}" in
    avx2) MARCH="${MARCH:-x86-64-v3}"; AERO_OUT="Default"; AERO_CCACHE_SUFFIX="" ;;
    avx1) MARCH="${MARCH:-ivybridge}"; AERO_OUT="Avx1";    AERO_CCACHE_SUFFIX="-avx1" ;;
    *) echo "erro: AERO_CPU inválido: ${AERO_CPU} (avx2|avx1)" >&2; exit 1 ;;
esac
