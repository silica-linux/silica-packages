# prepare: flutter .

%global srcrepo preview
%global commit ec0ecb2ab1fe1bb68525b1d2b947f2598137855d
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapdate 20261015
%global appid dev.frascella.Preview

# Nothing is compiled by rpmbuild (the Dart AOT library comes prebuilt, docs/flutter.md):
# no debuginfo.
%global debug_package %{nil}
# The Dart AOT library is private (dlopen'ed by the embedder).
%global __provides_exclude_from ^%{_libdir}/silica/.*$

Name:           preview
Version:        0^%{snapdate}git%{shortcommit}
Release:        1%{?dist}
Summary:        Preview, the image and PDF viewer of Silica

# Preview: MIT OR Apache-2.0; the Dart packages linked in libapp.so are listed in
# flutter_assets/NOTICES.Z.
License:        (MIT OR Apache-2.0) AND LicenseRef-Bundled-Dart
URL:            https://github.com/silica-os/preview
Source0:        %{srcrepo}-%{commit}.tar.gz
Source1:        %{srcrepo}-%{commit}-dart-root.tar.zst

ExclusiveArch:  x86_64
BuildRequires:  zstd
BuildRequires:  desktop-file-utils

Requires:       silica-embedder%{?_isa}
# Shared libraries loaded with FFI (dlopen), invisible to rpm's dependency generator:
# poppler-glib + cairo read and draw PDFs, qpdf-libs rewrites them (silica-os/silica-packages#4).
Requires:       poppler-glib
Requires:       cairo
Requires:       qpdf-libs
Recommends:     silica-icons

%description
Preview opens images and PDF documents: zoom, rotate, slideshow, annotations and PDF page editing,
built on silica_ui. PDFs are read and drawn by poppler-glib and written by qpdf, both loaded at
run time.

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
* Thu Oct 15 2026 Emanuele Frascella <emanuele@frascella.dev> - 0^20261015gitec0ecb2-1
- First package (runtime libraries: poppler-glib, cairo, qpdf-libs)
