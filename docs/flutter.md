# Flutter apps in RPMs

The shell and the apps are Flutter projects run by Silica's embedder in release mode: each
needs its `flutter_assets` folder and `libapp.so` (the Dart code compiled ahead of time)
next to it.

## Where the Dart code is compiled

`tools/container.sh` compiles it while preparing the sources, not in `rpmbuild`:

- The build needs the Flutter SDK at the pinned version (`flutter_version` in
  `specs/silica-flutter-engine.spec`), its Linux release artifacts (`gen_snapshot`, the
  product platform SDK) and the Dart packages from pub.dev and GitHub. None of them is in
  Fedora, and they would make every source RPM weigh more than a gigabyte.
- The steps are those of `cargo xtask bundle --release` in silica-desktop
  (`xtask/src/flutter.rs`): `flutter build bundle --release` for the assets, the frontend
  server in AOT mode for the kernel, `gen_snapshot --snapshot_kind=app-aot-elf --strip` for
  `libapp.so`.
- The result, `<repo>-<commit>-dart-<dir>.tar.zst`, is a source of the RPM, so the source
  RPMs stay self-contained and rebuild offline (COPR, mock). The licences of the Dart
  packages linked in are in `flutter_assets/NOTICES.Z`.

The Rust code (Ossido, the embedder, the services, the mail engine) is compiled by
`rpmbuild` from vendored crates.

## Layout

```
/usr/lib64/silica/shell/{flutter_assets,libapp.so}
/usr/lib64/silica/apps/<app id>/{flutter_assets,libapp.so}
/usr/libexec/silica/silica-app          the embedder with the system engine
/usr/share/applications/<app id>.desktop
```

Each app's `.desktop` entry comes from its repository (`linux/<app id>.desktop.in`), with
`@EMBEDDER@` → `silica-app` and `@BUNDLE@` → its `flutter_assets`. `libapp.so` is installed
0644: the embedder loads it with `dlopen`, and the RPM strip and debuginfo scripts (which only
touch executable files) must leave the AOT snapshot as `gen_snapshot` wrote it.
