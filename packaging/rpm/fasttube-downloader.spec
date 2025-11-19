Name:           fasttube-downloader
Version:        2.1
Release:        1%{?dist}
Summary:        FastTube Downloader – YouTube & generic file downloader
License:        MIT
URL:            https://github.com/Dawaman43/FastTubeDownloader
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3, python3-gobject, gtk3, yt-dlp, aria2

%description
Fast GTK desktop + browser extension integrated downloader using yt-dlp and aria2.

%prep
%setup -q

%build
# No build step needed

%install
mkdir -p %{buildroot}/opt/FastTubeDownloader
rsync -a --exclude '.git' --exclude 'dist' --exclude '__pycache__' --exclude 'packaging' . %{buildroot}/opt/FastTubeDownloader/
install -Dm755 packaging/launch-wrapper.sh %{buildroot}/usr/bin/fasttube-downloader
install -Dm644 packaging/fasttube-downloader.desktop %{buildroot}/usr/share/applications/fasttube-downloader.desktop
install -Dm644 icon16.png %{buildroot}/usr/share/icons/hicolor/16x16/apps/fasttube-downloader.png
install -Dm644 icon48.png %{buildroot}/usr/share/icons/hicolor/48x48/apps/fasttube-downloader.png
install -Dm644 icon128.png %{buildroot}/usr/share/icons/hicolor/128x128/apps/fasttube-downloader.png

%post
update-desktop-database >/dev/null 2>&1 || true
gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true

%files
%license LICENSE
%doc README.md
/opt/FastTubeDownloader
/usr/bin/fasttube-downloader
/usr/share/applications/fasttube-downloader.desktop
/usr/share/icons/hicolor/*/apps/fasttube-downloader.png

%changelog
* Wed Nov 19 2025 FastTube Downloader <maintainer@example.com> - 2.1-1
- Initial package
