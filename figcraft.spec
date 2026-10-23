%define _debugsource_template %{nil}
%define debug_package %{nil}

%global app_id ai.storyteller.figcraft
%global craft_fonts_commit 43913056ce82a3fdad0ef69f6b88d1dc922a8104
%global craft_fonts_short %(c=%{craft_fonts_commit}; echo ${c:0:7})

Name:           figcraft
Version:        0.10.0
Release:        2%{?dist}
Summary:        Open-source native interface design and prototyping application built in Rust

License:        (MIT OR Apache-2.0) AND OFL-1.1
URL:            https://github.com/storytold/figcraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        https://github.com/storytold/craft-fonts/archive/%{craft_fonts_commit}/craft-fonts-%{craft_fonts_short}.tar.gz

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
FigCraft is an open-source, native interface design and prototyping
application written in Rust. It offers frames, auto layout, components and
variants, vector networks, styles, variables and interactive prototypes in a
fast app that works offline.

This package also ships figcraft-cli, a headless companion for rendering and
exporting design files, running scripts and serving an MCP endpoint.

%prep
%autosetup -n %{name}-%{version} -a 1
mv craft-fonts-%{craft_fonts_commit} craft-fonts

%build
export CARGO_HOME=$PWD/.cargo-home
export RUSTFLAGS="%{?build_rustflags}"
export CRAFT_FONTS_DIR=$PWD/craft-fonts
export CRAFT_FONTS_REQUIRED=1
cargo build --release --locked -p figcraft -p figcraft-cli

%install
install -Dpm 0755 target/release/figcraft %{buildroot}%{_bindir}/figcraft
install -Dpm 0755 target/release/figcraft-cli %{buildroot}%{_bindir}/figcraft-cli
install -Dpm 0644 packaging/linux/%{app_id}.desktop %{buildroot}%{_datadir}/applications/%{app_id}.desktop
install -Dpm 0644 packaging/linux/%{app_id}.mime.xml %{buildroot}%{_datadir}/mime/packages/%{app_id}.xml
install -d %{buildroot}%{_metainfodir}
sed -e 's/@VERSION@/%{version}/g' \
    -e "s/@DATE@/$(date -u -d "@${SOURCE_DATE_EPOCH:-$(date +%%s)}" +%%F)/g" \
    packaging/linux/%{app_id}.metainfo.xml.in \
    > %{buildroot}%{_metainfodir}/%{app_id}.metainfo.xml
install -d %{buildroot}%{_datadir}/icons
cp -a assets/app-icon/hicolor %{buildroot}%{_datadir}/icons/
for f in craft-fonts/fonts/*/OFL.txt; do
    cp -p "$f" "OFL-$(basename "$(dirname "$f")").txt"
done

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{app_id}.desktop
appstreamcli validate --no-net %{buildroot}%{_metainfodir}/%{app_id}.metainfo.xml

%files
%license LICENSE-APACHE LICENSE-MIT OFL-*.txt
%doc README.md
%{_bindir}/figcraft
%{_bindir}/figcraft-cli
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/mime/packages/%{app_id}.xml
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/%{app_id}.*

%changelog
%autochangelog
