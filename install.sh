#!/usr/bin/env bash
# aerographene installer: picks the package for your distro and CPU from the
# latest GitHub release, checks it against SHA256SUMS and installs it.
#   curl -fsSL https://newcortexbr.github.io/aerographene/install.sh | bash
# options (env): AERO_VERSION=v0.3.0  AERO_CPU=avx2|avx1  AERO_FORMAT=arch|debian|fedora|linux
set -euo pipefail
# everything runs inside main so a piped script is fully read before anything
# executes; package managers read answers from the terminal, not from the pipe.
main() {
REPO="newcortexbr/aerographene"
say() { printf '\033[1;34m::\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(uname -s)" = Linux ] || die "aerographene is Linux-only for now."
[ "$(uname -m)" = x86_64 ] || die "only x86_64 builds exist."
command -v curl >/dev/null || die "curl is required."
command -v sha256sum >/dev/null || die "sha256sum is required."

# cpu: avx2 build needs x86-64-v3 (avx2 + bmi2 + fma); otherwise avx1
cpu="${AERO_CPU:-}"
if [ -z "$cpu" ]; then
  flags=$(grep -m1 '^flags' /proc/cpuinfo || true)
  if [[ " $flags " == *" avx2 "* && " $flags " == *" bmi2 "* && " $flags " == *" fma "* ]]; then cpu=avx2
  elif [[ " $flags " == *" avx "* ]]; then cpu=avx1
  else die "your CPU lacks AVX; no build fits it."; fi
fi

# format by package manager
fmt="${AERO_FORMAT:-}"
if [ -z "$fmt" ]; then
  if command -v pacman >/dev/null; then fmt=arch
  elif command -v apt-get >/dev/null; then fmt=debian
  elif command -v dnf >/dev/null; then fmt=fedora
  else fmt=linux; fi
fi
case "$fmt" in
  arch) ext=pkg.tar.zst ;; debian) ext=deb ;; fedora) ext=rpm ;; linux) ext=tar.zst ;;
  *) die "unknown format: $fmt" ;;
esac

# release
if [ -n "${AERO_VERSION:-}" ]; then api="https://api.github.com/repos/$REPO/releases/tags/$AERO_VERSION"
else api="https://api.github.com/repos/$REPO/releases/latest"; fi
json=$(curl -fsSL "$api") || die "could not reach the GitHub release API."
tag=$(printf '%s' "$json" | grep -m1 '"tag_name"' | sed -E 's/.*"tag_name": *"([^"]+)".*/\1/')
[ -n "$tag" ] || die "no published release found."

asset="$cpu-$fmt--aerographene-$tag.$ext"
base="https://github.com/$REPO/releases/download/$tag"
printf '%s' "$json" | grep -q "\"name\": *\"$asset\"" || die "release $tag has no $asset."

tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
say "aerographene $tag · $cpu · $fmt"
curl -fL --progress-bar -o "$tmp/$asset" "$base/$asset"
curl -fsSL -o "$tmp/SHA256SUMS" "$base/SHA256SUMS"
( cd "$tmp" && grep " $asset\$" SHA256SUMS | sha256sum -c --status ) || die "checksum mismatch, aborting."
say "checksum ok"

sudo_() { if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo "$@"; fi; }
if { : </dev/tty; } 2>/dev/null; then in=/dev/tty; yes=(); else in=/dev/null; yes=(--noconfirm); fi
case "$fmt" in
  arch)   sudo_ pacman -U --needed "${yes[@]}" "$tmp/$asset" <"$in" ;;
  debian) sudo_ apt-get install -y "$tmp/$asset" <"$in" ;;
  fedora) sudo_ dnf install -y "$tmp/$asset" <"$in" ;;
  linux)
    command -v zstd >/dev/null || die "zstd is required for the tarball."
    dest="${XDG_DATA_HOME:-$HOME/.local/share}/aerographene"
    mkdir -p "$dest" "$HOME/.local/bin"
    tar --zstd -xf "$tmp/$asset" -C "$dest" --strip-components=1
    ln -sf "$dest/aerographene" "$HOME/.local/bin/aerographene"
    say "installed to $dest; run: aerographene" ;;
esac
say "done."
}
main "$@"
