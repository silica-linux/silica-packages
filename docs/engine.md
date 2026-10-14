# The Flutter engine package

Silica's embedder needs `libflutter_engine.so` in **release** mode. Google publishes the
embedder engine (`linux-x64-embedder.zip`) only in debug mode, so silica-desktop builds the
release engine from source at the revision of the Flutter SDK it uses
(`crates/embedder/ENGINE_VERSION`; `cargo xtask engine --release`, see
`docs/engine-release.md` in silica-desktop). That build needs a ~10 GB gclient checkout and
about 15 minutes on 20 threads: too heavy for every CI run of this repository.

So the engine is built **once per Flutter version** and published as a release asset here:

1. In silica-desktop: `cargo xtask engine --release` (produces
   `target/flutter-engine/<rev>-release/{libflutter_engine.so,icudtl.dat}`).
2. Here: `tools/engine-tarball.sh <that dir> <Flutter SDK of the same revision>`. It checks
   the revision against `%global engine_rev` of `specs/silica-flutter-engine.spec` and packs the
   library, the ICU data, Flutter's `LICENSE` (BSD-3-Clause) and the engine's third-party
   notices (`bin/cache/pkg/sky_engine/LICENSE` of the SDK, shipped as `NOTICES`).
3. Upload: `gh release create engine-<flutter version> -R silica-linux/silica-packages
   out/silica-flutter-engine-<rev>-x86_64.tar.zst`.

`tools/build.sh silica-flutter-engine` downloads the asset of the release `engine-<version>`
(or takes `ENGINE=<tarball>`), and the spec installs it in `/usr/lib64/silica/engine`.

## When Flutter changes

Update `flutter_version` and `engine_rev` in `specs/silica-flutter-engine.spec` together with
silica-desktop's `ENGINE_VERSION`, rebuild and upload the engine, and rebuild every package
with a Dart AOT bundle: an AOT snapshot only runs on the engine of the same SDK.

## Later

Building the engine in CI (a self-hosted runner, or a scheduled job with a large disk) would
make the package reproducible from source; the tarball keeps the same layout so the spec does
not change.
