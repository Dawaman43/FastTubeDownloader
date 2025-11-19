#!/bin/bash
set -e

VERSION=$(cat version.txt)
echo "Building FastTube Downloader v$VERSION..."

# Clean dist
rm -rf dist
mkdir -p dist

# --- Source Tarball ---
echo "Creating source tarball..."
TAR_NAME="fasttube-downloader-$VERSION.tar.gz"
# Create temp dir for correct structure
TMP_DIR="dist/fasttube-downloader-$VERSION"
mkdir -p "$TMP_DIR"
rsync -a --exclude='.git' --exclude='dist' --exclude='__pycache__' --exclude='.venv' . "$TMP_DIR/"
tar -C dist -czf "dist/$TAR_NAME" "fasttube-downloader-$VERSION"
rm -rf "$TMP_DIR"

# --- RPM ---
if command -v rpmbuild >/dev/null 2>&1; then
    echo "Building RPM..."
    mkdir -p dist/rpm_build/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
    cp "dist/$TAR_NAME" dist/rpm_build/SOURCES/
    cp packaging/rpm/fasttube-downloader.spec dist/rpm_build/SPECS/
    
    # Update version in spec if needed (it should match version.txt)
    # We assume spec is already updated.
    
    rpmbuild --define "_topdir $(pwd)/dist/rpm_build" -bb dist/rpm_build/SPECS/fasttube-downloader.spec
    
    mkdir -p dist/rpm
    cp dist/rpm_build/RPMS/*/*.rpm dist/rpm/
    echo "RPM created in dist/rpm/"
else
    echo "rpmbuild not found, skipping RPM build."
fi

# --- DEB ---
echo "Preparing DEB package structure..."
DEB_DIR="dist/deb/fasttube-downloader_${VERSION}-1_all"
mkdir -p "$DEB_DIR/opt/FastTubeDownloader"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/16x16/apps"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/48x48/apps"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$DEB_DIR/DEBIAN"

# Copy files
rsync -a --exclude='.git' --exclude='dist' --exclude='__pycache__' --exclude='packaging' . "$DEB_DIR/opt/FastTubeDownloader/"
cp packaging/launch-wrapper.sh "$DEB_DIR/usr/bin/fasttube-downloader"
chmod 755 "$DEB_DIR/usr/bin/fasttube-downloader"
cp packaging/fasttube-downloader.desktop "$DEB_DIR/usr/share/applications/"
cp icon16.png "$DEB_DIR/usr/share/icons/hicolor/16x16/apps/fasttube-downloader.png"
cp icon48.png "$DEB_DIR/usr/share/icons/hicolor/48x48/apps/fasttube-downloader.png"
cp icon128.png "$DEB_DIR/usr/share/icons/hicolor/128x128/apps/fasttube-downloader.png"

# Create control file
cat > "$DEB_DIR/DEBIAN/control" <<EOF
Package: fasttube-downloader
Version: $VERSION
Architecture: all
Maintainer: FastTube Downloader <maintainer@example.com>
Depends: python3, python3-gi, yt-dlp, aria2
Section: utils
Priority: optional
Description: FastTube Downloader – YouTube & generic file downloader
 Fast GTK desktop + browser extension integrated downloader using yt-dlp and aria2.
EOF

# Build DEB if dpkg-deb exists
if command -v dpkg-deb >/dev/null 2>&1; then
    dpkg-deb --build "$DEB_DIR"
    echo "DEB created: ${DEB_DIR}.deb"
else
    echo "dpkg-deb not found. DEB directory structure created at $DEB_DIR"
    echo "You can build it on a Debian/Ubuntu system using: dpkg-deb --build $DEB_DIR"
fi

# --- Arch ---
echo "Preparing Arch package..."
mkdir -p dist/arch
cp packaging/arch/PKGBUILD dist/arch/
cp "dist/$TAR_NAME" dist/arch/
echo "Arch PKGBUILD and source tarball in dist/arch/"
echo "Run 'makepkg -si' in dist/arch/ to build and install."

echo "Done."
