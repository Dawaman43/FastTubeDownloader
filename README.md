# FastTube Downloader

**FastTube Downloader** is a powerful, IDM-style download manager for Linux that integrates seamlessly with your browser. It combines the robustness of `yt-dlp` and `aria2` with a modern, dark-themed GTK interface.

![FastTube Downloader Screenshot](https://github.com/Dawaman43/FastTubeDownloader/raw/main/screenshot.png)

## Features

- **IDM-Style Interface**: Modern dark UI with blue gradients, card-style list items, and animated progress bars.
- **Browser Integration**: Chrome/Chromium extension intercepts downloads and sends them to the desktop app.
- **High Performance**: Uses `aria2` for multi-connection downloads and `yt-dlp` for video extraction.
- **Playlist Support**: Automatically organizes playlist downloads into subfolders.
- **Detailed Stats**: Real-time display of download speed, ETA, and file size.
- **Smart Categorization**: Automatically sorts downloads into Music/Videos folders.
- **Queue Management**: Pause, resume, and prioritize downloads.

## Installation

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

3.  **Install the Chrome Extension:**
    - Open Chrome/Chromium and go to `chrome://extensions`.
    - Enable **Developer mode**.
    - Click **Load unpacked**.
    - Select the `FastTubeDownloader` folder (where `manifest.json` is located).
    - Note the Extension ID. If it differs from the one in `EXTENSION_ID_GUIDE.md`, update `native_host/com.fasttube.downloader.json` and re-run `setup.sh`.

## Usage

1.  **Launch the App**: Open "FastTube Downloader" from your applications menu.
2.  **Download**:
    - **From Browser**: Navigate to a YouTube video or any downloadable file. The extension will intercept the download and send it to the app.
    - **Manual**: Paste a URL into the "Add URL" box in the app and click "+".
3.  **Manage**: Use the toolbar buttons to pause, resume, or remove downloads.

## Packaging

To create packages for your distribution:

```bash
./release.sh
```

This will generate:
- **RPM**: `dist/rpm/` (requires `rpmbuild`)
- **DEB**: `dist/deb/` (directory structure, requires `dpkg-deb`)
- **Arch**: `dist/arch/` (PKGBUILD, requires `makepkg`)

## License

MIT License
