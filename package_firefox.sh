#!/bin/bash
# Package Firefox extension for Mozilla Add-ons submission

set -e

VERSION="2.1.2"
OUTPUT_DIR="dist/firefox"
EXTENSION_NAME="fasttube-downloader-firefox-${VERSION}"

echo "Packaging Firefox Extension v${VERSION}..."

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Copy Firefox-specific files
cp manifest.firefox.json "$TEMP_DIR/manifest.json"
cp background.js "$TEMP_DIR/"
cp content.js "$TEMP_DIR/"
cp popup.html "$TEMP_DIR/"
cp popup.js "$TEMP_DIR/"
cp popup.css "$TEMP_DIR/"
cp download_ui.js "$TEMP_DIR/"
cp icon16.png "$TEMP_DIR/"
cp icon48.png "$TEMP_DIR/"
cp icon128.png "$TEMP_DIR/"

# Create ZIP archive (Firefox uses .xpi but it's just a ZIP)
cd "$TEMP_DIR"
zip -r "${EXTENSION_NAME}.xpi" ./*

# Move to output directory
mv "${EXTENSION_NAME}.xpi" "${PWD}/../../${OUTPUT_DIR}/"

echo ""
cd - > /dev/null

echo "✅ Firefox extension packaged successfully!"
echo "Output: ${OUTPUT_DIR}/${EXTENSION_NAME}.xpi"
echo ""
echo "📋 Next steps for Firefox Add-ons submission:"
echo "1. Go to https://addons.mozilla.org/developers/addon/submit/distribution"
echo "2. Upload: ${OUTPUT_DIR}/${EXTENSION_NAME}.xpi"
echo "3. Fill in the metadata (description, screenshots, etc.)"
echo "4. Submit for review"
