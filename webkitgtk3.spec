Name:           webkitgtk3
Version:        2.99.99
Release:        99.placeholder%{?dist}
Summary:        Fake placeholder for webkitgtk3 to satisfy dependencies
License:        WTFPL
BuildArch:      noarch

Provides:       webkitgtk3 = %{version}-%{release}

# Dont fuck with real things.
# Provides:       libwebkitgtk-3.0.so.0()(64bit)
# Provides:       pkgconfig(webkitgtk-3.0)

%description
This is a fake placeholder package for webkitgtk3. It contains no files 
and does not install any libraries. It exists solely to satisfy 
RPM dependency requirements for other software.

%prep
# Nothing to prepare

%build
# Nothing to build

%install
# Create a dummy directory so the build doesn't fail for being empty
mkdir -p %{buildroot}%{_docdir}/%{name}
echo "This is a placeholder webkitgtk3 package. " > %{buildroot}%{_docdir}/%{name}/README

%files
%{_docdir}/%{name}/README

%changelog
* Tue May 12 2026 Placeholder <johndoe@johndoe.com> - 2.99.99-99
- Initial fake placeholder release
