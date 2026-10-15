# prepare: rust .
# prepare: flutter shell

%global srcrepo silica-desktop
%global commit 0ede8e3a7fa5cc22912987db041eafe5821efd38
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapdate 20261015

# The shell's Dart AOT library is private (dlopen'ed by the embedder).
%global __provides_exclude_from ^%{_libdir}/silica/.*$

Name:           silica-desktop
Version:        0^%{snapdate}git%{shortcommit}
Release:        1%{?dist}
Summary:        The Silica desktop: the Ossido compositor, the shell and its services

# Silica's code: MIT OR Apache-2.0. The bundled Rust crates are listed in cargo-vendor.txt
# and their licences summarised in LICENSE.dependencies; the Dart packages linked in the
# shell's AOT library are listed in its flutter_assets/NOTICES.Z.
License:        (MIT OR Apache-2.0) AND LicenseRef-Bundled-Crates AND LicenseRef-Bundled-Dart
URL:            https://github.com/silica-os/silica-desktop
Source0:        %{srcrepo}-%{commit}.tar.gz
Source1:        %{srcrepo}-%{commit}-vendor-root.tar.zst
Source2:        %{srcrepo}-%{commit}-dart-shell.tar.zst
Source3:        silica-session
Source4:        silica.desktop
Source5:        silica-app
Source6:        dev.frascella.Silica.service

# The Flutter engine and the AOT bundles exist only for x86_64 today.
ExclusiveArch:  x86_64

BuildRequires:  cargo-rpm-macros >= 26
BuildRequires:  rust >= 1.88
BuildRequires:  cargo
BuildRequires:  gcc
BuildRequires:  zstd
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-server)
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  pkgconfig(libudev)
BuildRequires:  pkgconfig(libinput)
BuildRequires:  pkgconfig(libseat)
BuildRequires:  pkgconfig(gbm)
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(egl)
BuildRequires:  pkgconfig(glesv2)
BuildRequires:  pkgconfig(dbus-1)

Requires:       silica-session = %{version}-%{release}

%description
Silica is a desktop for Linux built around the Ossido Wayland compositor and a shell
written in Flutter. This metapackage installs the whole session: the compositor, the
shell, the system services, the portal and the login entry.

%package -n ossido
Summary:        Ossido, the Wayland compositor of Silica

%description -n ossido
Ossido is Silica's Wayland compositor (Smithay): glass materials, window decorations,
spaces and Panorama, with a DRM/KMS backend for real sessions and a nested one for
development.

%package -n silica-embedder
Summary:        Flutter embedder for Silica's shell and apps
Requires:       silica-flutter-engine%{?_isa}

%description -n silica-embedder
The Flutter embedder that runs Silica's shell components and apps as Wayland clients,
with the platform channels of Silica (glass, windows, D-Bus, drag and drop, pty).
silica-app starts it with the system's release engine.

%package -n silica-daemon
Summary:        Silica's session services on D-Bus (notifications, system state)
# pw-play, for the interface sounds.
Requires:       pipewire-utils

%description -n silica-daemon
silica-daemon owns org.freedesktop.Notifications and dev.frascella.Silica on the session
bus: notifications and the system state shown by the Control Center, and the interface
sounds (played with pw-play).

%package -n silica-portal
Summary:        xdg-desktop-portal backend for Silica
Requires:       xdg-desktop-portal
Recommends:     xdg-desktop-portal-gtk
Recommends:     mustache

%description -n silica-portal
The FileChooser and Settings portal backend of Silica: open and save dialogs are
Mustache's, the appearance comes from silica-daemon.

%package -n silica-cli
Summary:        Command line client for Ossido's control channel

%description -n silica-cli
silica-cli talks to a running Ossido through its control channel (commands, screenshots,
synthetic input) and serves it over MCP. silica-action, from the same crate, runs the
shell's actions (the Apps and Screenshot entries call it).

