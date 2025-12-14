#!/bin/bash
# Build script for the Rust download engine

set -e

echo "Building Rust download engine..."

cd rust_downloader

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "Rust is not installed. Installing rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi

# Build the Rust module
echo "Compiling Rust module (this may take a few minutes)..."
cargo build --release

# Find the compiled .so file
SO_FILE=$(find target/release -name "fasttube_downloader*.so" -o -name "libfasttube_downloader*.so" | head -1)

if [ -z "$SO_FILE" ]; then
    echo "ERROR: Could not find compiled .so file"
    exit 1
fi

# Copy to the gui directory for Python to import
echo "Installing Rust module..."
cp "$SO_FILE" "../gui/fasttube_downloader.so"

echo "✅ Rust download engine built successfully!"
echo "Location: gui/fasttube_downloader.so"
