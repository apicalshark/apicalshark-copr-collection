# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 ApicalShark
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

%bcond_with tests

%global toolchain clang

# Performance-only build flags per redhat-rpm-config buildflags.md
%global _lto_cflags %{nil}
%undefine _hardened_build
%undefine _annotated_build
%undefine _fortify_level
%undefine _include_frame_pointers
%global debug_package %{nil}
%global eden_build_preset v3
%ifarch aarch64
%global eden_build_preset generic
%endif

%ifarch x86_64
%global optflags %(echo %{optflags} | sed -e 's/-O2/-O3/' -e 's/-march=x86-64-v2/-march=x86-64-v3/' -e 's/-march=x86-64/-march=x86-64-v3/' -e 's/-march=generic/-march=x86-64-v3/' -e 's/ -g / /')
%else
%global optflags %(echo %{optflags} | sed -e 's/-O2/-O3/' -e 's/ -g / /')
%endif

Name:           eden
Version:        0.2.1
Release:        1
Summary:        NS emulator/debugger

License:        GPL-3.0-or-later
URL:            https://eden-emu.dev/
Source0:        https://git.eden-emu.dev/eden-emu/eden/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        https://github.com/Eden-CI/PGO/releases/download/v020525/eden.profdata
Source2:        https://github.com/lat9nq/tzdb_to_nx/releases/download/221202/221202.zip

BuildRequires:  alsa-lib-devel
BuildRequires:  boost-devel >= 1.75.0
BuildRequires:  cmake >= 3.22
BuildRequires:  doxygen
BuildRequires:  enet-devel

BuildRequires:  fmt-devel >= 8.0.1
BuildRequires:  clang
BuildRequires:  lld
BuildRequires:  glslang
BuildRequires:  graphviz
BuildRequires:  hidapi-devel
BuildRequires:  hicolor-icon-theme
BuildRequires:  jack-audio-connection-kit-devel
BuildRequires:  libusb1-devel
BuildRequires:  libva-devel
BuildRequires:  libXext-devel
BuildRequires:  libxml2-devel
BuildRequires:  libzip-devel
BuildRequires:  libzstd-devel
BuildRequires:  llvm-devel
BuildRequires:  lz4-devel
BuildRequires:  mold
BuildRequires:  nasm
BuildRequires:  ncurses-devel
BuildRequires:  nettle-devel
BuildRequires:  ninja-build
BuildRequires:  json-devel >= 3.8
BuildRequires:  openssl-devel
BuildRequires:  opus-devel
BuildRequires:  pcre2-devel
BuildRequires:  pulseaudio-libs-devel
BuildRequires:  libshaderc-devel
BuildRequires:  speexdsp-devel
BuildRequires:  SDL2-devel >= 2.0.18
BuildRequires:  unzip
BuildRequires:  vulkan-loader-devel >= 1.3.274
BuildRequires:  vulkan-utility-libraries-devel
BuildRequires:  wayland-devel
BuildRequires:  zlib-devel

# Qt
BuildRequires:  qt6-qtbase-devel
BuildRequires:  qt6-qtbase-private-devel
BuildRequires:  qt6-qtcharts-devel
BuildRequires:  qt6-linguist
BuildRequires:  qt6-qtmultimedia-devel
BuildRequires:  qt6-qtwebengine-devel
BuildRequires:  quazip-qt6-devel

# Build tools needed by external CPM dependencies
BuildRequires:  autoconf
BuildRequires:  libtool
BuildRequires:  cmake(SPIRV-Headers)
BuildRequires:  cmake(SPIRV-Tools)
BuildRequires:  jq
BuildRequires:  pkgconfig(gamemode)
BuildRequires:  pkgconfig(libudev)
BuildRequires:  stb_image-devel
BuildRequires:  stb_image_write-devel
BuildRequires:  stb_image_resize-devel
BuildRequires:  VulkanMemoryAllocator-devel

Requires:       gamemode

ExclusiveArch:  x86_64 aarch64

%description
Eden is an open source NS emulator/debugger.

%prep
%setup -c -T
tar xf %{SOURCE0} --strip-components=1
mkdir -p build/externals/nx_tzdb
unzip %{SOURCE2} -d build/externals/nx_tzdb/nx_tzdb/

# Enforce package versioning in GUI
sed -i \
-e 's|@GIT_BRANCH@|dev|g' \
-e 's|@GIT_DESC@|%{version}|g' \
-e 's|@BUILD_NAME@|%{name}|g' \
src/common/scm_rev.cpp.in

%build
# Fix "too many open files" error
ulimit -n 2048

%cmake \
        -GNinja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_IGNORE_PATH=/home/linuxbrew/.linuxbrew \
        -DENABLE_QT_TRANSLATION=ON \
        -DENABLE_LTO=ON \
        -DDYNARMIC_ENABLE_LTO=ON \
        -DUSE_DISCORD_PRESENCE=ON \
        -DUSE_FASTER_LINKER=ON \
        -Dhttplib_FORCE_BUNDLED=ON \
        -DYUZU_USE_BUNDLED_SDL2=OFF \
        -DYUZU_USE_EXTERNAL_SDL2=OFF \
        -DYUZU_USE_BUNDLED_FFMPEG=ON \
        -DYUZU_USE_QT_MULTIMEDIA=ON \
        -DYUZU_USE_QT_WEB_ENGINE=ON \
        -DYUZU_BUILD_PRESET=%{eden_build_preset} \
        -DYUZU_TESTS=%{?with_tests:ON}%{!?with_tests:OFF} \
        -DDYNARMIC_TESTS=OFF \
        -DBUILD_TESTING=OFF \
        -DUSE_CCACHE=OFF \
        -DCMAKE_C_FLAGS="%{build_cflags} -fprofile-use=%{SOURCE1} -Wno-backend-plugin -Wno-profile-instr-unprofiled -Wno-profile-instr-out-of-date" \
        -DCMAKE_CXX_FLAGS="%{build_cxxflags} -fprofile-use=%{SOURCE1} -Wno-backend-plugin -Wno-profile-instr-unprofiled -Wno-profile-instr-out-of-date" \
        -Wno-dev

%cmake_build

%install
%cmake_install

%files
%doc README.md
%license LICENSE.txt
%{_bindir}/%{name}
%{_bindir}/%{name}-cli
%{_bindir}/%{name}-room
%{_datadir}/applications/dev.eden_emu.eden.desktop
%{_datadir}/icons/hicolor/scalable/apps/dev.eden_emu.eden.svg
%{_datadir}/metainfo/dev.eden_emu.eden.metainfo.xml
%{_datadir}/mime/packages/dev.eden_emu.eden.xml

%changelog
* Tue Jun 16 2026 ApicalShark - 0.2.1-1
- Initial Fedora RPM build
