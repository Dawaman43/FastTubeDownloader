#!/bin/bash
# FastTube Downloader v2.0 - CLEAN Installation Script
# This removes the old extension and does a fresh install

echo "================================================"
echo "  FastTube Downloader v2.0"
echo "  CLEAN INSTALLATION"
echo "================================================"
echo ""

# Verify we're in the right directory
if [ ! -f "manifest.json" ]; then
    echo "❌ Error: manifest.json not found"
    exit 1
fi

echo "Step 1: Verify New Files"
echo "========================"

# Check if new files exist
NEW_FILES=("popup.css" "PLAYLIST_FOLDERS.md" "QUICKSTART.md")
ALL_PRESENT=true

for file in "${NEW_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ Found: $file"
    else
        echo "✗ Missing: $file"
        ALL_PRESENT=false
    fi
done

if [ "$ALL_PRESENT" = false ]; then
    echo ""
    echo "❌ Some new files are missing. Installation may not be complete."
    exit 1
fi

# Verify manifest version
VERSION=$(grep '"version"' manifest.json | head -1 | cut -d'"' -f4)
echo "✓ Manifest version: $VERSION"

if [ "$VERSION" != "2.0" ]; then
    echo "⚠ Warning: Expected version 2.0, found $VERSION"
fi

echo ""
echo "Step 2: Remove Old Extension from Chrome"
echo "========================================="
echo ""
echo "Please follow these steps CAREFULLY:"
echo ""
echo "1. Open Chrome and go to: chrome://extensions/"
echo "2. Find 'FastTube Downloader' in the list"
echo "3. Click the 'Remove' button (trash icon)"
echo "4. Confirm removal when prompted"
echo ""
echo "This ensures no old cached data remains."
echo ""

read -p "Press ENTER when you've removed the old extension..."

echo ""
echo "Step 3: Load New Extension"
echo "=========================="
echo ""
echo "Now install the NEW version:"
echo ""
echo "1. On chrome://extensions/ page"
echo "2. Make sure 'Developer mode' is ON (toggle top-right)"
echo "3. Click 'Load unpacked' button"
echo "4. Navigate to and select this folder:"
echo "   $(pwd)"
echo "5. Click 'Select Folder'"
echo ""

# Open Chrome extensions if available
if command -v chromium-browser &> /dev/null; then
    read -p "Open chrome://extensions/ now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        chromium-browser chrome://extensions/ &
        sleep 2
    fi
fi

read -p "Press ENTER when you've loaded the new extension..."

echo ""
echo "Step 4: Verify Installation"
echo "============================"
echo ""
echo "Check these things on chrome://extensions/:"
echo ""
echo "  ✓ Extension name: 'FastTube Downloader'"
echo "  ✓ Extension version: '2.0'"
echo "  ✓ Description includes: 'IDM-style interface'"
echo "  ✓ No errors shown"
echo ""

read -p "Does everything look correct? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "❌ Installation verification failed"
    echo ""
    echo "Troubleshooting:"
    echo "1. Make sure Developer mode is enabled"
    echo "2. Try closing and reopening Chrome"
    echo "3. Check for errors in the extension details"
    exit 1
fi

echo ""
echo "Step 5: Test the New UI"
echo "======================="
echo ""
echo "1. Click the FastTube extension icon in Chrome toolbar"
echo "2. You should see the NEW IDM-style popup with:"
echo "   - Blue gradient header"
echo "   - Three tabs: Active, History, Settings"
echo "   - Dark theme interface"
echo ""

read -p "Do you see the new IDM-style interface? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "❌ New UI not showing"
    echo ""
    echo "Try these steps:"
    echo "1. Hard refresh the extension:"
    echo "   - Go to chrome://extensions/"
    echo "   - Click the reload icon on FastTube"
    echo "2. Close ALL Chrome windows and reopen"
    echo "3. Check the service worker console for errors:"
    echo "   - Click 'service worker' link under the extension"
    exit 1
fi

echo ""
echo "================================================"
echo "  ✅ CLEAN INSTALLATION SUCCESSFUL!"
echo "================================================"
echo ""
echo "New Features Available:"
echo "  • IDM-style popup with tabs ✓"
echo "  • Real-time progress tracking"
echo "  • Download history"
echo "  • Settings panel"
echo "  • Playlist folder organization"
echo ""
echo "Next Steps:"
echo "  1. Test on a YouTube video"
echo "  2. Try downloading a playlist"
echo "  3. Check ~/Downloads/ for playlist folders"
echo ""
echo "Desktop App Status:"

if pgrep -f "python.*main_window.py" > /dev/null; then
    echo "  ✓ Desktop app is running"
else
    echo "  ⚠ Desktop app not running"
    echo "  Start it with: python3 gui/main_window.py &"
fi

echo ""
echo "📚 Documentation:"
echo "  • QUICKSTART.md - Getting started guide"
echo "  • PLAYLIST_FOLDERS.md - Playlist feature details"
echo ""
