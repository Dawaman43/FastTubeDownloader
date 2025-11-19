#!/bin/bash
# Force Chrome to reload ALL extension files (clear cache)

echo "🔄 Forcing Chrome Extension Cache Refresh"
echo "========================================="
echo ""

cd /home/dawitworku/Documents/FastTubeDownloader

echo "This will force Chrome to reload all extension files."
echo ""

# Create a timestamp file to force reload
TIMESTAMP=$(date +%s)
echo "// Cache buster: $TIMESTAMP" >> popup.js.tmp
mv popup.js.tmp popup.js.bak 2>/dev/null
cat popup.js > popup.js.tmp
echo "" >> popup.js.tmp
echo "// Last updated: $TIMESTAMP" >> popup.js.tmp
mv popup.js.tmp popup.js

echo "✓ Modified popup.js to force reload"
echo ""
echo "📋 Now do these steps IN ORDER:"
echo ""
echo "1. Go to: chrome://extensions/"
echo "2. Find 'FastTube Downloader'"
echo "3. Click the RELOAD button (🔄 circular arrow icon)"
echo "4. Close the extension popup if it's open"
echo "5. Click the extension icon again"
echo ""
echo "You MUST see:"
echo "  🔵 Blue gradient header (not white!)"
echo "  📑 Three tabs: Active | History | Settings"
echo "  🌙 Dark background (#1a1d23)"
echo ""

read -p "Press ENTER to open chrome://extensions/ ..."

if command -v chromium-browser &> /dev/null; then
    chromium-browser chrome://extensions/ &
    echo ""
    echo "✓ Opened Chrome extensions page"
elif command -v google-chrome &> /dev/null; then
    google-chrome chrome://extensions/ &
    echo ""
    echo "✓ Opened Chrome extensions page"
else
    echo "⚠ Please manually open: chrome://extensions/"
fi

echo ""
echo "After clicking RELOAD on the extension:"
echo "========================================"
echo ""
echo "RIGHT-CLICK on the extension icon → Inspect popup"
echo "This opens DevTools for the popup."
echo ""
echo "In the Console tab, you should see:"
echo "  • No red errors"
echo "  • Blue gradient background visible"
echo ""
echo "If you STILL see white background:"
echo "  1. In DevTools, right-click the reload button"
echo "  2. Select 'Empty Cache and Hard Reload'"
echo "  3. Close popup and reopen"
echo ""
