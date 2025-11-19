#!/bin/bash
# Debug Extension Loading

echo "🔍 FastTube Downloader v2.0 - Debug Check"
echo "=========================================="
echo ""

cd /home/dawitworku/Documents/FastTubeDownloader

echo "1. Checking Required Files:"
echo "--------------------------"
REQUIRED_FILES=(
    "manifest.json"
    "popup.html"
    "popup.js"
    "popup.css"
    "background.js"
    "content.js"
    "icon16.png"
    "icon48.png"
    "icon128.png"
)

ALL_GOOD=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        SIZE=$(ls -lh "$file" | awk '{print $5}')
        echo "  ✓ $file ($SIZE)"
    else
        echo "  ✗ MISSING: $file"
        ALL_GOOD=false
    fi
done

echo ""
echo "2. Checking manifest.json:"
echo "-------------------------"
if python3 -m json.tool manifest.json > /dev/null 2>&1; then
    echo "  ✓ JSON syntax is valid"
    VERSION=$(grep '"version"' manifest.json | cut -d'"' -f4)
    NAME=$(grep '"name"' manifest.json | cut -d'"' -f4)
    DESC=$(grep '"description"' manifest.json | cut -d'"' -f4)
    echo "  ✓ Name: $NAME"
    echo "  ✓ Version: $VERSION"
    echo "  ✓ Description: $DESC"
else
    echo "  ✗ JSON syntax error!"
    ALL_GOOD=false
fi

echo ""
echo "3. Checking popup.html:"
echo "----------------------"
if grep -q "popup.css" popup.html; then
    echo "  ✓ Links to popup.css"
else
    echo "  ✗ Missing popup.css link"
    ALL_GOOD=false
fi

if grep -q "popup.js" popup.html; then
    echo "  ✓ Links to popup.js"
else
    echo "  ✗ Missing popup.js link"
    ALL_GOOD=false
fi

if grep -q "IDM" popup.html || grep -q "Active" popup.html; then
    echo "  ✓ Contains new v2.0 content"
else
    echo "  ⚠ Might be old version"
fi

echo ""
echo "4. Checking popup.css:"
echo "---------------------"
if grep -q "#0d6efd" popup.css; then
    echo "  ✓ Contains IDM blue color (#0d6efd)"
else
    echo "  ⚠ Missing IDM styling"
fi

if grep -q "\.tabs" popup.css; then
    echo "  ✓ Contains tab styling"
else
    echo "  ⚠ Missing tab styling"
fi

echo ""
echo "5. Checking popup.js:"
echo "--------------------"
if grep -q "tabSwitching" popup.js || grep -q "switchTab" popup.js; then
    echo "  ✓ Contains tab switching logic"
else
    echo "  ⚠ Missing tab logic"
fi

if grep -q "downloadHistory" popup.js || grep -q "history" popup.js; then
    echo "  ✓ Contains history functionality"
else
    echo "  ⚠ Missing history functionality"
fi

echo ""
echo "=========================================="
if [ "$ALL_GOOD" = true ]; then
    echo "✅ All checks passed!"
    echo ""
    echo "Extension should load correctly."
    echo ""
    echo "📋 Installation Instructions:"
    echo "1. Go to: chrome://extensions/"
    echo "2. Enable 'Developer mode' (top-right toggle)"
    echo "3. If FastTube is already there, click REMOVE first"
    echo "4. Click 'Load unpacked'"
    echo "5. Select: $(pwd)"
    echo ""
    echo "After loading, you should see:"
    echo "  • Name: FastTube Downloader"
    echo "  • Version: 2.0"
    echo "  • Description: Download YouTube videos fast with IDM-style interface"
    echo ""
    echo "Click the extension icon and you should see:"
    echo "  • Blue gradient header"
    echo "  • Three tabs: Active, History, Settings"
    echo "  • Dark theme"
else
    echo "❌ Some checks failed!"
    echo ""
    echo "Please review the errors above."
fi
echo ""

# Offer to open the directory in file manager
read -p "Open this directory in file manager? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    xdg-open . &
fi
