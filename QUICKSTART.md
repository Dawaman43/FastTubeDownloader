# FastTube Downloader v2.0.0 - Quick Start Guide

## Installation Complete! ✅

FastTube Downloader v2.0.0 is now installed and running!

## Current Status

- ✅ App installed to `/opt/FastTubeDownloader`
- ✅ Launcher created: `fasttube-downloader`
- ✅ Desktop entry added
- ✅ Firefox extension packaged: `dist/firefox/fasttube-downloader-firefox-2.1.2.xpi`
- ⚠️ System Tray: Temporarily disabled due to AppIndicator compatibility issue
  - App will close normally instead of minimizing to tray
  - Will be fixed in next update

## Launch the App

```bash
fasttube-downloader
```

Or search for "FastTube Downloader" in your applications menu.

## Load Browser Extensions

### Chrome/Chromium
1. Open `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select `/home/dave/FastTubeDownloader`

### Firefox (Local Testing)
1. Open `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Select `/home/dave/FastTubeDownloader/manifest.firefox.json`

### Firefox (Production - Submit to Mozilla)
1. Go to https://addons.mozilla.org/developers/addon/submit/distribution
2. Upload `dist/firefox/fasttube-downloader-firefox-2.1.2.xpi`
3. Follow instructions in `FIREFOX_SUBMISSION.md`

## Test the App

1. **YouTube Video**: Paste a YouTube URL and click "Add Download"
2. **YouTube Playlist**: Try a playlist URL - files will organize into subfolders
3. **Generic File**: Try a PDF or ZIP file URL
4. **Context Menu**: Right-click any link/video in your browser → "Download with FastTube"

## Features Available

✅ Universal download support (1000+ sites)
✅ All file types (videos, music, documents, archives, etc.)
✅ Smart folder organization (Videos/, Music/, Documents/, etc.)
✅ Playlist subfolders
✅ Multi-threaded downloads (16-32 connections)
✅ Context menu integration
✅ Background downloading
✅ Desktop notifications
⏳ System Tray (coming in next update)
⏳ Rust engine (optional, build with `sudo ./setup.sh --with-rust`)

## Troubleshooting

### App won't start
```bash
# Check for errors
python3 /opt/FastTubeDownloader/gui/main_window.py
```

### Extension not working
- Make sure native messaging host is set up (automatic during install)
- Check browser console for errors (F12)
- Reload the extension

### Downloads fail
- Verify `yt-dlp` and `aria2` are installed: `which yt-dlp aria2c`
- Check download folder permissions
- Update yt-dlp: `sudo pacman -S yt-dlp`

## Next Steps

1. Test downloading from different websites
2. Submit Firefox extension to Mozilla Add-ons
3. Star the project on GitHub: https://github.com/Dawaman43/FastTubeDownloader
4. Report any issues: https://github.com/Dawaman43/FastTubeDownloader/issues

Enjoy FastTube Downloader v2! 🚀
