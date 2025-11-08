#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
TMP_DIR="$ROOT_DIR/.tmp_ext_build"
mkdir -p "$DIST_DIR" "$TMP_DIR"

cd "$ROOT_DIR"

CHROME_FILES=(
  "manifest.json"
  "background.js"
  "content.js"
  "download_ui.js"
  "popup.html"
  "popup.js"
  "icon16.png"
  "icon48.png"
  "icon128.png"
)

for f in "${CHROME_FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing file: $f" >&2
    exit 1
  fi
done

rm -f "$DIST_DIR/fasttube_chrome.zip"
zip -q -r "$DIST_DIR/fasttube_chrome.zip" "${CHROME_FILES[@]}"
echo "Built: $DIST_DIR/fasttube_chrome.zip"

# Firefox: copy MV2 manifest to temp as manifest.json and zip the same assets
rm -rf "$TMP_DIR/firefox"
mkdir -p "$TMP_DIR/firefox"
cp -f manifest.firefox.json "$TMP_DIR/firefox/manifest.json"
cp -f background.js content.js download_ui.js popup.html popup.js "$TMP_DIR/firefox/"
cp -f icon16.png icon48.png icon128.png "$TMP_DIR/firefox/"

pushd "$TMP_DIR/firefox" >/dev/null
zip -q -r "$DIST_DIR/fasttube_firefox.zip" .
popd >/dev/null

echo "Built: $DIST_DIR/fasttube_firefox.zip"

echo "Done. Load these zips in your browser stores or as temporary add-ons (Firefox)." 
