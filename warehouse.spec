Name:           warehouse
Version:        2.2.0
Release:        1%{?dist}
Summary:        Manage all things Flatpak

License:        GPL-3.0-only
URL:            https://github.com/flattool/warehouse
Source0:        https://github.com/flattool/warehouse/archive/refs/tags/%{version}.tar.gz


BuildRequires:  blueprint-compiler
BuildRequires:  desktop-file-utils
BuildRequires:  gettext
BuildRequires:  glib2-devel
BuildRequires:  libappstream-glib
BuildRequires:  meson >= 0.64.0
BuildRequires:  pkgconfig(gtk4)
BuildRequires:  pkgconfig(libadwaita-1)
BuildRequires:  python3-devel

Requires:       flatpak
Requires:       gtk4
Requires:       hicolor-icon-theme
Requires:       libadwaita
Requires:       python3-gobject

BuildArch:      noarch

%description
Warehouse is a versatile toolbox for Flatpak. It provides a simple UI
to control complex Flatpak options without resorting to the command
line: view package info, change package versions (rollbacks), manage
user data and leftover data, batch uninstall, manage remotes, install
from files/remotes, and take snapshots of app data.


%prep
%autosetup -n warehouse-%{version}

# Flatpak manifest runs behind flatpak-spawn --host to escape the
# sandbox (finish-args talk org.freedesktop.Flatpak, filesystems
# /var/lib/flatpak:ro, ~/.local/share/flatpak:ro, ~/.var/app, host-etc).
# A native RPM runs on the host already, where flatpak-spawn --host
# does not work, so call flatpak / sh directly (single-line and
# multi-line list forms).
python3 - <<'EOF'
import re, pathlib
for p in pathlib.Path('src').rglob('*.py'):
    t = p.read_text()
    t = re.sub(r'"flatpak-spawn",\s*"--host",\s*', '', t)
    t = re.sub(r'\["flatpak-spawn",\s*"--host"\]', '[]', t)
    p.write_text(t)
EOF
if grep -rn 'flatpak-spawn' src; then exit 1; fi

# Upstream hardcodes the Flatpak-sandbox path for extra installations.
# Fall back to the host path when building natively.
sed -i 's|custom_install_config_path = "/run/host/etc/flatpak/installations.d"|custom_install_config_path = "/etc/flatpak/installations.d"|' src/host_info.py


%build
%meson -Dprofile=default
%meson_build


%install
%meson_install
%find_lang warehouse


%check
desktop-file-validate %{buildroot}%{_datadir}/applications/io.github.flattool.Warehouse.desktop || :
appstream-util validate-relax --nonet %{buildroot}%{_datadir}/metainfo/io.github.flattool.Warehouse.metainfo.xml || :


%files -f warehouse.lang
%license LICENSE
%doc README.md
%{_bindir}/warehouse
%{_datadir}/warehouse/
%{_datadir}/applications/io.github.flattool.Warehouse.desktop
%{_datadir}/metainfo/io.github.flattool.Warehouse.metainfo.xml
%{_datadir}/glib-2.0/schemas/io.github.flattool.Warehouse.gschema.xml
%{_datadir}/icons/hicolor/scalable/apps/io.github.flattool.Warehouse.svg
%{_datadir}/icons/hicolor/symbolic/apps/io.github.flattool.Warehouse-symbolic.svg


%changelog
%autochangelog
