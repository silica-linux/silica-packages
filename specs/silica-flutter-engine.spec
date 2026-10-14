# The Flutter engine in release mode for Silica's embedder. Google publishes the embedder
# engine only in debug mode, so silica-desktop builds the release one from source at the
# revision of the Flutter SDK it uses (`cargo xtask engine --release`, about 15 minutes and
# 10 GB of checkout: too heavy for every CI run). The library built that way is published
# once per Flutter version as a release asset of silica-packages (tools/engine-tarball.sh),
# and this spec packages it. See docs/engine.md.
# prepare: engine

%global flutter_version 3.47.7
%global engine_rev deb287481e3ce9468f3434937ced4240a70539ca

# A prebuilt, stripped library: no debuginfo to extract.
%global debug_package %{nil}

Name:           silica-flutter-engine
Version:        %{flutter_version}
Release:        1%{?dist}
Summary:        Flutter engine (release mode) for the Silica embedder

# Flutter: BSD-3-Clause. NOTICES (the sky_engine LICENSE of the same SDK) carries the full
# texts of the third-party components linked in the engine (Skia, Impeller, ICU, the Dart
# VM, BoringSSL, HarfBuzz, FreeType, zlib, …); an SPDX breakdown of that file is still to do.
License:        BSD-3-Clause AND LicenseRef-Flutter-Engine-NOTICES
URL:            https://github.com/flutter/flutter
Source0:        silica-flutter-engine-%{engine_rev}-x86_64.tar.zst

ExclusiveArch:  x86_64
BuildRequires:  zstd

# The engine is loaded by silica-embedder with dlopen: no soname, private directory.
%global __provides_exclude_from ^%{_libdir}/silica/engine/.*$

%description
The Flutter engine library (libflutter_engine.so, release mode, AOT) and its ICU data,
used by Silica's Flutter embedder to run the shell and the apps. Built from source at
engine revision %{engine_rev} (Flutter %{flutter_version}).

%prep
%setup -q -c -T
zstd -dc %{SOURCE0} | tar -x --strip-components=1

%build
# Prebuilt: see the header of this spec.

%install
install -Dpm 0755 libflutter_engine.so %{buildroot}%{_libdir}/silica/engine/libflutter_engine.so
install -Dpm 0644 icudtl.dat %{buildroot}%{_libdir}/silica/engine/icudtl.dat
install -Dpm 0644 ENGINE_VERSION %{buildroot}%{_libdir}/silica/engine/ENGINE_VERSION

%files
%license LICENSE NOTICES
%dir %{_libdir}/silica
%{_libdir}/silica/engine/

%changelog
* Wed Oct 14 2026 Emanuele Frascella <emanuele@frascella.dev> - 3.47.7-1
- First package: engine deb28748 built from source for Flutter 3.47.7
