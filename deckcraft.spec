%define _debugsource_template %{nil}
%define debug_package %{nil}

%global app_id ai.storyteller.deckcraft

Name:           deckcraft
Version:        0.10.0
Release:        1%{?dist}
Summary:        Open-source native presentation and slide designer built in Rust

License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/deckcraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  cargo
BuildRequires:  rust >= 1.95
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  pkgconfig(alsa)
BuildRequires:  desktop-file-utils
BuildRequires:  appstream

Requires:       hicolor-icon-theme
Requires:       libxkbcommon
Requires:       libxkbcommon-x11
Requires:       alsa-lib
Requires:       (vulkan-loader or libglvnd-egl)

Recommends:     libwayland-client
Recommends:     libX11
Recommends:     libXcursor
Recommends:     libXi
Recommends:     libXrandr
Recommends:     mesa-vulkan-drivers
Recommends:     xdg-desktop-portal

%description
DeckCraft is an open-source, native presentation and slide designer written in
Rust. It builds decks with themes, layouts, shapes, pictures, tables, charts,
transitions and animations, opens and saves PowerPoint (.pptx) files, and
presents them full screen with a presenter view.

This package also ships deckcraft-cli, a headless companion for rendering and
converting decks, running command scripts, inspecting files and serving an MCP
endpoint.

%prep
%autosetup -n %{name}-%{version}

%build
export CARGO_HOME=$PWD/.cargo-home
export RUSTFLAGS="%{?build_rustflags}"
cargo build --release --locked -p deckcraft -p deckcraft-cli

%install
install -Dpm 0755 target/release/deckcraft %{buildroot}%{_bindir}/deckcraft
install -Dpm 0755 target/release/deckcraft-cli %{buildroot}%{_bindir}/deckcraft-cli
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
%{_bindir}/deckcraft
%{_bindir}/deckcraft-cli
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/mime/packages/%{app_id}.xml
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/%{app_id}.*

%changelog
* Fri Oct 23 2026 Storytold Artcraft Packaging <packaging@storytold.ai> - 0.10.0-1
- Initial package
