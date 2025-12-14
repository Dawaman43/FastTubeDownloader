#!/bin/bash

set -e  

INSTALL_DIR="/opt/FastTubeDownloader"
BIN_LINK="/usr/bin/fasttube-downloader"
DESKTOP_GLOBAL="/usr/share/applications/fasttube-downloader.desktop"
TARGET_USER="${SUDO_USER:-$USER}"
TARGET_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6 2>/dev/null || echo "$HOME")
CONFIG_DIR="$TARGET_HOME/.config/FastTubeDownloader"
NATIVE_CHROME="$TARGET_HOME/.config/google-chrome/NativeMessagingHosts/com.fasttube.downloader.json"
NATIVE_CHROMIUM="$TARGET_HOME/.config/chromium/NativeMessagingHosts/com.fasttube.downloader.json"
NATIVE_FIREFOX="$TARGET_HOME/.mozilla/native-messaging-hosts/com.fasttube.downloader.json"
EXTENSION_PATH="$PWD"  
if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
  AS_USER=(sudo -u "$SUDO_USER")
else
  AS_USER=()
fi

echo "Checking/installing dependencies..."
PKG_OK=0
if command -v apt-get >/dev/null 2>&1; then
  if apt-cache show libgirepository-2.0-dev >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-appindicator3-0.1 gir1.2-notify-0.7 libgirepository-2.0-dev yt-dlp aria2 jq || PKG_OK=1
  else
    sudo apt-get update && sudo apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-appindicator3-0.1 gir1.2-notify-0.7 libgirepository1.0-dev yt-dlp aria2 jq || PKG_OK=1
  fi
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y python3-gobject gtk3 libappindicator-gtk3 yt-dlp aria2 jq || PKG_OK=1
elif command -v pacman >/dev/null 2>&1; then
  sudo pacman -Sy --needed --noconfirm python-gobject gtk3 libappindicator-gtk3 yt-dlp aria2 jq || PKG_OK=1
elif command -v zypper >/dev/null 2>&1; then
  sudo zypper --non-interactive in python3-gobject gtk3 yt-dlp aria2 jq || PKG_OK=1
else
  echo "Warning: Unknown package manager. Please ensure dependencies are installed: python gobject/GTK3 bindings, yt-dlp, aria2, jq." >&2
fi
if [ "$PKG_OK" -ne 0 ]; then
  echo "Note: some dependencies may have failed to install. If the app doesn't start, install manually for your distro." >&2
fi

echo "Installing to $INSTALL_DIR..."
sudo mkdir -p "$INSTALL_DIR"
sudo rsync -av --exclude='setup.sh' --exclude='README.md' . "$INSTALL_DIR/"

# Optional: Build Rust download engine
if [ "$BUILD_RUST" = "1" ] || [ "$1" = "--with-rust" ]; then
  echo "Building Rust download engine..."
  if command -v cargo >/dev/null 2>&1; then
    cd "$INSTALL_DIR/rust_downloader"
    cargo build --release 2>/dev/null || echo "Rust build failed, will use aria2c fallback"
    SO_FILE=$(find target/release -name "fasttube_downloader*.so" -o -name "libfasttube_downloader*.so" 2>/dev/null | head -1)
    if [ -n "$SO_FILE" ]; then
      cp "$SO_FILE" "$INSTALL_DIR/gui/fasttube_downloader.so"
      echo "✅ Rust engine installed"
    fi
    cd -
  else
    echo "⚠️  Rust not installed. Skipping Rust engine (will use aria2c fallback)"
    echo "   To install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
  fi
fi

for hostdir in "$TARGET_HOME/.config/google-chrome/NativeMessagingHosts" "$TARGET_HOME/.config/chromium/NativeMessagingHosts"; do
  if [ -f "$hostdir/com.fasttube.downloader.json" ]; then
    if grep -q 'fast_ytdl.sh' "$hostdir/com.fasttube.downloader.json"; then
      echo "Cleaning stale native host at $hostdir/com.fasttube.downloader.json"
      rm -f "$hostdir/com.fasttube.downloader.json"
    fi
  fi
done
sudo chmod +x "$INSTALL_DIR/fast_ytdl.sh"
sudo chmod +x "$INSTALL_DIR/native_host/bridge.py"
sudo find "$INSTALL_DIR/gui" -name "*.py" -exec chmod +x {} \;

sudo mkdir -p "$INSTALL_DIR/icons"
if [ -f "$INSTALL_DIR/icon128.png" ]; then sudo cp -f "$INSTALL_DIR/icon128.png" "$INSTALL_DIR/icons/"; fi
if [ -f "$INSTALL_DIR/icon48.png" ]; then sudo cp -f "$INSTALL_DIR/icon48.png" "$INSTALL_DIR/icons/"; fi
if [ -f "$INSTALL_DIR/icon16.png" ]; then sudo cp -f "$INSTALL_DIR/icon16.png" "$INSTALL_DIR/icons/"; fi

"${AS_USER[@]}" mkdir -p "$CONFIG_DIR"

"${AS_USER[@]}" mkdir -p "$(dirname "$NATIVE_CHROME")"
# Ensure a stable extension ID: if manifest.json has no 'key', generate one
MANIFEST_JSON="$INSTALL_DIR/manifest.json"
if [ -f "$MANIFEST_JSON" ]; then
  if ! grep -q '"key"' "$MANIFEST_JSON"; then
    echo "Generating extension key for stable ID..."
    if command -v python3 >/dev/null 2>&1; then
      ( cd "$INSTALL_DIR" && python3 tools/generate_extension_key.py ) || true
    fi
  fi
