%global debug_package %{nil}
%global _pkgname Vita3K

Name:           vita3k
Version:        0.0.2
Release:        1%{?dist}
Summary:        Experimental PlayStation Vita emulator
License:        GPLv2
URL:            https://github.com/Vita3K/Vita3K

BuildRequires:  git cmake ninja-build SDL2-devel pkg-config gtk3-devel clang lld xdg-desktop-portal openssl openssl-devel libstdc++-static

%description
Vita3K is an experimental open-source PlayStation Vita emulator for Windows,
Linux, macOS and Android.

%prep
git clone --recursive %{url}.git %{_pkgname}

%build
pushd %{_pkgname}
cmake -B build -GNinja \
      -DCMAKE_C_COMPILER=clang \
      -DCMAKE_CXX_COMPILER=clang++ \
      -DCMAKE_EXE_LINKER_FLAGS="-fuse-ld=lld" \
      -DCMAKE_SHARED_LINKER_FLAGS="-fuse-ld=lld" \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX="/usr" \
      -DUSE_VITA3K_UPDATE=OFF \
      -DXXH_X86DISPATCH_ALLOW_AVX=ON
ninja
popd

%install
pushd build
DESTDIR=$RPM_BUILD_ROOT ninja install
popd

%files
%{_bindir}/%{_pkgname}
%dir %{_datadir}/%{_pkgname}
%{_datadir}/%{_pkgname}/*
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_datadir}/applications/%{name}.desktop

%changelog
%autochangelog