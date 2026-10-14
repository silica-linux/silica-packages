#!/bin/bash
# Runs inside the Fedora container started by tools/build.sh: /src is this repository
# (read-only), /cache the shared cache, /out the destination of the RPMs.
#
# For each package it prepares the sources its spec declares, then runs `rpmbuild -ba`:
#   %global srcrepo <repo>      repository under github.com/silica-linux
#   %global commit <ref>        commit or tag
#   # prepare: rust <dir>       `cargo vendor` of the workspace in <dir> (offline rpmbuild)
#   # prepare: flutter <dir>    the Flutter app in <dir>, built as an AOT bundle
#                               (flutter_assets + libapp.so) with the pinned Flutter SDK
#   # prepare: engine           the prebuilt release engine from /cache (tools/build.sh)
# Every other file in specs/ named by a Source tag (session scripts, D-Bus files) is copied
# as is.
set -euo pipefail

top=/work/rpmbuild
mkdir -p "$top"/{SOURCES,SPECS,BUILD,RPMS,SRPMS} /work/git

log() { echo "container.sh: $*" >&2; }

# Base tools, once per container.
dnf -y -q install rpm-build rpmdevtools dnf5-plugins git-core zstd tar gzip unzip xz \
  which findutils curl cargo rust >/dev/null
git config --global --add safe.directory '*'
git config --global advice.detachedHead false

flutter_version="$(sed -n 's/^%global flutter_version[[:space:]]*//p' /src/specs/silica-flutter-engine.spec)"
flutter_root="/cache/flutter-$flutter_version"
export PUB_CACHE=/cache/pub CARGO_HOME=/cache/cargo
export FLUTTER_SUPPRESS_ANALYTICS=true CI=true

global() { sed -n "s/^%global $1[[:space:]]*//p" "$2" | head -n1; }

# The repository at the ref, checked out in /work/git/<repo>-<ref>.
checkout() {
  local repo="$1" ref="$2" dir="/work/git/$1-$2"
  if [ ! -d "$dir/.git" ]; then
    local url="https://github.com/silica-linux/$repo.git"
    if [ -n "${GH_TOKEN:-}" ]; then
      url="https://x-access-token:$GH_TOKEN@github.com/silica-linux/$repo.git"
    fi
    git init -q "$dir"
    git -C "$dir" fetch -q --depth 1 "$url" "$ref"
    git -C "$dir" checkout -q FETCH_HEAD
  fi
  echo "$dir"
}

slug() { if [ "$1" = . ]; then echo root; else echo "${1//\//-}"; fi; }

flutter_sdk() {
  if [ ! -x "$flutter_root/bin/flutter" ]; then
    log "Flutter $flutter_version in $flutter_root"
    rm -rf "$flutter_root"
    git clone -q --depth 1 --branch "$flutter_version" \
      https://github.com/flutter/flutter.git "$flutter_root"
  fi
  # The engine artifacts for Linux: gen_snapshot and the product SDK for the AOT build.
  "$flutter_root/bin/flutter" --version >/dev/null
  "$flutter_root/bin/flutter" precache --linux --no-android --no-ios --no-web \
    --no-macos --no-windows --no-fuchsia >/dev/null
}

# The AOT bundle of the Flutter app in $1, as `cargo xtask bundle --release` builds it in
# silica-desktop (xtask/src/flutter.rs, bundle_release).
dart_bundle() {
  local app="$1" tarball="$2" stage
  flutter_sdk
  stage="$(mktemp -d)"
  local cache="$flutter_root/bin/cache"
  local package
  package="$(sed -n 's/^name:[[:space:]]*//p' "$app/pubspec.yaml" | head -n1)"
  (
    cd "$app"
    "$flutter_root/bin/flutter" pub get >/dev/null
    "$flutter_root/bin/flutter" build bundle --release --asset-dir "$stage/flutter_assets" >/dev/null
    "$cache/dart-sdk/bin/dartaotruntime" \
      "$cache/dart-sdk/bin/snapshots/frontend_server_aot.dart.snapshot" \
      --sdk-root "$cache/artifacts/engine/common/flutter_patched_sdk_product/" \
      --target=flutter --aot --tfa --no-print-incremental-dependencies \
      -Ddart.vm.product=true -Ddart.vm.profile=false \
      --packages .dart_tool/package_config.json \
      --output-dill "$stage/app.dill" "package:$package/main.dart"
  )
  "$cache/artifacts/engine/linux-x64-release/gen_snapshot" \
    --deterministic --snapshot_kind=app-aot-elf --strip \
    "--elf=$stage/libapp.so" "$stage/app.dill"
  rm -f "$stage/app.dill"
  tar -C "$stage" --sort=name --owner=0 --group=0 --numeric-owner -cf - flutter_assets libapp.so \
    | zstd -q -19 -T0 -o "$tarball"
  rm -rf "$stage"
}

build() {
  local pkg="$1" spec="/src/specs/$1.spec"
  local repo ref src
  repo="$(global srcrepo "$spec")"
  ref="$(global commit "$spec")"
  log "$pkg${repo:+: $repo at $ref}"
  cp "$spec" "$top/SPECS/"

  if [ -n "$repo" ]; then
    src="$(checkout "$repo" "$ref")"
    git -C "$src" archive --format=tar.gz --prefix="$repo-$ref/" HEAD \
      >"$top/SOURCES/$repo-$ref.tar.gz"
  fi

  local kind dir
  while read -r kind dir; do
    case "$kind" in
      rust)
        log "$pkg: cargo vendor in $dir"
        (cd "$src/$dir" && rm -rf vendor && cargo vendor --locked --versioned-dirs -q vendor >/dev/null)
        tar -C "$src/$dir" --sort=name --owner=0 --group=0 --numeric-owner -cf - vendor \
          | zstd -q -19 -T0 -o "$top/SOURCES/$repo-$ref-vendor-$(slug "$dir").tar.zst"
        ;;
      flutter)
        log "$pkg: Dart AOT bundle of $dir"
        dart_bundle "$src/$dir" "$top/SOURCES/$repo-$ref-dart-$(slug "$dir").tar.zst"
        ;;
      engine)
        local rev
        rev="$(global engine_rev "$spec")"
        cp "/cache/silica-flutter-engine-$rev-x86_64.tar.zst" "$top/SOURCES/"
        ;;
    esac
  done < <(sed -n 's/^# prepare:[[:space:]]*//p' "$spec")

  # Local sources (session script, D-Bus and portal files) live next to the specs.
  local file
  for file in $(rpmspec -P "$spec" 2>/dev/null | sed -n 's/^Source[0-9]*:[[:space:]]*//p'); do
    file="${file##*/}"
    if [ -f "/src/specs/files/$file" ]; then
      cp "/src/specs/files/$file" "$top/SOURCES/"
    fi
  done

  dnf -y -q builddep "$top/SPECS/$pkg.spec" >/dev/null
  rpmbuild --define "_topdir $top" -ba "$top/SPECS/$pkg.spec"
  # Copied after each package, so a later failure keeps what was built.
  find "$top/RPMS" "$top/SRPMS" -name '*.rpm' -exec mv -t /out {} +
  chown -R "${OWNER:-0:0}" /out 2>/dev/null || true
}

for pkg in "$@"; do
  build "$pkg"
done

chown -R "${OWNER:-0:0}" /cache 2>/dev/null || true
log "done: $*"
