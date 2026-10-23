%define _debugsource_template %{nil}
%define debug_package %{nil}

%global app_id ai.storyteller.cadcraft

Name:           cadcraft
Version:        0.12.0
Release:        1%{?dist}
Summary:        Open-source native CAD and drafting application built in Rust

License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/cadcraft
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
CADCraft is an open-source, native computer-aided design and drafting
application written in Rust. It offers a command line, object snaps, layers,
dimensions, hatches and blocks, opens and saves DXF and DWG drawings, and
exports SVG and PNG.

This package also ships cadcraft-cli, a headless companion for inspecting and
converting drawings, running scripts, exporting files and serving an MCP
endpoint.

%prep
%autosetup -n %{name}-%{version}

%build
export CARGO_HOME=$PWD/.cargo-home
export RUSTFLAGS="%{?build_rustflags}"
export CADCRAFT_BUILD_DATE=$(date -u -d "@${SOURCE_DATE_EPOCH:-$(date +%%s)}" +%%F)
cargo build --release --locked -p cadcraft -p cadcraft-cli

%install
install -Dpm 0755 target/release/cadcraft %{buildroot}%{_bindir}/cadcraft
install -Dpm 0755 target/release/cadcraft-cli %{buildroot}%{_bindir}/cadcraft-cli
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
%{_bindir}/cadcraft
%{_bindir}/cadcraft-cli
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/mime/packages/%{app_id}.xml
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/%{app_id}.*

%changelog
%autochangelog
