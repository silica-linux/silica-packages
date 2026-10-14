#!/bin/bash
# tools/build.sh <package>... | all
#
# Builds Silica RPMs in a Fedora container (podman if present, otherwise docker): the source
# preparation (git archive, `cargo vendor`, the Dart AOT bundles) and `rpmbuild -ba` run in
# the container, the RPMs and SRPMs land in out/<fedora>/.
#
# Environment:
#   FEDORA     Fedora release of the container (default 44, the current stable release, as silica-os)
#   GH_TOKEN   optional: the silica-linux repositories are public, a token only raises the
#              GitHub rate limits
#   CACHE      cache directory shared between builds (default .cache/): the Flutter SDK, the
#              pub and cargo caches, the prebuilt engine tarball
#   ENGINE     path of a local engine tarball (tools/engine-tarball.sh) to use instead of the
#              GitHub release asset
#   CONTAINER  podman or docker (default: the first one found)
#   IMAGE      container image (default registry.fedoraproject.org/fedora:$FEDORA)
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
fedora="${FEDORA:-44}"
cache="${CACHE:-$root/.cache}"
out="$root/out/fc$fedora"

all=(silica-icons silica-flutter-engine silica-desktop mustache clock
  calculator terminal mail settings)

if [ $# -eq 0 ]; then
  echo "usage: tools/build.sh <package>... | all   (packages: ${all[*]})" >&2
  exit 2
fi
if [ "$1" = all ]; then
  set -- "${all[@]}"
fi
for pkg in "$@"; do
  if [ ! -f "$root/specs/$pkg.spec" ]; then
    echo "build.sh: no specs/$pkg.spec" >&2
    exit 2
  fi
done

engine_ver="$(sed -n 's/^%global flutter_version[[:space:]]*//p' "$root/specs/silica-flutter-engine.spec")"
engine_rev="$(sed -n 's/^%global engine_rev[[:space:]]*//p' "$root/specs/silica-flutter-engine.spec")"
engine_file="silica-flutter-engine-$engine_rev-x86_64.tar.zst"

container="${CONTAINER:-}"
if [ -z "$container" ]; then
  if command -v podman >/dev/null; then container=podman
  elif command -v docker >/dev/null; then container=docker
  else echo "build.sh: neither podman nor docker found" >&2; exit 1
  fi
fi

token="${GH_TOKEN:-}"

mkdir -p "$cache" "$out"

# The prebuilt release engine is a release asset of this repository (docs/engine.md).
for pkg in "$@"; do
  [ "$pkg" = silica-flutter-engine ] || continue
  if [ -n "${ENGINE:-}" ]; then
    cp "$ENGINE" "$cache/$engine_file"
  elif [ ! -f "$cache/$engine_file" ]; then
    curl -fsSL -o "$cache/$engine_file.part" \
      "https://github.com/silica-linux/silica-packages/releases/download/engine-$engine_ver/$engine_file"
    mv "$cache/$engine_file.part" "$cache/$engine_file"
  fi
done

# The container runs as root; the files it writes in out/ and .cache/ are handed back to
# the caller at the end (docker; rootless podman maps root to the caller already).
# TAR_OPTIONS: the Flutter SDK unpacks its artifacts as "root", which under rootless podman
# cannot take the archives' original owners.
owner="$(id -u):$(id -g)"
"$container" run --rm \
  -e GH_TOKEN="$token" -e OWNER="$owner" -e FEDORA="$fedora" \
  -e TAR_OPTIONS=--no-same-owner \
  -v "$root:/src:ro,z" -v "$cache:/cache:z" -v "$out:/out:z" \
  "${IMAGE:-registry.fedoraproject.org/fedora:$fedora}" \
  bash /src/tools/container.sh "$@"
echo "build.sh: RPMs in $out"
