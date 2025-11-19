# FastTube Downloader v2.0 - Quick Start Guide

## 🚀 Installation & Testing

### 1. Load the Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Navigate to and select: `/home/dawitworku/Documents/FastTubeDownloader`
5. The extension should now appear in your extensions list

### 2. Verify Extension ID Stability

The extension uses a hardcoded key in `manifest.json` to maintain a stable ID across reloads. The current ID should be:
```
Extension ID: ocdnlcnfhdlefgbkfbbooegjdfpkgedf
```

> **Important**: This ID must match the ID configured in the native messaging host file at:
> `~/.config/google-chrome/NativeMessagingHosts/com.fasttube.downloader.json`

### 3. Test the New Interface

#### Quick Visual Check
1. Click the FastTube extension icon in Chrome toolbar
2. You should see the new IDM-style popup with:
   - Blue gradient header
   - Three tabs: Active, History, Settings
   - Modern dark theme

#### Test Active Downloads
1. Go to any YouTube video (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
2. Click the red download button overlay on the video player
3. Select format and quality
4. Click **Download**
5. Open extension popup
6. Verify you see:
   - Download title
   - Progress bar animating
   - Download speed (if native app running)
   - ETA calculation
   - Pause/Cancel buttons

#### Test Settings
1. Click Settings tab
2. Toggle various settings (notifications, auto-start, etc.)
3. Change max simultaneous downloads
4. Close popup and reopen
5. Verify settings persisted

#### Test History
1. Complete a download
2. Go to History tab
3. Verify the download appears
4. Try searching for it
5. Test Clear History button

### 4. Verify Extension Persistence

The extension now includes keep-alive mechanisms. To verify:

1. Check Chrome DevTools console for the service worker:
   - Go to `chrome://extensions/`
   - Find FastTube Downloader
   - Click "service worker" link under "Inspect views"
   - You should see periodic "Keep-alive ping" messages every minute

2. Leave browser open for several hours
3. Verify extension remains active (not disabled)

### 5. Test with Desktop App

If you have the native desktop application:

1. Start the desktop app
2. Queue a download from the extension
3. Watch progress update in real-time
4. Verify notifications appear when download completes

If desktop app is NOT running:
- You should see a native host error message in the popup
- The extension will attempt to auto-reconnect when app starts

---

## 🎨 What's New - Visual Tour

### IDM-Style Design Elements

**Color Scheme**:
- Primary Blue: `#0d6efd` (matches IDM)
- Success Green: `#28a745`
- Warning Yellow: `#ffc107`
- Danger Red: `#dc3545`
- Dark Background: `#1a1d23`

**Animation Features**:
- Smooth tab transitions
- Progress bar shimmer effect
- Hover state animations
- Fade-in for new downloads

**Typography**:
- System font stack for native look
- Proper hierarchy with font weights
- Letter spacing for readability

---

## 🔍 Troubleshooting

### Extension Not Loading
- Check Developer mode is enabled
- Verify no syntax errors in console
- Try removing and re-adding the extension

### Progress Not Showing
- Ensure desktop app is running
- Check service worker console for errors
- Verify native messaging host is configured

### Settings Not Saving
- Check browser console for storage errors
- Verify `chrome.storage` permissions in manifest
- Try clearing extension data and reloading

### Extension Getting Disabled
- This should no longer happen with v2.0
- Check for alarm creation in service worker console
- Look for "Keep-alive ping" messages

---

## 📦 Files Changed in v2.0

### New Files
- `popup.css` - Complete IDM-style stylesheet

### Modified Files
- `manifest.json` - v2.0, added alarms & notifications permissions
- `popup.html` - Complete redesign with tabs
- `popup.js` - Full rewrite with 500+ lines
- `background.js` - Keep-alive, persistence, notifications

---

## 🎯 Testing Checklist

- [ ] Extension loads without errors
- [ ] IDM-style popup appears
- [ ] Can start downloads from YouTube
- [ ] Progress updates in real-time
- [ ] Can pause/resume downloads
- [ ] Download history works
- [ ] Settings persist across sessions
- [ ] Notifications appear (if enabled)
- [ ] Extension badge shows download count
- [ ] Extension stays enabled over multiple days
- [ ] Native error shown when app not running
- [ ] Auto-reconnect works when app restarts

---

## 💡 Development Tips

### Reload Extension After Changes
After making code changes:
```bash
# In chrome://extensions/, click the reload icon for FastTube
# Or use keyboard shortcut while on extensions page
```

### View Service Worker Console
```
chrome://extensions/ → FastTube Downloader → "service worker" link
```

### View Popup Console
```
Right-click extension icon → Inspect popup
```

### Check Storage
```javascript
// In any extension console:
chrome.storage.local.get(null, console.log);
chrome.storage.sync.get(null, console.log);
```

### Monitor Alarms
```javascript
// In service worker console:
chrome.alarms.getAll(console.log);
```

---

## 🌟 Next Steps

The extension is now feature-complete for v2.0. Optional future enhancements could include:

1. **Bandwidth Limiter** - Control download speed
2. **Download Scheduler** - Schedule downloads for specific times
3. **Cloud Sync** - Sync history across devices
4. **Playlist Categorization** - Auto-organize by playlist
5. **Video Preview** - Thumbnail preview in download card

Happy downloading! 🎉
