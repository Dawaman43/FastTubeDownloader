#!/bin/bash
# FastTube Downloader v2.0 - Quick Installation Script

echo "================================================"
echo "  FastTube Downloader v2.0 Installation"
echo "  IDM-Style Interface + Playlist Folders"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "manifest.json" ]; then
    echo "❌ Error: manifest.json not found. Please run this script from the FastTubeDownloader directory."
    exit 1
fi

echo "✓ Found FastTubeDownloader directory"
echo ""

# Check for Chrome/Chromium
CHROME_INSTALLED=false
if command -v google-chrome &> /dev/null; then
    CHROME_INSTALLED=true
    CHROME_CMD="google-chrome"
elif command -v chromium &> /dev/null; then
    CHROME_INSTALLED=true
    CHROME_CMD="chromium"
elif command -v chromium-browser &> /dev/null; then
    CHROME_INSTALLED=true
    CHROME_CMD="chromium-browser"
fi

if [ "$CHROME_INSTALLED" = true ]; then
    echo "✓ Chrome/Chromium found: $CHROME_CMD"
else
    echo "⚠ Chrome/Chromium not found in PATH"
fi
echo ""

# Installation Steps
echo "📋 Installation Steps:"
echo ""
echo "STEP 1: Load Extension in Chrome"
echo "================================="
echo "1. Open Chrome and go to: chrome://extensions/"
echo "2. Enable 'Developer mode' (toggle in top-right)"
echo "3. Click 'Load unpacked'"
echo "4. Select this directory: $(pwd)"
echo ""
echo "OR if already installed:"
echo "1. Go to chrome://extensions/"
echo "2. Find 'FastTube Downloader'"
echo "3. Click the reload icon (🔄) to update"
echo ""

# Offer to open Chrome extensions page
if [ "$CHROME_INSTALLED" = true ]; then
    read -p "Would you like to open chrome://extensions/ now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Opening Chrome extensions page..."
        $CHROME_CMD chrome://extensions/ &
        sleep 2
    fi
fi

echo ""
echo "STEP 2: Verify Extension"
echo "========================"
echo "After loading/reloading the extension, verify:"
echo "  ✓ Extension version shows: 2.0"
echo "  ✓ Extension icon appears in Chrome toolbar"
echo "  ✓ No errors shown on chrome://extensions/"
echo ""

echo "STEP 3: Test the Extension"
echo "==========================  "
echo "1. Click the extension icon - you should see the new IDM-style popup"
echo "2. Go to any YouTube video or playlist"
echo "3. Click the red download button on the video"
echo "4. Test downloading a video from a playlist to verify folder organization"
echo ""

echo "STEP 4: Desktop App (Optional but Recommended)"
echo "==============================================="
echo "The desktop app should already be installed if you used setup.sh before."
echo "If not, run: ./setup.sh"
echo ""

# Check if desktop app is running
if pgrep -f "python.*main_window.py" > /dev/null; then
    echo "✓ Desktop app is already running"
else
    echo "⚠ Desktop app is not running"
    echo ""
    read -p "Would you like to start the desktop app now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "gui/main_window.py" ]; then
            echo "Starting desktop app..."
            python3 gui/main_window.py &
            echo "✓ Desktop app started"
        elif command -v fasttube-downloader &> /dev/null; then
            echo "Starting desktop app..."
            fasttube-downloader &
            echo "✓ Desktop app started"
        else
            echo "❌ Could not find desktop app. Run ./setup.sh first."
        fi
    fi
fi

echo ""
echo "================================================"
echo "  🎉 Installation Complete!"
echo "================================================"
echo ""
echo "📚 New Features in v2.0:"
echo "  • IDM-style popup interface with tabs"
echo "  • Real-time progress tracking"
echo "  • Download history with search"
echo "  • Comprehensive settings panel"
echo "  • Desktop notifications"
echo "  • Playlist folder organization ⭐ NEW!"
echo ""
echo "📖 Documentation:"
echo "  • Quick Start: QUICKSTART.md"
echo "  • Playlist Folders: PLAYLIST_FOLDERS.md"
echo "  • Full Walkthrough: Check artifacts"
echo ""
echo "🧪 Test Playlist Folders:"
echo "  1. Go to any YouTube playlist"
echo "  2. Add it with the extension"
echo "  3. Videos will be saved in: ~/Downloads/[Playlist Name]/"
echo ""
echo "💡 Tip: If you see any issues, check the service worker console:"
echo "   chrome://extensions/ → FastTube Downloader → 'service worker'"
echo ""
