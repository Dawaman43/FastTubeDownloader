#!/usr/bin/env bash
# FastTube Downloader easy installer
# Detects distro, downloads latest prebuilt package (.deb/.rpm) if available,
# installs dependencies, falls back to local install if no package asset is found.

set -euo pipefail
REPO="Dawaman43/FastTubeDownloader"
API="https://api.github.com/repos/${REPO}/releases/latest"
TMP_DIR="/tmp/fasttube-install"
mkdir -p "$TMP_DIR"
ARCH=$(uname -m)
if [[ "$ARCH" == "x86_64" || "$ARCH" == "amd64" ]]; then ARCH_LABEL="amd64"; else ARCH_LABEL="$ARCH"; fi

have_cmd(){ command -v "$1" >/dev/null 2>&1; }

log(){ echo -e "\e[1;32m[fasttube]\e[0m $*"; }
warn(){ echo -e "\e[1;33m[fasttube warn]\e[0m $*"; }
err(){ echo -e "\e[1;31m[fasttube error]\e[0m $*" >&2; }

fetch_asset_url(){ # pattern
  local pattern="$1"
  curl -s "$API" | grep 'browser_download_url' | grep -E "$pattern" | head -n1 | cut -d '"' -f4 || true
}

install_deps(){
  log "Installing runtime dependencies (python/gtk, yt-dlp, aria2)..."
  if have_cmd apt-get; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-gi gir1.2-gtk-3.0 yt-dlp aria2
  elif have_cmd dnf; then
    sudo dnf install -y python3 python3-gobject gtk3 yt-dlp aria2 || true
  elif have_cmd zypper; then
    sudo zypper --non-interactive in python3 python3-gobject gtk3 yt-dlp aria2 || true
  elif have_cmd pacman; then
    sudo pacman -Sy --needed --noconfirm python gtk3 python-gobject yt-dlp aria2 || true
  else
    warn "Unknown package manager. Please install: python3-gi GTK3 yt-dlp aria2 manually."
  fi
}

install_deb(){
  local url="$1"
  local file="$TMP_DIR/fasttube.deb"
  log "Downloading .deb: $url"
  curl -L "$url" -o "$file"
  log "Installing .deb..."
  sudo apt install -y "./$file"
}

install_rpm(){
  local url="$1"
  local file="$TMP_DIR/fasttube.rpm"
  log "Downloading .rpm: $url"
  curl -L "$url" -o "$file"
  log "Installing .rpm..."
  if have_cmd dnf; then sudo dnf install -y "$file"; elif have_cmd rpm; then sudo rpm -i "$file"; else err "No RPM installer found"; fi
}

local_install(){
  log "Falling back to local install (rsync into /opt)"
  if [[ ! -f setup.sh ]]; then err "Run from project root (setup.sh missing)."; exit 1; fi
  sudo bash setup.sh
}

show_post(){
  cat <<EOF

FastTube Downloader installed.
Launch app: fasttube-downloader
Load browser extension (Chrome): chrome://extensions > Developer Mode > Load unpacked > project root
Permanent ID: run python3 tools/generate_extension_key.py before loading extension
EOF
}

log "Detecting distribution..."
. /etc/os-release 2>/dev/null || true
ID_LIKE_LOWER=$(echo "${ID_LIKE:-}" | tr 'A-Z' 'a-z')
ID_LOWER=$(echo "${ID:-}" | tr 'A-Z' 'a-z')

install_deps

ASSET_DEB=$(fetch_asset_url ".deb$")
ASSET_RPM=$(fetch_asset_url ".rpm$")

if [[ "$ID_LOWER" =~ (debian|ubuntu|linuxmint) || "$ID_LIKE_LOWER" =~ (debian|ubuntu) ]]; then
  if [[ -n "$ASSET_DEB" ]]; then
    install_deb "$ASSET_DEB"
  else
    warn "No .deb asset found in latest release; performing local install."
    local_install
  fi
elif [[ "$ID_LOWER" =~ (fedora|rhel|centos|rocky|almalinux|opensuse) || "$ID_LIKE_LOWER" =~ (fedora|rhel|suse) ]]; then
  if [[ -n "$ASSET_RPM" ]]; then
    install_rpm "$ASSET_RPM"
  else
    warn "No .rpm asset found in latest release; performing local install."
    local_install
  fi
else
  warn "Unsupported / unknown distro family ($ID_LOWER). Doing local install."
  local_install
fi

show_post
