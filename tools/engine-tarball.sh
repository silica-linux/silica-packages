#!/bin/bash
# tools/engine-tarball.sh <engine dir> <flutter sdk> [out dir]
#
# Packs the release Flutter engine built from source by silica-desktop
# (`cargo xtask engine --release`, docs/engine-release.md there) into the tarball the
# silica-flutter-engine spec uses: libflutter_engine.so, icudtl.dat, Flutter's LICENSE
# (BSD-3-Clause) and the engine's third-party notices (the sky_engine LICENSE of the same
# SDK). Upload it as an asset of the `engine-<flutter version>` release of this repository:
#
#   gh release create engine-3.47.7 -R silica-os/silica-packages \
#     --title "Flutter engine 3.47.7 (release)" out/silica-flutter-engine-<rev>-x86_64.tar.zst
set -euo pipefail

engine="${1:?engine dir, e.g. ~/silica/silica/target/flutter-engine/<rev>-release}"
sdk="${2:?Flutter SDK of the same revision, e.g. ~/sdk/flutter}"
out="${3:-$(cd "$(dirname "$0")/.." && pwd)/out}"
root="$(cd "$(dirname "$0")/.." && pwd)"

rev="$(sed -n 's/^%global engine_rev[[:space:]]*//p' "$root/specs/silica-flutter-engine.spec")"
sdk_rev="$(cat "$sdk/bin/internal/engine.version" 2>/dev/null || true)"
if [ -n "$sdk_rev" ] && [ "$sdk_rev" != "$rev" ]; then
  echo "engine-tarball.sh: the SDK is at engine $sdk_rev, the spec wants $rev" >&2
  exit 1
fi
for f in libflutter_engine.so icudtl.dat; do
  [ -f "$engine/$f" ] || { echo "engine-tarball.sh: $engine/$f missing" >&2; exit 1; }
done
if file "$engine/libflutter_engine.so" | grep -q 'with debug_info'; then
  echo "engine-tarball.sh: warning: the library has debug info (expected a stripped release build)" >&2
fi

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
dir="$stage/silica-flutter-engine-$rev"
mkdir -p "$dir"
cp "$engine/libflutter_engine.so" "$engine/icudtl.dat" "$dir/"
cp "$sdk/LICENSE" "$dir/LICENSE"
cp "$sdk/bin/cache/pkg/sky_engine/LICENSE" "$dir/NOTICES"
echo "$rev" >"$dir/ENGINE_VERSION"

mkdir -p "$out"
tar -C "$stage" --sort=name --owner=0 --group=0 --numeric-owner -cf - "silica-flutter-engine-$rev" \
  | zstd -q -19 -T0 -o "$out/silica-flutter-engine-$rev-x86_64.tar.zst"
echo "$out/silica-flutter-engine-$rev-x86_64.tar.zst"
