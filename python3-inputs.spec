Name:           python3-inputs
Version:        0.5
Release:        1
Summary:        Cross-platform Python support for keyboards, mice and gamepads
License:        BSD-3-Clause
URL:            https://github.com/zeth/inputs
Source0:        https://github.com/zeth/inputs/archive/refs/tags/v%{version}.tar.gz
Patch0:         3203c9e25f1e14c4316d85d59c536b4e407f569f.patch
BuildRequires:  python3
BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  fdupes
BuildArch:      noarch

%description
Cross-platform Python support for keyboards, mice and gamepads.

%prep
%autosetup -p1 -n inputs-%{version}

%build
%pyproject_wheel

%install
%pyproject_install

%files
%{python3_sitelib}/*

%changelog
%autochangelog