%package -n silica-shell
Summary:        The Silica shell: menu bar, Dock, Faro, Control Center, notifications
Requires:       silica-embedder = %{version}-%{release}
Recommends:     silica-icons

%description -n silica-shell
The Flutter shell of Silica, compiled ahead of time: wallpaper, menu bar, Dock, Faro,
app switcher, notifications and Control Center, each run as a layer by the embedder.

%package -n silica-session
Summary:        The Silica Wayland session entry
Requires:       ossido = %{version}-%{release}
Requires:       silica-shell = %{version}-%{release}
Requires:       silica-daemon = %{version}-%{release}
Requires:       silica-portal = %{version}-%{release}
Requires:       dbus-tools
Requires:       adwaita-cursor-theme
Recommends:     rsms-inter-fonts
Recommends:     silica-icons
Recommends:     mustache

%description -n silica-session
The Silica entry for login managers (wayland-sessions) and the silica-session launcher
that starts Ossido with the shell.

%prep
%autosetup -n %{srcrepo}-%{commit} -p1
zstd -dc %{SOURCE1} | tar -x
%cargo_prep -v vendor
mkdir -p shell-bundle
zstd -dc %{SOURCE2} | tar -x -C shell-bundle

%build
%cargo_build -- -p ossido -p silica-embedder -p silica-daemon -p silica-portal -p silica-cli
%{cargo_license_summary -a}
%{cargo_license -a} > LICENSE.dependencies
%cargo_vendor_manifest

%install
for bin in ossido silica-cli silica-action; do
  install -Dpm 0755 target/rpm/$bin %{buildroot}%{_bindir}/$bin
done
for bin in silica-embedder silica-daemon silica-portal; do
  install -Dpm 0755 target/rpm/$bin %{buildroot}%{_libexecdir}/silica/$bin
done

subst() {
  sed -e 's|@LIBEXECDIR@|%{_libexecdir}|g' -e 's|@LIBDIR@|%{_libdir}|g' "$1"
}
subst %{SOURCE5} > silica-app
install -Dpm 0755 silica-app %{buildroot}%{_libexecdir}/silica/silica-app
subst %{SOURCE3} > silica-session
install -Dpm 0755 silica-session %{buildroot}%{_bindir}/silica-session
install -Dpm 0644 %{SOURCE4} %{buildroot}%{_datadir}/wayland-sessions/silica.desktop
# Brings graphical-session.target up, which xdg-desktop-portal requires.
install -Dpm 0644 data/systemd/silica-session.target \
  %{buildroot}%{_userunitdir}/silica-session.target
subst %{SOURCE6} > dev.frascella.Silica.service
install -Dpm 0644 dev.frascella.Silica.service \
  %{buildroot}%{_datadir}/dbus-1/services/dev.frascella.Silica.service

