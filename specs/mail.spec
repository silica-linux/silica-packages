# prepare: rust engine
# prepare: flutter app

%global srcrepo mail
%global commit a4e71f10320ef3c49c03c1e212ddd5484ff11de7
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapdate 20261014
%global appid dev.frascella.Mail

# The Dart AOT library is private (dlopen'ed by the embedder).
%global __provides_exclude_from ^%{_libdir}/silica/.*$

Name:           mail
Version:        0^%{snapdate}git%{shortcommit}
Release:        1%{?dist}
Summary:        Mail, the email client of Silica

# Mail: MIT OR Apache-2.0. The engine's bundled Rust crates are listed in cargo-vendor.txt
# (licences in LICENSE.dependencies); the Dart packages of the app in
# flutter_assets/NOTICES.Z.
License:        (MIT OR Apache-2.0) AND LicenseRef-Bundled-Crates AND LicenseRef-Bundled-Dart
URL:            https://github.com/silica-linux/mail
Source0:        %{srcrepo}-%{commit}.tar.gz
Source1:        %{srcrepo}-%{commit}-vendor-engine.tar.zst
Source2:        %{srcrepo}-%{commit}-dart-app.tar.zst
Source3:        dev.frascella.Mail.service

ExclusiveArch:  x86_64
BuildRequires:  cargo-rpm-macros >= 26
BuildRequires:  rust
BuildRequires:  cargo
BuildRequires:  gcc
BuildRequires:  zstd
BuildRequires:  desktop-file-utils

Requires:       silica-embedder%{?_isa}
Requires:       silica-mail-engine%{?_isa} = %{version}-%{release}
Recommends:     silica-icons

%description
Mail is Silica's email client: mailboxes, threads, search and the composer, on top of
silica-mail-engine.

%package -n silica-mail-engine
Summary:        IMAP and SMTP engine of Silica's Mail, on D-Bus

%description -n silica-mail-engine
silica-mail-engine syncs IMAP accounts, sends through SMTP and keeps an offline store; it
serves dev.frascella.Mail on the session bus (started on demand by D-Bus activation).

%prep
%autosetup -n %{srcrepo}-%{commit}
cd engine
zstd -dc %{SOURCE1} | tar -x
%cargo_prep -v vendor
cd ..
mkdir bundle
zstd -dc %{SOURCE2} | tar -x -C bundle

%build
cd engine
%cargo_build
%{cargo_license_summary -a}
%{cargo_license -a} > LICENSE.dependencies
%cargo_vendor_manifest

%install
install -Dpm 0755 engine/target/rpm/silica-mail-engine \
  %{buildroot}%{_libexecdir}/silica/silica-mail-engine
sed 's|@LIBEXECDIR@|%{_libexecdir}|' %{SOURCE3} > dev.frascella.Mail.service
install -Dpm 0644 dev.frascella.Mail.service \
  %{buildroot}%{_datadir}/dbus-1/services/dev.frascella.Mail.service

install -dm 0755 %{buildroot}%{_libdir}/silica/apps/%{appid}
cp -a bundle/flutter_assets %{buildroot}%{_libdir}/silica/apps/%{appid}/
# 0644: dlopen'ed, kept away from the strip and debuginfo scripts (executables only).
install -pm 0644 bundle/libapp.so %{buildroot}%{_libdir}/silica/apps/%{appid}/libapp.so
sed -e 's|@EMBEDDER@|%{_libexecdir}/silica/silica-app|' \
    -e 's|@BUNDLE@|%{_libdir}/silica/apps/%{appid}/flutter_assets|' \
    app/linux/%{appid}.desktop.in > %{appid}.desktop
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

%files -n silica-mail-engine
%license LICENSE-MIT LICENSE-APACHE engine/LICENSE.dependencies engine/cargo-vendor.txt
%dir %{_libexecdir}/silica
%{_libexecdir}/silica/silica-mail-engine
%{_datadir}/dbus-1/services/dev.frascella.Mail.service

%changelog
* Wed Oct 14 2026 Emanuele Frascella <emanuele@frascella.dev> - 0^20261014gita4e71f1-1
- First package
