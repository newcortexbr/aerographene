#!/usr/bin/env bash
# Anexa os zips Windows ao draft da release, regenera SHA256SUMS cobrindo TODOS os assets e,
# só com --publish, publica como release normal (não pre-release) e latest.
# Roda no runner (ssh cezanne), onde estão ~/aerographene-win/dist/<cpu>/ e o gh autenticado.
# Pré-requisito: draft <tag> já criado pelo workflow release.yml (cpu avx2) com os assets Linux.
# Uso: build/release-assets.sh vX.Y.Z [--publish] [--notes docs/releases/vX.Y.Z.md]
#   AERO_WIN_DIST  padrão ~/aerographene-win/dist
#   AERO_WIN_CPUS  padrão "avx2 avx1"
#   AERO_REPO      padrão newcortexbr/aerographene
set -euo pipefail

tag="${1:?uso: $0 vX.Y.Z [--publish] [--notes arquivo]}"; shift
[[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "tag inválida: $tag" >&2; exit 1; }
publish=0; notes=""
while [ $# -gt 0 ]; do
  case "$1" in
    --publish) publish=1 ;;
    --notes) notes="${2:?}"; shift ;;
    *) echo "opção desconhecida: $1" >&2; exit 1 ;;
  esac
  shift
done
repo="${AERO_REPO:-newcortexbr/aerographene}"
dist="${AERO_WIN_DIST:-$HOME/aerographene-win/dist}"
cpus="${AERO_WIN_CPUS:-avx2 avx1}"

[ "$(gh release view "$tag" --repo "$repo" --json isDraft -q .isDraft)" = true ] \
  || { echo "erro: $tag não existe como draft" >&2; exit 1; }

work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT

# 1. zips Windows com o nome final
for cpu in $cpus; do
  src="$dist/$cpu/aerographene-win-$cpu.zip"
  [ -s "$src" ] || { echo "erro: falta $src" >&2; exit 1; }
  cp -- "$src" "$work/${cpu}-windows--aerographene-${tag}.zip"
done

# 2. assets Linux atuais do draft (menos SHA256SUMS) para o hash cobrir tudo
pargs=()
while IFS= read -r n; do pargs+=(-p "$n"); done < <(gh release view "$tag" --repo "$repo" --json assets \
  -q '.assets[].name | select(. != "SHA256SUMS")')
[ ${#pargs[@]} -gt 0 ] || { echo "erro: draft sem assets Linux" >&2; exit 1; }
gh release download "$tag" --repo "$repo" -D "$work" "${pargs[@]}"

# 3. SHA256SUMS de todos os assets
(cd "$work" && sha256sum -- * | grep -v ' SHA256SUMS$' | sort -k2 > SHA256SUMS.new && mv SHA256SUMS.new SHA256SUMS)
cat "$work/SHA256SUMS"

# 4. sobe (windows + SHA256SUMS novo)
gh release upload "$tag" --repo "$repo" --clobber "$work"/*-windows--*.zip "$work/SHA256SUMS"

# 5. publica, se pedido
if [ "$publish" = 1 ]; then
  [ -n "$notes" ] && [ -s "$notes" ] || { echo "erro: --publish exige --notes com arquivo não vazio" >&2; exit 1; }
  gh release edit "$tag" --repo "$repo" --notes-file "$notes" --title "aerographene $tag" \
    --draft=false --prerelease=false --latest
fi