# The shell's own applications (Apps, Screenshot): the templates with their @ACTION@
# replaced by silica-action, as xtask's shell_entries does.
for template in shell/linux/*.desktop.in; do
  entry=$(basename "$template" .in)
  sed 's|@ACTION@|%{_bindir}/silica-action|g' "$template" \
    > "$entry"
  install -Dpm 0644 "$entry" %{buildroot}%{_datadir}/applications/"$entry"
done

# The portal: the backend, the .portal file and the configuration that picks it when
# XDG_CURRENT_DESKTOP=Silica.
install -Dpm 0644 crates/portal/data/silica.portal \
  %{buildroot}%{_datadir}/xdg-desktop-portal/portals/silica.portal
install -Dpm 0644 crates/portal/data/silica-portals.conf \
  %{buildroot}%{_datadir}/xdg-desktop-portal/silica-portals.conf
sed 's|@PORTAL@|%{_libexecdir}/silica/silica-portal|' \
  crates/portal/data/org.freedesktop.impl.portal.desktop.silica.service.in \
  > org.freedesktop.impl.portal.desktop.silica.service
install -Dpm 0644 org.freedesktop.impl.portal.desktop.silica.service \
  %{buildroot}%{_datadir}/dbus-1/services/org.freedesktop.impl.portal.desktop.silica.service

# The interface sounds, played by silica-daemon from $XDG_DATA_DIRS/silica/sounds.
install -dm 0755 %{buildroot}%{_datadir}/silica/sounds
install -pm 0644 data/sounds/*.wav %{buildroot}%{_datadir}/silica/sounds/

# The shell: flutter_assets with libapp.so next to it, as the embedder expects.
install -dm 0755 %{buildroot}%{_libdir}/silica/shell
cp -a shell-bundle/flutter_assets %{buildroot}%{_libdir}/silica/shell/
# 0644: dlopen'ed, and outside the reach of the strip and debuginfo scripts (which only
# touch executable files): the AOT snapshot must stay as gen_snapshot wrote it.
install -pm 0644 shell-bundle/libapp.so %{buildroot}%{_libdir}/silica/shell/libapp.so

%check
# A session entry, not an application: desktop-file-validate rejects DesktopNames there.
grep -q '^Exec=/usr/bin/silica-session$' %{buildroot}%{_datadir}/wayland-sessions/silica.desktop
sh -n %{buildroot}%{_bindir}/silica-session
# Not desktop-file-validate: OnlyShowIn=Silica is not a registered desktop.
for entry in dev.frascella.Apps dev.frascella.MissionControl dev.frascella.Screenshot; do
  grep -q '^Exec=%{_bindir}/silica-action ' %{buildroot}%{_datadir}/applications/$entry.desktop
done
! grep -rq '@ACTION@' %{buildroot}%{_datadir}/applications
sh -n %{buildroot}%{_libexecdir}/silica/silica-app

%files
%license LICENSE-MIT LICENSE-APACHE LICENSE.dependencies cargo-vendor.txt
%doc README.md

%files -n ossido
%license LICENSE-MIT LICENSE-APACHE
%{_bindir}/ossido

%files -n silica-embedder
%license LICENSE-MIT LICENSE-APACHE
%dir %{_libexecdir}/silica
%{_libexecdir}/silica/silica-embedder
%{_libexecdir}/silica/silica-app

%files -n silica-daemon
%license LICENSE-MIT LICENSE-APACHE
%dir %{_libexecdir}/silica
%{_libexecdir}/silica/silica-daemon
%dir %{_datadir}/silica
%{_datadir}/silica/sounds/
%{_datadir}/dbus-1/services/dev.frascella.Silica.service

%files -n silica-portal
%license LICENSE-MIT LICENSE-APACHE
%dir %{_libexecdir}/silica
%{_libexecdir}/silica/silica-portal
%{_datadir}/xdg-desktop-portal/portals/silica.portal
%{_datadir}/xdg-desktop-portal/silica-portals.conf
%{_datadir}/dbus-1/services/org.freedesktop.impl.portal.desktop.silica.service

%files -n silica-cli
%license LICENSE-MIT LICENSE-APACHE
%{_bindir}/silica-cli
%{_bindir}/silica-action
%{_datadir}/applications/dev.frascella.Apps.desktop
%{_datadir}/applications/dev.frascella.MissionControl.desktop
%{_datadir}/applications/dev.frascella.Screenshot.desktop

%files -n silica-shell
%license LICENSE-MIT LICENSE-APACHE
%dir %{_libdir}/silica
%{_libdir}/silica/shell/

%files -n silica-session
%license LICENSE-MIT LICENSE-APACHE
%{_bindir}/silica-session
%{_datadir}/wayland-sessions/silica.desktop
%{_userunitdir}/silica-session.target

%changelog
* Thu Oct 15 2026 Emanuele Frascella <emanuele@frascella.dev> - 0^20261015git0ede8e3-1
- Update to the current main (release 0.1.2); install the Mission Control entry

* Wed Oct 14 2026 Emanuele Frascella <emanuele@frascella.dev> - 0^20261014git0823efa-1
- First package
