%define _debugsource_template %{nil}
%define debug_package %{nil}

%global app_id ai.storyteller.soundcraft

Name:           soundcraft
Version:        0.13.1
Release:        1%{?dist}
Summary:        Open-source native digital audio workstation built in Rust

License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/soundcraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  cargo
BuildRequires:  rust >= 1.90
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
Recommends:     (pipewire-alsa or alsa-plugins-pulseaudio)

%description
SoundCraft is an open-source, native digital audio workstation written in Rust.
It records, edits and mixes multitrack audio and MIDI in Edit and Mix windows,
with non-destructive clip editing, a mixer with inserts, sends, buses,
automation and metering, built-in EQ, dynamics, reverb, delay and instruments.

This package also ships soundcraft-cli, a headless companion for editing,
converting and bouncing audio, controlling a running instance and serving an
MCP endpoint.

%prep
%autosetup -n %{name}-%{version}

%build
export CARGO_HOME=$PWD/.cargo-home
export RUSTFLAGS="%{?build_rustflags}"
cargo build --release --locked -p soundcraft -p soundcraft-cli

%install
install -Dpm 0755 target/release/soundcraft %{buildroot}%{_bindir}/soundcraft
install -Dpm 0755 target/release/soundcraft-cli %{buildroot}%{_bindir}/soundcraft-cli
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
%{_bindir}/soundcraft
%{_bindir}/soundcraft-cli
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/mime/packages/%{app_id}.xml
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/%{app_id}.*

%changelog
%autochangelog
