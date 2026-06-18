%global debug_package %{nil}

Name: vpngate-gtk
Version: 0.0.1.6
Release: 1
Summary: VPN Gate GTK4 Client
License: GPL-3.0-or-later
URL: https://github.com/apicalshark/vpngate-gtk
Source0: https://github.com/apicalshark/vpngate-gtk/archive/refs/tags/v%{version}.tar.gz
Source1: vpngate-gtk.sh
Source3: vpngate-gtk.desktop

BuildRequires: python3
BuildRequires: python3-devel
BuildRequires: python3-requests
BuildRequires: libadwaita-devel
BuildRequires: python3-gobject

Requires: python3
Requires: python3-requests
Requires: python3-gobject
Requires: python3-trayer
Requires: libadwaita
Requires: NetworkManager-openvpn
Requires: openvpn

%description
VPN Gate GTK4 Client – A simple GTK4/libadwaita application to browse
and connect to free VPN Gate servers. Supports both the official VPN Gate
API and the api.ovpn.pw fallback source.

%prep
%setup -n vpngate-gtk-%{version}

%build
%{__python3} -m compileall .

%install
mkdir -p %{buildroot}%{_datadir}/vpngate-gtk
cp -r . %{buildroot}%{_datadir}/vpngate-gtk/

mkdir -p %{buildroot}%{_bindir}
cp %{SOURCE1} %{buildroot}%{_bindir}/vpngate-gtk
chmod 755 %{buildroot}%{_bindir}/vpngate-gtk

mkdir -p %{buildroot}%{_datadir}/applications
cp %{SOURCE3} %{buildroot}%{_datadir}/applications/vpngate-gtk.desktop

for size in 256x256 64x64 32x32; do
  mkdir -p %{buildroot}%{_datadir}/icons/hicolor/$size/apps
  cp hicolor/$size/apps/vpngate-gtk.png %{buildroot}%{_datadir}/icons/hicolor/$size/apps/
done

%files
%{_datadir}/vpngate-gtk/
%{_bindir}/vpngate-gtk
%{_datadir}/applications/vpngate-gtk.desktop
%{_datadir}/icons/hicolor/*/apps/vpngate-gtk.png

%changelog
%autochangelog
