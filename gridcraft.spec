%define _debugsource_template %{nil}
%define debug_package %{nil}

%global app_id ai.storyteller.gridcraft

Name:           gridcraft
Version:        0.14.2
Release:        1%{?dist}
Summary:        Open-source native spreadsheet application built in Rust

License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/gridcraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  cargo
BuildRequires:  rust >= 1.90
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  desktop-file-utils
BuildRequires:  appstream

Requires:       hicolor-icon-theme
Requires:       libxkbcommon
Requires:       libxkbcommon-x11
Requires:       (vulkan-loader or libglvnd-egl)

Recommends:     libwayland-client
Recommends:     libX11
Recommends:     libXcursor
Recommends:     libXi
Recommends:     libXrandr
Recommends:     mesa-vulkan-drivers
Recommends:     xdg-desktop-portal

%description
GridCraft is an open-source, native spreadsheet application written in Rust.
It provides workbooks with formulas, charts, data analysis and rich
formatting, and opens and saves XLSX, XLSB, ODS and CSV files.

This package also ships gridcraft-cli, a headless companion for evaluating
formulas, generating and inspecting workbooks, running scripts and serving an
MCP endpoint.

%prep
%autosetup -n %{name}-%{version}

%build
export CARGO_HOME=$PWD/.cargo-home
export RUSTFLAGS="%{?build_rustflags}"
cargo build --release --locked -p gridcraft -p gridcraft-cli

%install
install -Dpm 0755 target/release/gridcraft %{buildroot}%{_bindir}/gridcraft
install -Dpm 0755 target/release/gridcraft-cli %{buildroot}%{_bindir}/gridcraft-cli
install -Dpm 0644 packaging/linux/%{app_id}.desktop %{buildroot}%{_datadir}/applications/%{app_id}.desktop
install -Dpm 0644 packaging/linux/%{app_id}.mime.xml %{buildroot}%{_datadir}/mime/packages/%{app_id}.xml
install -d %{buildroot}%{_metainfodir}
sed -e 's/@VERSION@/%{version}/g' \
    -e "s/@DATE@/$(date -u -d "@${SOURCE_DATE_EPOCH:-$(date +%%s)}" +%%F)/g" \
    packaging/linux/%{app_id}.metainfo.xml.in \
    > %{buildroot}%{_metainfodir}/%{app_id}.metainfo.xml
install -d %{buildroot}%{_datadir}/icons
cp -a assets/app-icon/hicolor %{buildroot}%{_datadir}/icons/

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{app_id}.desktop
appstreamcli validate --no-net %{buildroot}%{_metainfodir}/%{app_id}.metainfo.xml

%files
%license LICENSE-APACHE LICENSE-MIT
%doc README.md
%{_bindir}/gridcraft
%{_bindir}/gridcraft-cli
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/mime/packages/%{app_id}.xml
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/%{app_id}.*

%changelog
%autochangelog
