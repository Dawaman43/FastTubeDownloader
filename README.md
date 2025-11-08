# FastTube Downloader

Fast, extensible desktop + browser extension YouTube & generic file downloader.

![FastTube Downloader Screenshot](https://github.com/Dawaman43/FastTubeDownloader/blob/main/.github/screenshot.png?raw=1)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub tag](https://img.shields.io/github/v/tag/Dawaman43/FastTubeDownloader?sort=semver)](https://github.com/Dawaman43/FastTubeDownloader/tags)
[![Build Release](https://github.com/Dawaman43/FastTubeDownloader/actions/workflows/release.yml/badge.svg)](https://github.com/Dawaman43/FastTubeDownloader/actions)

## Features
- Desktop GTK app with queue, history, parallel downloads
- High-speed media via yt-dlp; segmented generic downloads via aria2 (RPC optional)
- Generic file support with automatic folder categorisation by extension
- Playlist expansion with deduplication
- Native messaging bridge: Chrome (MV3) + Firefox (MV2) manifests
- Permanent extension ID tooling (stable across machines)
- Pause / resume for aria2 RPC generic downloads
- Auto-start option, clipboard detection, size persistence

## Quick Install (Linux)
Recommended (auto-detects distro, grabs prebuilt package if available, else falls back):
```bash
curl -fsSL https://raw.githubusercontent.com/Dawaman43/FastTubeDownloader/main/scripts/easy_install.sh | bash
```
This will:
- Install dependencies (python3-gi / GTK3, yt-dlp, aria2)
- Download and install the latest .deb or .rpm (if published)
- Fall back to local install via `setup.sh` when no package asset is found

Manual alternative:
```bash
./setup.sh
```
Then load the browser extension (for now still manual):
- Chrome / Chromium: chrome://extensions (Developer Mode) > Load unpacked > repo root
- Firefox: about:debugging#/runtime/this-firefox > Load Temporary Add-on > select `manifest.firefox.json`

To keep a permanent extension ID in Chrome, generate a key first (`python3 tools/generate_extension_key.py`) then reload.

### Direct Package Install (If you prefer manual)
Debian / Ubuntu:
```bash
wget -O fasttube.deb https://github.com/Dawaman43/FastTubeDownloader/releases/latest/download/fasttube-downloader_amd64.deb
sudo apt install ./fasttube.deb
```
Fedora / RHEL / openSUSE:
```bash
wget -O fasttube.rpm https://github.com/Dawaman43/FastTubeDownloader/releases/latest/download/fasttube-downloader.x86_64.rpm
sudo rpm -i fasttube.rpm
```
If the above links 404, the release doesn’t yet contain those assets—either wait for the next tagged build (CI attaches them) or use `scripts/easy_install.sh` / `./setup.sh`.

## Stable Extension ID
Generate and inject a key (produces a stable ID):
```bash
python3 tools/generate_extension_key.py
```
Reload extension. Re-run `./setup.sh` (the script auto-detects ID for native messaging).

## Packaging
Use the provided build script to produce Chrome and Firefox extension archives in `dist/`:
```bash
scripts/build.sh
```
Outputs:
- `dist/fasttube_chrome.zip` (Manifest V3)
- `dist/fasttube_firefox.zip` (Manifest V2)

You can also load unpacked directly from the repo during development.

## Linux Distribution Packages

### Debian/Ubuntu (.deb)
We provide a Debian packaging layout under `packaging/debian/`.

Build locally (requires `debhelper`):
```bash
cd packaging
dpkg-buildpackage -us -uc
```
The resulting `.deb` will appear one level up. Install with:
```bash
sudo apt install ./fasttube-downloader_*.deb
```

### Fedora/openSUSE/RHEL (RPM)
Spec file is at `packaging/rpm/fasttube-downloader.spec`.

Build locally (requires `rpm-build`):
```bash
mkdir -p ~/rpmbuild/{SOURCES,SPECS}
git archive --format=tar.gz --prefix=fasttube-downloader-0.1.0/ -o ~/rpmbuild/SOURCES/fasttube-downloader-0.1.0.tar.gz HEAD
cp packaging/rpm/fasttube-downloader.spec ~/rpmbuild/SPECS/
rpmbuild -ba ~/rpmbuild/SPECS/fasttube-downloader.spec
```

### Arch Linux (PKGBUILD)
PKGBUILD is at `packaging/arch/PKGBUILD`.

Build locally (requires `base-devel`):
```bash
cd packaging/arch
makepkg -si
```

### AppImage
AppImage recipe is provided at `packaging/AppImageBuilder.yml`.

Build (requires `appimage-builder`):
```bash
appimage-builder --recipe packaging/AppImageBuilder.yml
```

### Flatpak
Flatpak manifest at `packaging/flatpak/com.fasttube.downloader.json`.

Build and install locally (requires `flatpak-builder`):
```bash
flatpak-builder build-dir packaging/flatpak/com.fasttube.downloader.json --install --user --force-clean
flatpak run com.fasttube.downloader
```

### Snap
Snapcraft recipe at `packaging/snap/snapcraft.yaml`.

Build (requires `snapcraft`):
```bash
cd packaging/snap
snapcraft
```
Note: Snap is configured with `confinement: classic` to access aria2/yt-dlp and the filesystem.

## Native Messaging
Setup script installs the host JSON for Chrome/Chromium (and prompts or auto-computes extension ID). For Firefox, copy the same host file into:
```
~/.mozilla/native-messaging-hosts/com.fasttube.downloader.json
```
Adjust `allowed_extensions` (Firefox) / `allowed_origins` (Chrome) accordingly.

## Generic File Downloads
Select "Generic File" in the format combo or paste a direct URL (.zip/.apk/etc.). Categorisation uses `generic_extensions_map` in config.
If aria2 RPC enabled: pause/resume works from the queue.
If aria2 missing: (TODO) fallback will attempt curl / wget.

## Configuration File
Stored at `~/.config/FastTubeDownloader/config.json`.
Notable keys:
- enable_generic (bool)
- auto_start (bool)
- aria2_rpc_enabled (bool)
- aria2_rpc_port (int)
- generic_extensions_map (dict category -> [extensions])
- window_width / window_height (persisted)

## Developer Utilities
- `tools/generate_extension_key.py` – produce stable ID, patch manifest
- `tests/test_playlist_dedup.py` – simple playlist dedup test

## Future Enhancements
- In-app settings UI for toggles and extension map editing
- aria2 absence fallback to curl/wget
- Firefox native host installer section in setup.sh

## Legal Notice
This project provides tooling for downloading content. Ensure you comply with YouTube’s Terms of Service and local laws. You are responsible for how you use this software. The authors are not liable for misuse.

## Troubleshooting
| Issue | Fix |
|-------|-----|
| Extension ID changed | Re-run key script; ensure manifest.key kept; never overwrite private key unless intending ID change |
| Native host error in popup | Rerun `./setup.sh`; check extension ID alignment; inspect `~/.cache/fasttube-downloader.log` |
| Downloads not starting | Confirm control server log: `Control server listening on 127.0.0.1:47653` |
| Playlist duplicates | Already fixed via JSON flat playlist parser |

## License
MIT (add license file if distributing).

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md). Friendly contributions welcome! Good first issues are labeled.
