Name:           python3-trayer
Version:        0.1.1
Release:        1
Summary:        Add system tray icons with context menus
License:        BSD-3-Clause
URL:            https://github.com/Enne2/trayer
Source0:        https://github.com/Enne2/trayer/archive/refs/tags/v%{version}.tar.gz
BuildRequires:  python3
BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  fdupes
BuildArch:      noarch

%description
Add system tray icons with context menus to your GTK4 applications with just a few lines of code.

%prep
%autosetup -p1 -n trayer-%{version}

%build
%pyproject_wheel

%install
%pyproject_install

%files
%{python3_sitelib}/*

%changelog
%autochangelog
