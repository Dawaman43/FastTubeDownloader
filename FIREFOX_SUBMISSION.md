# Firefox Add-on Submission Guide

This guide helps you submit FastTube Downloader v2.1.2 to Mozilla Add-ons (AMO).

## Quick Start

The Firefox extension package is ready: `dist/firefox/fasttube-downloader-firefox-2.1.2.xpi`

## Submission Steps

### 1. Create Developer Account
- Go to https://addons.mozilla.org/developers/
- Sign in with Firefox Account (or create one)
- Accept the Developer Agreement

### 2. Submit Extension
- Go to https://addons.mozilla.org/developers/addon/submit/distribution
- Choose "On this site" (for AMO listing)
- Upload `dist/firefox/fasttube-downloader-firefox-2.1.2.xpi`

### 3. Fill Extension Details

**Basic Information:**
- **Name**: FastTube Downloader
- **Summary**: Universal download manager with IDM-style features. Download videos, music, documents, and files from any website with multi-threaded acceleration.
- **Description**:
  ```
  FastTube Downloader is a powerful, IDM-style universal download manager for Firefox.
  
  KEY FEATURES:
  • Universal Support - Works on ALL websites (YouTube, Vimeo, Twitter, any file host)
  • All File Types - Videos, music, documents, archives, programs, images
  • Smart Organization - Auto-categorize downloads into Videos/, Music/, Documents/, etc.
  • Playlist Support - Organize playlist downloads into subfolders
  • Multi-threaded Downloads - Up to 32 parallel connections for maximum speed
  • Context Menus - Right-click any link to download
  • Background Downloads - Downloads continue even when browser closes
  • Native Integration - Connects to native app for high-performance downloads
  
  SUPPORTED SITES:
  • 1000+ video sites via yt-dlp (YouTube, Vimeo, Dailymotion, TikTok, etc.)
  • Any direct file download
  • Archive sites (ZIP, RAR, 7z files)
  • Document repositories (PDF, Office docs)
  • Software downloads (installers, AppImages)
  
  TECHNICAL HIGHLIGHTS:
  • Optional Rust download engine (3-5x faster)
  • aria2c integration for multi-connection downloads
  • System tray support
  • Speed limiting
  • Download history
  
  Open source on GitHub: https://github.com/Dawaman43/FastTubeDownloader
  ```

**Categories:**
- Download Management
- Web Development

**Tags:**
- download manager
- youtube downloader
- video downloader
- file downloader
- idm alternative
- multi-threaded downloads

**License**: MIT License

**Privacy Policy**: (Use the following)
  ```
  FastTube Downloader does not collect, store, or transmit any personal data.
  
  • No analytics or tracking
  • No data sent to third-party servers
  • Downloads are processed locally on your computer
  • URLs are sent only to the local native host application
  • No cookies or browsing history are accessed
  
  The extension only accesses:
  • Download events (to intercept downloads)
  • Active tab URL (when you click the extension button)
  • Web request headers (to detect file types)
  
  All processing happens locally. Your privacy is respected.
  ```

### 4. Add Screenshots

You should prepare 3-5 screenshots showing:
1. Extension popup with download controls
2. Context menu "Download with FastTube"
3. Downloads organized in folders
4. Main application window with download queue
5. System tray icon

**Screenshot size**: 1280x800 or 640x400 (PNG format)

### 5. Version Notes

For v2.1.2, use:
```
v2.1.2 - Universal Download Manager Release

NEW FEATURES:
• Universal site support - works on ALL websites
• Support for all file types (documents, archives, programs, etc.)
• Intelligent file organization (IDM-style categories)
• Playlist folder organization
• Context menus for quick downloads
• Rust-powered download engine (optional, 3-5x faster)
• System tray support for background downloads

IMPROVEMENTS:
• Migrated to Manifest V3
• Enhanced file type detection
• Better download interception
• Improved error handling
• Faster download speed

TECHNICAL:
• Multi-threaded downloads (up to 32 connections)
• Native messaging with local application
• Automatic file categorization
```

### 6. Expected Review Timeline

- **Automated Review**: ~15 minutes (if no manual review needed)
- **Manual Review**: 1-10 days (if flagged for manual review)

Mozilla will review for:
- Security issues
- Privacy concerns
- Code quality
- Permissions usage

### 7. After Approval

Once approved:
- Extension will be listed on https://addons.mozilla.org
- Users can install with one click
- Auto-updates will be handled by Mozilla
- You can submit updates anytime

## Tips for Faster Approval

1. **Clear Description**: Be explicit about what permissions are used for
2. **Good Screenshots**: Show the extension in action
3. **Privacy Policy**: Be transparent about data handling
4. **Source Code**: Link to GitHub repository
5. **Test Thoroughly**: Ensure no bugs before submission

## Updating the Extension

For future updates:
1. Increment version in `manifest.firefox.json`
2. Run `./package_firefox.sh`
3. Go to https://addons.mozilla.org/developers/addons
4. Click your extension → "Upload New Version"
5. Upload the new .xpi file

## Support

If the extension is rejected:
- Read the reviewer's feedback carefully
- Fix the issues mentioned
- Resubmit with explanation of changes
- Contact support if you disagree with the rejection
