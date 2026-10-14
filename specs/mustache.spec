# prepare: flutter .

%global srcrepo mustache
%global commit a10918b4ba5b42b17daa7149c023ff811025ac3d
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapdate 20261014
%global appid dev.frascella.Mustache

# Nothing is compiled by rpmbuild (the Dart AOT library comes prebuilt, docs/flutter.md):
# no debuginfo.
%global debug_package %{nil}
# The Dart AOT library is private (dlopen'ed by the embedder).
%global __provides_exclude_from ^%{_libdir}/silica/.*$

Name:           mustache
Version:        0.1.0^%{snapdate}git%{shortcommit}
Release:        1%{?dist}
Summary:        Mustache, the file manager of Silica

# Mustache: MIT OR Apache-2.0; the Dart packages linked in libapp.so are listed in
# flutter_assets/NOTICES.Z.
License:        (MIT OR Apache-2.0) AND LicenseRef-Bundled-Dart
URL:            https://github.com/silica-linux/mustache
Source0:        %{srcrepo}-%{commit}.tar.gz
Source1:        %{srcrepo}-%{commit}-dart-root.tar.zst

ExclusiveArch:  x86_64
BuildRequires:  zstd
BuildRequires:  desktop-file-utils

Requires:       silica-embedder%{?_isa}
Recommends:     silica-icons

%description
Mustache is Silica's file manager: icon, list, column and gallery views, tags, Quick Look,
tabs, and the open and save dialogs of the Silica portal.

%prep
%autosetup -n %{srcrepo}-%{commit}
mkdir bundle
zstd -dc %{SOURCE1} | tar -x -C bundle

%build
# Built ahead of time by tools/container.sh (Dart AOT, see docs/flutter.md).

%install
install -dm 0755 %{buildroot}%{_libdir}/silica/apps/%{appid}
cp -a bundle/flutter_assets %{buildroot}%{_libdir}/silica/apps/%{appid}/
install -pm 0644 bundle/libapp.so %{buildroot}%{_libdir}/silica/apps/%{appid}/libapp.so
sed -e 's|@EMBEDDER@|%{_libexecdir}/silica/silica-app|' \
    -e 's|@BUNDLE@|%{_libdir}/silica/apps/%{appid}/flutter_assets|' \
    linux/%{appid}.desktop.in > %{appid}.desktop
install -Dpm 0644 %{appid}.desktop %{buildroot}%{_datadir}/applications/%{appid}.desktop

%check
# OnlyShowIn=Silica is not a registered desktop name for desktop-file-validate (it wants
# X- values); the rest of the entry is validated.
sed '/^OnlyShowIn=/d' %{buildroot}%{_datadir}/applications/%{appid}.desktop > check.desktop
desktop-file-validate check.desktop

%files
%license LICENSE-MIT LICENSE-APACHE
%doc README.md
%dir %{_libdir}/silica
%dir %{_libdir}/silica/apps
%{_libdir}/silica/apps/%{appid}/
%{_datadir}/applications/%{appid}.desktop

%changelog
* Wed Oct 14 2026 Emanuele Frascella <emanuele@frascella.dev> - 0.1.0^20261014git2be5c3d-1
- First package
