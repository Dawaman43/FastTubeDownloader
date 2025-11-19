# 🔧 Extension Showing Old Interface - Quick Fix

## Problem
Extension is loaded but showing the OLD white interface instead of the NEW blue IDM-style interface.

## Cause
Chrome has **cached** the old popup files. Even after reloading, Chrome sometimes keeps old HTML/CSS/JS in memory.

## ✅ SOLUTION (Do ALL steps):

### Method 1: Hard Reload (Try This First)

1. **Go to**: `chrome://extensions/`

2. **Find FastTube Downloader** in the list

3. **Click the RELOAD button** (🔄 circular arrow icon)

4. **Close Chrome COMPLETELY**:
   - Close ALL Chrome windows
   - Make sure no Chrome processes are running

5. **Reopen Chrome** and test the extension

6. **Click extension icon** → Should now see:
   - 🔵 **Blue gradient header**
   - 📑 **Three tabs**: Active | History | Settings
   - 🌙 **Dark theme background**

### Method 2: Manual Cache Clear (If Method 1 Doesn't Work)

1. **Click extension icon** (even if it shows old interface)

2. **Right-click anywhere in the popup** → **Inspect**
   - This opens DevTools attached to the popup

3. **In DevTools**:
   - Click the **Network** tab
   - Check **"Disable cache"** checkbox (top of Network tab)
   - Right-click the reload button → **"Empty Cache and Hard Reload"**

4. **Close the popup**

5. **Reload extension** at `chrome://extensions/`

6. **Click extension icon again** → Should show new interface

### Method 3: Nuclear Option (Guaranteed to Work)

1. Go to `chrome://extensions/`

2. **REMOVE** FastTube Downloader completely

3. **Close Chrome entirely**

4. **Delete Chrome's extension cache**:
   ```bash
   rm -rf ~/.cache/chromium/Default/Extensions/*
   # OR if using Google Chrome:
   rm -rf ~/.cache/google-chrome/Default/Extensions/*
   ```

5. **Reopen Chrome**

6. Go to `chrome://extensions/`

7. Enable **Developer mode**

8. Click **Load unpacked**

9. Select: `/home/dawitworku/Documents/FastTubeDownloader`

10. **Test**: Click extension icon → NEW blue interface!

## Visual Comparison

### ❌ OLD (What You're Seeing Now)
```
╔═══════════════════════════════╗
║ FastTube Downloader           ║  ← White background
║                               ║
║ Downloads                     ║  ← Simple text
║                               ║
║ (list of downloads)           ║
╚═══════════════════════════════╝
```

### ✅ NEW (What You Should See)
```
╔═══════════════════════════════╗
║ 🔵 FastTube Downloader   ⟳ ⚙ ║  ← Blue gradient header
╠═══════════════════════════════╣
║ Active(0)|History|Settings    ║  ← Three tabs
╠═══════════════════════════════╣
║                               ║
║        📥                     ║  ← Dark background
║   No active downloads         ║
║                               ║
╚═══════════════════════════════╝
```

## Quick Test Commands

Run this to verify files are correct:
```bash
cd /home/dawitworku/Documents/FastTubeDownloader
./debug_extension.sh
```

Run this to force reload:
```bash
cd /home/dawitworku/Documents/FastTubeDownloader
./force_reload.sh
```

## Still Not Working?

If you STILL see the old interface after all methods:

1. **Check if you have MULTIPLE Chrome profiles**:
   - You might be installing in one profile but using another
   - Check `chrome://version/` for "Profile Path"

2. **Check if it's a different browser**:
   - Chromium vs Google Chrome are separate
   - Make sure you're using the same browser

3. **Verify manifest version**:
   ```bash
   grep version /home/dawitworku/Documents/FastTubeDownloader/manifest.json
   ```
   Should show: `"version": "2.0"`

4. **Check extension details** on chrome://extensions/:
   - Expand the FastTube entry
   - Version MUST show **2.0**
   - If it shows 1.0, the wrong folder is loaded

## Emergency Recovery

If nothing works, completely uninstall and reinstall:

```bash
cd /home/dawitworku/Documents/FastTubeDownloader

# Remove extension from Chrome first
# Then run:
./clean_install.sh
```
