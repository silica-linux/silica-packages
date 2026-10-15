%global srcrepo silica-icons
%global commit v0.6.1

Name:           silica-icons
Version:        0.6.1
Release:        1%{?dist}
Summary:        Silica's icons: apps, files and folders, system symbols

# Icons: CC-BY-SA-4.0. apps/silica/ is the Silica logo, a trademark of the project, not
# covered by CC BY-SA (README of silica-icons; silica-brand TRADEMARKS.md). Derived
# distributions must remove it.
License:        CC-BY-SA-4.0 AND LicenseRef-Silica-Trademark
URL:            https://github.com/silica-os/silica-icons
Source0:        %{srcrepo}-%{commit}.tar.gz

BuildArch:      noarch

%description
The icons of Silica in their layered format, read by the shell and the apps (silica_ui)
from %{_datadir}/silica/icons: app icons (reserved for Silica's own apps), folders, file
types, volumes and Trash, badges, and the system symbols in three weights.

%prep
%autosetup -n %{srcrepo}-%{commit}

%build
# Nothing to build: the icons are used as they are.

%install
install -dm 0755 %{buildroot}%{_datadir}/silica/icons
cp -a apps badges files symbols %{buildroot}%{_datadir}/silica/icons/
# The previews are for the repository's README only.
find %{buildroot}%{_datadir}/silica/icons -name preview.png -delete

%files
%license LICENSE
%doc README.md ASSETS.md
%dir %{_datadir}/silica
%{_datadir}/silica/icons/

%changelog
* Wed Oct 14 2026 Emanuele Frascella <emanuele@frascella.dev> - 0.4.2-1
- Update to 0.4.2

* Wed Oct 14 2026 Emanuele Frascella <emanuele@frascella.dev> - 0.3.0-1
- First package