fi
EXT_ID_INPUT=${EXT_ID:-}
if [ -z "$EXT_ID_INPUT" ]; then
  if [ -f "$MANIFEST_JSON" ]; then
    EXT_ID_INPUT=$(python3 - "$MANIFEST_JSON" <<'PY'
import sys, json, base64, hashlib
mf = sys.argv[1]
try:
    with open(mf, 'r') as f:
        m = json.load(f)
    key_b64 = m.get('key')
    if isinstance(key_b64, str) and key_b64.strip():
        der = base64.b64decode(key_b64)
        d = hashlib.sha256(der).digest()[:16]
        alphabet = 'abcdefghijklmnop'
        ext_id = ''.join(alphabet[b>>4] + alphabet[b & 0xF] for b in d)
        print(ext_id, end='')
except Exception:
    pass
PY
    )
  fi
fi
if [ -z "$EXT_ID_INPUT" ]; then
  echo "Enter your extension ID (from chrome://extensions after loading unpacked):"
  read -r EXT_ID_INPUT
fi
if [ -z "$EXT_ID_INPUT" ]; then
  echo "No extension ID provided. You can also set EXT_ID env var when running setup.sh." >&2
  EXT_ID_INPUT="gifdkhjpnkiaekcagnehmolkpndfohke"
fi

"${AS_USER[@]}" bash -c "cat > '$NATIVE_CHROME'" << EOJSON
{
  "name": "com.fasttube.downloader",
  "description": "Native host for FastTube Downloader",
  "path": "$INSTALL_DIR/native_host/bridge.py",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://$EXT_ID_INPUT/"]
}
EOJSON

"${AS_USER[@]}" mkdir -p "$(dirname "$NATIVE_CHROMIUM")"
"${AS_USER[@]}" bash -c "cat > '$NATIVE_CHROMIUM'" << EOJSON
{
  "name": "com.fasttube.downloader",
  "description": "Native host for FastTube Downloader",
  "path": "$INSTALL_DIR/native_host/bridge.py",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://$EXT_ID_INPUT/"]
}
EOJSON

"${AS_USER[@]}" mkdir -p "$(dirname "$NATIVE_FIREFOX")"
"${AS_USER[@]}" bash -c "cat > '$NATIVE_FIREFOX'" << EOJSON
{
  "name": "com.fasttube.downloader",
  "description": "Native host for FastTube Downloader",
  "path": "$INSTALL_DIR/native_host/bridge.py",
  "type": "stdio",
  "allowed_extensions": ["fasttube@local"]
}
EOJSON

echo "Installing launcher to $BIN_LINK..."
sudo tee "$BIN_LINK" >/dev/null <<'EOSH'
#!/bin/sh
LOGDIR="${XDG_CACHE_HOME:-$HOME/.cache}"
mkdir -p "$LOGDIR" 2>/dev/null || true
# Try python3, then python (for distros where it's named python)
exec python3 /opt/FastTubeDownloader/gui/main_window.py "$@" 2>>"$LOGDIR/fasttube-downloader.log" || \
exec python /opt/FastTubeDownloader/gui/main_window.py "$@" 2>>"$LOGDIR/fasttube-downloader.log"
EOSH
sudo chmod +x "$BIN_LINK"

echo "Installing icons..."
if [ -f "$INSTALL_DIR/icons/icon16.png" ]; then
  sudo install -D -m 0644 "$INSTALL_DIR/icons/icon16.png" \
    "/usr/share/icons/hicolor/16x16/apps/fasttube-downloader.png"
fi
if [ -f "$INSTALL_DIR/icons/icon48.png" ]; then
  sudo install -D -m 0644 "$INSTALL_DIR/icons/icon48.png" \
    "/usr/share/icons/hicolor/48x48/apps/fasttube-downloader.png"
fi
if [ -f "$INSTALL_DIR/icons/icon128.png" ]; then
  sudo install -D -m 0644 "$INSTALL_DIR/icons/icon128.png" \
    "/usr/share/icons/hicolor/128x128/apps/fasttube-downloader.png"
fi
sudo gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true

echo "Installing desktop entry to $DESKTOP_GLOBAL..."
sudo bash -c "cat > '$DESKTOP_GLOBAL'" << 'EOENTRY'
[Desktop Entry]
Name=FastTube Downloader
GenericName=YouTube Video Downloader
Comment=Queue and download YouTube videos quickly with yt-dlp + aria2
Exec=/usr/bin/fasttube-downloader
Icon=fasttube-downloader
Terminal=false
Type=Application
Categories=AudioVideo;Network;Utility;
StartupWMClass=FastTube Downloader
Keywords=youtube;download;video;yt-dlp;aria2;
EOENTRY
sudo update-desktop-database /usr/share/applications 2>/dev/null || true

echo "Installation complete!"
echo "• Launch GUI: Search 'FastTube Downloader' in your app menu, or run: fasttube-downloader"
echo "• Browser Extension: Go to chrome://extensions/ > Enable 'Developer mode' > 'Load unpacked' > select $EXTENSION_PATH"
echo "  To keep a permanent extension ID, see EXTENSION_ID_GUIDE.md and set the 'key' in manifest.json before loading."
echo "• First Launch: The setup wizard will run—pick your download folder, etc."
echo "• Test: Try a YouTube URL in the GUI, or visit a video page and click the red download button."
echo "• Uninstall (if needed): sudo rm -rf $INSTALL_DIR && sudo rm -f $BIN_LINK $DESKTOP_GLOBAL && rm -f $NATIVE_CHROME $NATIVE_CHROMIUM && sudo xdg-icon-resource uninstall --size 128 fasttube-downloader 2>/dev/null || true"

echo "Note: If you previously ran this script with 'sudo ./setup.sh', your per-user files may have been created in /root. This version ensures files go to $TARGET_HOME."
