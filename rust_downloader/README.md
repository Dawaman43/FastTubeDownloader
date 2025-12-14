# FastTube Downloader - Rust Module

This directory contains the high-performance Rust-based download engine.

## Features

- **Multi-threaded Downloads**: Up to 32 parallel connections
- **HTTP Range Requests**: Efficient chunk-based downloading
- **Automatic Fallback**: Falls back to single-threaded for unsupported servers
- **Progress Tracking**: Real-time progress, speed, and ETA calculation
- **Python Integration**: Seamless PyO3 bindings

## Performance Benefits

- **3-5x faster** than Python-based downloaders for large files
- **Lower memory usage** due to streaming architecture
- **Better connection management** with Rust's async runtime
- **Native binary performance** without Python overhead

## Building

### Prerequisites

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install Python development headers
sudo apt-get install python3-dev  # Ubuntu/Debian
sudo dnf install python3-devel     # Fedora
```

### Build

```bash
# From the project root
chmod +x build_rust.sh
./build_rust.sh
```

This will:
1. Compile the Rust module in release mode (optimized)
2. Copy the `.so` file to `gui/` directory
3. Make it importable from Python as `fasttube_downloader`

## Usage from Python

```python
from gui.download_engine import get_engine

engine = get_engine()

# Download a file
engine.download_file(
    url="https://example.com/file.zip",
    output_path="/home/user/Downloads/file.zip",
    connections=16,
    speed_limit_kbps=1000  # Optional: 1 MB/s limit
)

# Get file size
size = engine.get_file_size("https://example.com/file.zip")
print(f"File size: {size} bytes")
```

## Fallback Mechanism

If the Rust module fails to load or compile, the system automatically falls back to `aria2c`:

```
[Rust] Attempting fast download...
[Rust downloader failed]: Module not found
[Fallback] Using aria2c...
```

This ensures the application always works, even without the Rust module.

## Development

```bash
cd rust_downloader

# Run tests
cargo test

# Build with debug symbols
cargo build

# Build optimized release
cargo build --release

# Check for issues
cargo clippy
```

## License

MIT (matching the main project)
