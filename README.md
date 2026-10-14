<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/silica-logo-dark.svg">
    <img alt="Silica" src=".github/silica-logo-light.svg" width="200">
  </picture>
</p>

<h1 align="center">silica-packages</h1>

<p align="center">
  <b>Silica packages for Fedora.</b><br>
  The desktop, the apps, Inter and silica-icons as RPMs, with a Wayland session you can pick at login.
</p>

<p align="center">
  <img alt="Fedora: RPM" src="https://img.shields.io/badge/Fedora-RPM-51A2DA?style=flat-square&logo=fedora">
  <img alt="status: alpha" src="https://img.shields.io/badge/status-alpha-d9822b?style=flat-square">
</p>

The first step towards the distribution: Silica installable on any Fedora, without
reinstalling. The same packages feed the image of [`silica-os`](https://github.com/silica-linux/silica-os).

Target: **Fedora 45, x86_64** (the Flutter engine and the Dart AOT bundles exist only for
x86_64 today).

## Packages

| Package | From | Contents |
|---|---|---|
| `silica-desktop` | silica-desktop | metapackage: the whole session |
| `ossido` | silica-desktop | the compositor, `/usr/bin/ossido` |
| `silica-embedder` | silica-desktop | the Flutter embedder and `silica-app` (embedder + system engine) in `/usr/libexec/silica` |
| `silica-daemon` | silica-desktop | notifications and system state on the session bus |
| `silica-portal` | silica-desktop | xdg-desktop-portal backend (FileChooser, Settings) |
| `silica-cli` | silica-desktop | client of Ossido's control channel, MCP server |
| `silica-shell` | silica-desktop | the shell, AOT-compiled, in `/usr/lib64/silica/shell` |
| `silica-session` | silica-desktop | `silica-session` and the `wayland-sessions` entry |
| `silica-flutter-engine` | Flutter (prebuilt, see [docs/engine.md](docs/engine.md)) | `libflutter_engine.so` in release mode, `/usr/lib64/silica/engine` |
| `silica-icons` | silica-icons | `/usr/share/silica/icons` |
| `mustache`, `clock`, `calculator`, `terminal` | the app repositories | `/usr/lib64/silica/apps/<app id>` and the `.desktop` entry |
| `mail`, `silica-mail-engine` | mail | the app, and the IMAP/SMTP engine started by D-Bus activation |

Inter comes from Fedora (`rsms-inter-fonts`, recommended by `silica-session`); `silica_ui`
also bundles the two weights it uses in every app.

### Dependencies

```
silica-desktop ─▶ silica-session ─┬▶ ossido
                                  ├▶ silica-shell ─▶ silica-embedder ─▶ silica-flutter-engine
                                  ├▶ silica-daemon
                                  └▶ silica-portal ─▶ xdg-desktop-portal
                                     (recommends: mustache, silica-icons, rsms-inter-fonts)
mustache, clock, calculator, terminal, mail ─▶ silica-embedder
mail ─▶ silica-mail-engine
```

## Building

```bash
tools/build.sh silica-desktop mustache   # or: tools/build.sh all
ls out/fc45/                                    # RPMs and SRPMs
```

`tools/build.sh` runs everything in a Fedora container (podman, or docker): it fetches each
source repository at the commit or tag written in its spec (`%global commit`), vendors the
Rust crates (`cargo vendor`, so `rpmbuild` runs offline), builds the Dart AOT bundles with the
pinned Flutter SDK ([docs/flutter.md](docs/flutter.md)), then runs `rpmbuild -ba`. The source
RPMs are self-contained.

- `GH_TOKEN` (optional): the sources are public; a token only raises GitHub's rate limits.
- `CACHE` (default `.cache/`): the Flutter SDK, the pub and cargo caches and the engine
  tarball, shared between builds.
- `ENGINE`: a local engine tarball (`tools/engine-tarball.sh`) instead of the release asset.
- `FEDORA` (default 45), `CONTAINER`, `IMAGE`.

To package a new version of a component, update `%global commit` (and `snapdate`) in its
spec, the `Version` if the source has a new tag, and add a `%changelog` entry.

## Installing

Every tag of this repository builds all the packages in CI and attaches to its GitHub
release the RPMs, a dnf repository (`silica-repo-<tag>-fc45.tar.zst`) and `silica.repo`.

```bash
sudo mkdir -p /var/lib/silica-repo
sudo tar -C /var/lib/silica-repo --strip-components=1 -xf silica-repo-<tag>-fc45.tar.zst
sudo cp silica.repo /etc/yum.repos.d/
sudo dnf install silica-desktop mustache silica-icons
```

Then choose **Silica** in the login manager. `/etc/silica/session.env` and
`/etc/silica/session.env.d/*.env` configure the session (`SILICA_RENDERER`, `SILICA_BACKEND`,
`OSSIDO_ARGS`; see `silica-session`). The session (`silica-session`) runs Ossido on
DRM/KMS; started inside another Wayland or X11 session it opens nested in a window.

Publishing on COPR (`dnf copr enable`) is wired in CI and waits for the `COPR_TOKEN` secret
(the content of `~/.config/copr`) and the `COPR_PROJECT` variable (`owner/name`).

## CI

`.github/workflows/build.yml`: one job per package in a `fedora:45` container, the RPMs as
artifacts, then the dnf repository; on `v*` tags the GitHub release and, when configured,
the COPR builds, and a `packages-release` dispatch to silica-os (secret
`SILICA_OS_DISPATCH_TOKEN`, a token allowed to create dispatch events there; skipped when
absent).
