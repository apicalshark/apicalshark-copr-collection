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

%global app_id io.tangencylabs.solidcraft

Name:           solidcraft
Version:        0.30.1
Release:        1%{?dist}
Summary:        Open-source parametric 3D CAD application built in pure Rust

License:        MIT OR Apache-2.0
URL:            https://github.com/tangency-labs/solidcraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

# Migration / compatibility shim: replaces and obsoletes solvecraft
Provides:       solvecraft = %{version}-%{release}
Obsoletes:      solvecraft < 0.8.0

BuildRequires:  cargo
BuildRequires:  rust >= 1.95
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
Recommends:     libX11-xcb
Recommends:     libxcb
Recommends:     libXcursor
Recommends:     libXi
Recommends:     mesa-vulkan-drivers
Recommends:     xdg-desktop-portal

%description
SolidCraft is an open-source parametric 3D CAD application built in pure Rust.
It provides sketches with a geometric constraint solver, a parametric feature
timeline, components and joints, sheet metal, and support for STEP, IGES, 3MF,
STL and OBJ file formats.

This package ships:
- solidcraft: the graphical 3D CAD desktop application
- solidcraft-cli: headless CLI runner, exporter, snapshot renderer and MCP server
- solvecraft-cli: compatibility forwarding alias to solidcraft-cli

%prep
%autosetup -n %{name}-%{version}

%build
export CARGO_HOME=$PWD/.cargo-home
export RUSTFLAGS="%{custom_rustflags}"

# Cargo profiles configure optimizations, LTO, and stripping safely for target binaries:
cargo build --release --locked -p solidcraft -p solidcraft-cli

%install
# Install the three binaries (solidcraft, solidcraft-cli, and compatibility alias solvecraft-cli)
install -Dm 0755 target/release/%{name} %{buildroot}%{_bindir}/%{name}
install -Dm 0755 target/release/%{name}-cli %{buildroot}%{_bindir}/%{name}-cli
install -Dm 0755 target/release/solvecraft-cli %{buildroot}%{_bindir}/solvecraft-cli

# Install desktop entry file
install -Dm 0644 assets/platforms/linux/%{app_id}.desktop \
    %{buildroot}%{_datadir}/applications/%{app_id}.desktop

# Install AppStream metadata
mkdir -p %{buildroot}%{_metainfodir}
sed -e 's/@VERSION@/%{version}/g' \
    -e 's/@DATE@/%(date -u +%%Y-%%m-%%d)/g' \
    assets/platforms/linux/%{app_id}.metainfo.xml.in > \
    %{buildroot}%{_metainfodir}/%{app_id}.metainfo.xml

# Install shared MIME type definition
install -Dm 0644 assets/platforms/linux/%{app_id}.mime.xml \
    %{buildroot}%{_datadir}/mime/packages/%{app_id}.xml

# Install application icons
for s in 16 24 32 48 64 128 256 512; do
    icon_src="assets/icons/app/linux/exports/hicolor/${s}x${s}/apps/%{app_id}.png"
    if [ -f "$icon_src" ]; then
        install -Dm 0644 "$icon_src" \
            "%{buildroot}%{_datadir}/icons/hicolor/${s}x${s}/apps/%{app_id}.png"
    fi
done

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{app_id}.desktop
appstreamcli validate --no-net --explain %{buildroot}%{_metainfodir}/%{app_id}.metainfo.xml

%files
%license LICENSE-MIT LICENSE-APACHE NOTICE THIRD-PARTY-LICENSES.txt
%doc README.md
%{_bindir}/%{name}
%{_bindir}/%{name}-cli
%{_bindir}/solvecraft-cli
%{_datadir}/applications/%{app_id}.desktop
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/mime/packages/%{app_id}.xml
%{_datadir}/icons/hicolor/*/apps/%{app_id}.png

%changelog
%autochangelog
