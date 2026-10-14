#!/bin/bash
# tools/build.sh <package>... | all
#
# Builds Silica RPMs in a Fedora container (podman if present, otherwise docker): the source
# preparation (git archive, `cargo vendor`, the Dart AOT bundles) and `rpmbuild -ba` run in
# the container, the RPMs and SRPMs land in out/<fedora>/.
#
# Environment:
#   FEDORA     Fedora release of the container (default 45)
#   GH_TOKEN   token that can read the silica-linux repositories (most are private); if unset,
#              `gh auth token` is used when gh is logged in
#   CACHE      cache directory shared between builds (default .cache/): the Flutter SDK, the
#              pub and cargo caches, the prebuilt engine tarball
#   ENGINE     path of a local engine tarball (tools/engine-tarball.sh) to use instead of the
#              GitHub release asset
#   CONTAINER  podman or docker (default: the first one found)
#   IMAGE      container image (default registry.fedoraproject.org/fedora:$FEDORA)
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
fedora="${FEDORA:-45}"
cache="${CACHE:-$root/.cache}"
out="$root/out/fc$fedora"

all=(silica-icons silica-flutter-engine silica-desktop mustache clock
  calculator terminal mail)

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
if [ -z "$token" ] && command -v gh >/dev/null; then
  token="$(gh auth token 2>/dev/null || true)"
fi

mkdir -p "$cache" "$out"

# The prebuilt release engine is a release asset of this repository (docs/engine.md).
for pkg in "$@"; do
  [ "$pkg" = silica-flutter-engine ] || continue
  if [ -n "${ENGINE:-}" ]; then
    cp "$ENGINE" "$cache/$engine_file"
  elif [ ! -f "$cache/$engine_file" ]; then
    GH_TOKEN="$token" gh release download "engine-$engine_ver" \
      -R silica-linux/silica-packages -p "$engine_file" -D "$cache"
  fi
done

# The container runs as root; the files it writes in out/ and .cache/ are handed back to
# the caller at the end (docker; rootless podman maps root to the caller already).
owner="$(id -u):$(id -g)"
"$container" run --rm \
  -e GH_TOKEN="$token" -e OWNER="$owner" -e FEDORA="$fedora" \
  -v "$root:/src:ro,z" -v "$cache:/cache:z" -v "$out:/out:z" \
  "${IMAGE:-registry.fedoraproject.org/fedora:$fedora}" \
  bash /src/tools/container.sh "$@"
echo "build.sh: RPMs in $out"
