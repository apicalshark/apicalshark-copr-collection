Name:           podman-docker-socket-compat
Version:        0.0.2
Release:        1
Summary:        Provides docker.socket and docker.service aliases for Podman's socket
License:        MIT
URL:            https://github.com/apicalshark/podman-docker-socket-compat
BuildArch:      noarch
Requires:       podman
Requires:       podman-docker
Requires:       systemd

%description
This package creates symbolic links in /etc/systemd/system to make docker.socket and docker.service point to podman.socket and
podman.service respectively. This is useful for Gnome Shell extensions or other tools that expect
systemctl is-active docker.socket or similar commands to work.

%prep

%install
mkdir -p %{buildroot}/etc/systemd/system
ln -s /usr/lib/systemd/system/podman.socket %{buildroot}/etc/systemd/system/docker.socket
ln -s /usr/lib/systemd/system/podman.service %{buildroot}/etc/systemd/system/docker.service

%files
%attr(0644,root,root) /etc/systemd/system/docker.socket
%attr(0644,root,root) /etc/systemd/system/docker.service
