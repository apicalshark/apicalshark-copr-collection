%define _debugsource_template %{nil}
%define debug_package %{nil}

%global app_id ai.storyteller.pdfcraft

Name:           pdfcraft
Version:        0.13.0
Release:        1%{?dist}
Summary:        Open-source native PDF reader and editor built in Rust

License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/pdfcraft
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
Recommends:     cups-client

%description
PdfCraft is an open-source, native PDF reader and editor written in Rust. It
renders documents with proper kerning, ligatures, complex scripts and vertical
CJK text, combines, splits, rotates and reorders pages, fills and signs forms,
applies redaction and encryption, and keeps long documents navigable with
bookmarks, thumbnails and page labels.

This package also ships pdfcraft-cli, a headless companion for inspecting and
rendering PDFs, extracting text, editing pages, combining, splitting, running
scripts and serving an MCP endpoint.

%prep
%autosetup -n %{name}-%{version}

%build
export CARGO_HOME=$PWD/.cargo-home
export RUSTFLAGS="%{?build_rustflags}"
cargo build --release --locked -p pdfcraft -p pdfcraft-cli

%install
install -Dpm 0755 target/release/pdfcraft %{buildroot}%{_bindir}/pdfcraft
install -Dpm 0755 target/release/pdfcraft-cli %{buildroot}%{_bindir}/pdfcraft-cli
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
%{_bindir}/pdfcraft
%{_bindir}/pdfcraft-cli
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/mime/packages/%{app_id}.xml
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/%{app_id}.*

%changelog
%autochangelog
