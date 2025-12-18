%global custom_cflags -O3 -march=x86-64-v3 -fPIC -fno-semantic-interposition
%global _hardened_build 0
%global _lto_cflags -flto=auto

Name:           pkg2zip-fork
Version:        2.6
Release:        1%{?dist}
Summary:        Decrypts PlayStation Vita pkg files and packages them into zip archives
License:        Unlicense
URL:            https://github.com/lusid1/pkg2zip

Source0:        %{url}/archive/%{version}.tar.gz
Source1:        memset.patch

BuildRequires:  make
BuildRequires:  gcc

%description
This is lusid1's fork of pkg2zip, recommended by NoPayStation. 
It decrypts PlayStation Vita pkg files and packages them into zip archives.

%prep
%setup -q -n pkg2zip-%{version}
patch -p1 -i %{SOURCE1}

%build
CFLAGS="%{optflags} %{custom_cflags}"
LDFLAGS="%{build_ldflags} %{_lto_cflags}"
%make_build CFLAGS="$CFLAGS" LDFLAGS="$LDFLAGS"

%install
install -Dm755 pkg2zip %{buildroot}%{_bindir}/pkg2zip

%files
%{_bindir}/pkg2zip

%changelog
%autochangelog
