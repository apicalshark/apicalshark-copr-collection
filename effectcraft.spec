%define _debugsource_template %{nil}
%define debug_package %{nil}

# Disable all default Red Hat / Fedora build and compiler flags (CFLAGS, LDFLAGS, RUSTFLAGS, annobin, package notes, hardening)
%undefine _auto_set_build_flags

# Only use RUSTFLAGS for compiler target-cpu instruction set tuning:
%ifarch x86_64
%global custom_rustflags -C target-cpu=x86-64-v3
%else
%global custom_rustflags %{nil}
%endif

%global app_id ai.storyteller.effectcraft
%global craft_fonts_commit bfcbf714e45a3ea8e98f88ab2b7971372a576414
%global craft_fonts_short %(c=%{craft_fonts_commit}; echo ${c:0:7})

Name:           effectcraft
Version:        0.23.1
Release:        2%{?dist}
Summary:        Open-source native motion graphics and visual effects compositor built in Rust

License:        (MIT OR Apache-2.0) AND OFL-1.1
URL:            https://github.com/storytold/effectcraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        https://github.com/storytold/craft-fonts/archive/%{craft_fonts_commit}/craft-fonts-%{craft_fonts_short}.tar.gz

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
EffectCraft is an open-source, native motion graphics and visual effects
compositor written in Rust. It composes layered scenes with keyframes and a
graph editor, masks and shapes, text animators, expressions, 3D cameras and
lights, over 300 effects and a render queue, with GPU compositing.

This package also ships effectcraft-cli, a headless companion for rendering
frames and sequences, running command scripts and serving an MCP endpoint.

%prep
%autosetup -n %{name}-%{version} -a 1
mv craft-fonts-%{craft_fonts_commit} craft-fonts

%build
export CARGO_HOME=$PWD/.cargo-home
export RUSTFLAGS="%{custom_rustflags}"

# Cargo profiles configure optimizations, LTO, and stripping safely for target binaries:
export CARGO_PROFILE_RELEASE_OPT_LEVEL=3
export CARGO_PROFILE_RELEASE_DEBUG=false
export CARGO_PROFILE_RELEASE_STRIP="symbols"
export CARGO_PROFILE_RELEASE_LTO="thin"
export CARGO_PROFILE_RELEASE_CODEGEN_UNITS=16
export CRAFT_FONTS_DIR=$PWD/craft-fonts
export CRAFT_FONTS_REQUIRED=1
cargo build --release --locked -p effectcraft -p effectcraft-cli

%install
install -Dpm 0755 target/release/effectcraft %{buildroot}%{_bindir}/effectcraft
install -Dpm 0755 target/release/effectcraft-cli %{buildroot}%{_bindir}/effectcraft-cli
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
%{_bindir}/effectcraft
%{_bindir}/effectcraft-cli
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/mime/packages/%{app_id}.xml
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/%{app_id}.*

%changelog
%autochangelog
