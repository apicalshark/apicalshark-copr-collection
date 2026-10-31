%define _debugsource_template %{nil}
%define debug_package %{nil}

%global app_id ai.storyteller.wordcraft
%global craft_fonts_commit b076417b5880bd4154bd22f00695b1d28c6bea83
%global craft_fonts_short %(c=%{craft_fonts_commit}; echo ${c:0:7})
%global craft_i18n_commit 9205108cfdced5177706264038848b68b2422d2b
%global craft_i18n_short %(c=%{craft_i18n_commit}; echo ${c:0:7})

Name:           wordcraft
Version:        0.13.2
Release:        1%{?dist}
Summary:        Open-source native word processor built in Rust

License:        (MIT OR Apache-2.0) AND OFL-1.1
URL:            https://github.com/storytold/wordcraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        https://github.com/storytold/craft-fonts/archive/%{craft_fonts_commit}/craft-fonts-%{craft_fonts_short}.tar.gz
Source2:        https://github.com/storytold/craft-i18n/archive/%{craft_i18n_commit}/craft-i18n-%{craft_i18n_short}.tar.gz

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
WordCraft is an open-source, native word processor written in Rust. It offers
a familiar ribbon workflow with styles, tables, track changes, references and
mail merge, and reads and writes Word .docx files as well as ODT, RTF, Markdown
and HTML documents.

This package also ships wordcraft-cli, a headless companion for editing and
converting documents, running scripts and serving an MCP endpoint.

%prep
%autosetup -n %{name}-%{version} -a 1
%setup -q -D -T -a 2 -n %{name}-%{version}
mv craft-fonts-%{craft_fonts_commit} craft-fonts
mv craft-i18n-%{craft_i18n_commit} craft-i18n

%build
export CARGO_HOME=$PWD/.cargo-home
export RUSTFLAGS="%{?build_rustflags}"
export CRAFT_FONTS_DIR=$PWD/craft-fonts
export CRAFT_FONTS_REQUIRED=1
export CRAFT_I18N_DIR=$PWD/craft-i18n
export CRAFT_I18N_REQUIRED=1
cargo build --release --locked -p wordcraft -p wordcraft-cli

%install
install -Dpm 0755 target/release/wordcraft %{buildroot}%{_bindir}/wordcraft
install -Dpm 0755 target/release/wordcraft-cli %{buildroot}%{_bindir}/wordcraft-cli
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
%{_bindir}/wordcraft
%{_bindir}/wordcraft-cli
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/mime/packages/%{app_id}.xml
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/%{app_id}.*

%changelog
%autochangelog
