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
%make_build

%install
install -Dm755 pkg2zip %{buildroot}%{_bindir}/pkg2zip

%files
%{_bindir}/pkg2zip

%changelog
%autochangelog
