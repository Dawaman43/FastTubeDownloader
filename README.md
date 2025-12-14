# FastTube Downloader v2

**FastTube Downloader** is a powerful, IDM-style universal download manager for Linux. It works with **any website** and **any file type** - not just YouTube! It combines the robustness of `yt-dlp` and `aria2` with a modern, dark-themed GTK interface.

![FastTube Downloader Screenshot](https://github.com/Dawaman43/FastTubeDownloader/raw/main/screenshot.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](version.txt)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## 🚀 What's New in v2

- **Universal Download Support**: Download from any website, not just YouTube
- **All File Types**: Videos, music, documents, archives, programs, images - everything!
- **IDM-Style Categories**: Auto-organize files into Videos/, Music/, Documents/, Archives/, etc.
- **Playlist Folder Organization**: Playlists download to `Videos/[PlaylistName]/`
- **Background Downloads**: Runs in background without blocking your workflow
- **Context Menu Integration**: Right-click any link to "Download with FastTube"
- **System Tray Support**: Minimize to tray for background operation
- **Browser Extension v2.1.2**: Works on ALL websites with download interception
- **Rust-Powered Engine**: Optional high-performance download engine (3-5x faster)
- **Improved Performance**: Faster downloads with optimized connection handling

## ✨ Features

- **IDM-Style Interface**: Modern dark UI with blue gradients, card-style list items, and animated progress bars
- **Universal Browser Integration**: Chrome/Chromium/Firefox extension intercepts downloads from any site
- **High Performance**: Uses `aria2` for multi-connection downloads and `yt-dlp` for video extraction
- **Smart Categorization**: Automatically sorts downloads into category folders
- **Playlist Support**: Automatically organizes playlist downloads into subfolders
- **Detailed Stats**: Real-time display of download speed, ETA, and file size
- **Queue Management**: Pause, resume, and prioritize downloads
- **Drag & Drop**: Drop URLs directly into the window

## 📦 Installation

### Prerequisites
- Python 3.8+
- `yt-dlp`
- `aria2`
- GTK3 and Python GObject bindings

### Quick Install (Linux)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Dawaman43/FastTubeDownloader.git
    cd FastTubeDownloader
    ```

2.  **Run the setup script:**
    ```bash
    sudo ./setup.sh
    ```
    This will install the app to `/opt/FastTubeDownloader`, create a desktop entry, and set up the native messaging host for browser integration.

3.  **Install the Browser Extension:**

    **Chrome/Chromium:**
    - Open Chrome/Chromium and go to `chrome://extensions`
    - Enable **Developer mode**
    - Click **Load unpacked**
    - Select the `FastTubeDownloader` folder (where `manifest.json` is located)
    - Note the Extension ID. If it differs from the one in `EXTENSION_ID_GUIDE.md`, update `native_host/com.fasttube.downloader.json` and re-run `setup.sh`

    **Firefox:**
    - Open Firefox and go to `about:debugging#/runtime/this-firefox`
    - Click **Load Temporary Add-on**
    - Select `manifest.firefox.json` from the FastTubeDownloader folder

## 🎯 Usage

1.  **Launch the App**: Open "FastTube Downloader" from your applications menu
2.  **Download**:
    - **From Browser**: Navigate to any website. The extension will intercept downloads and send them to the app
    - **Context Menu**: Right-click any link → "Download with FastTube"
    - **Manual**: Paste a URL into the "Add URL" box in the app and click "+"
3.  **Manage**: Use the toolbar buttons to pause, resume, or remove downloads

### Supported Sites

Thanks to `yt-dlp`, FastTube supports **1000+ video sites** including:
- YouTube (videos, playlists, channels)
- Vimeo, Dailymotion, Twitch
- Facebook, Instagram, Twitter, TikTok
- And many more!

Plus direct downloads from **any website** for:
- Videos (.mp4, .mkv, .webm, etc.)
- Music (.mp3, .flac, .m4a, etc.)
- Documents (.pdf, .docx, .xlsx, etc.)
- Archives (.zip, .rar, .7z, etc.)
- Programs (.deb, .rpm, .AppImage, etc.)
- Images (.jpg, .png, .gif, etc.)

## 📁 File Organization

FastTube automatically organizes your downloads:

```
~/Downloads/
├── Videos/
│   ├── MyPlaylist/          # Playlists get their own folder
│   │   ├── Video1.mp4
│   │   └── Video2.mp4
│   └── SingleVideo.mp4
├── Music/
│   └── Song.mp3
├── Documents/
│   └── Report.pdf
├── Archives/
│   └── Files.zip
└── Programs/
    └── app.AppImage
```

## 🚀 Performance Optimization (Optional)

For maximum download speed, build the optional Rust engine:

```bash
# Install Rust (one-time setup)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Build with Rust engine
sudo ./setup.sh --with-rust
```

**Benefits**:
- 3-5x faster downloads for large files
- Lower CPU and memory usage
- Better connection management

If Rust isn't available, the app automatically falls back to aria2c (still fast!).

See [BUILD_RUST.md](BUILD_RUST.md) for details.

## 🔧 Configuration

Settings are stored in `~/.config/FastTubeDownloader/config.json`:

- **Download Folder**: Base directory for downloads
- **Category Mode**: `idm` (categorized) or `flat` (single folder)
- **Max Connections**: Number of parallel connections per download
- **Max Concurrent**: Number of simultaneous downloads
- **Speed Limit**: Download speed limit in KB/s

## 📦 Packaging

To create packages for your distribution:

```bash
./release.sh
```

This will generate:
- **RPM**: `dist/rpm/` (requires `rpmbuild`)
- **DEB**: `dist/deb/` (requires `dpkg-deb`)
- **Arch**: `dist/arch/` (PKGBUILD, requires `makepkg`)
- **AppImage**: `dist/appimage/` (requires `appimagetool`)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Start for Contributors

```bash
# Clone
git clone https://github.com/Dawaman43/FastTubeDownloader.git
cd FastTubeDownloader

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install yt-dlp

# Run the app
python3 gui/main_window.py
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube and video site downloader
- [aria2](https://aria2.github.io/) - Multi-protocol download utility
- All our contributors!

---

**Made with ❤️ for the open source community**
