#!/usr/bin/env python3
"""
Python wrapper for the Rust download engine.
Provides a fallback to aria2c if the Rust module is not available.
"""
import os
import subprocess
from pathlib import Path

# Try to import the Rust module
try:
    import fasttube_downloader as rust_dl
    HAS_RUST_DOWNLOADER = True
except ImportError:
    HAS_RUST_DOWNLOADER = False
    rust_dl = None


class DownloadEngine:
    """Unified download engine that uses Rust if available, falls back to aria2c"""
    
    def __init__(self):
        self.use_rust = HAS_RUST_DOWNLOADER
        
    def download_file(self, url: str, output_path: str, connections: int = 16, 
                     speed_limit_kbps: int = None) -> bool:
        """
        Download a file using the best available method.
        
        Args:
            url: URL to download
            output_path: Path to save the file
            connections: Number of parallel connections
            speed_limit_kbps: Speed limit in KB/s (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_rust:
            try:
                rust_dl.download_file(
                    url, 
                    output_path, 
                    connections=connections,
                    speed_limit_kbps=speed_limit_kbps
                )
                return True
            except Exception as e:
                print(f"[Rust downloader failed]: {e}")
                print("[Fallback] Using aria2c...")
                self.use_rust = False
        
        # Fallback to aria2c
        return self._download_with_aria2c(url, output_path, connections, speed_limit_kbps)
    
    def _download_with_aria2c(self, url: str, output_path: str, 
                             connections: int, speed_limit_kbps: int) -> bool:
        """Fallback download using aria2c"""
        output_dir = str(Path(output_path).parent)
        output_name = Path(output_path).name
        
        cmd = [
            "aria2c",
            "-x", str(connections),
            "-s", str(connections),
            "-k", "1M",
            "--min-split-size=1M",
            "--file-allocation=none",
            "-d", output_dir,
            "-o", output_name,
        ]
        
        if speed_limit_kbps:
            cmd.append(f"--max-overall-download-limit={speed_limit_kbps}K")
        
        cmd.append(url)
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"[aria2c failed]: {e}")
            return False
    
    def get_file_size(self, url: str) -> int:
        """Get file size without downloading"""
        if self.use_rust:
            try:
                return rust_dl.get_file_size(url)
            except Exception:
                pass
        
        # Fallback using curl
        try:
            result = subprocess.run(
                ["curl", "-sI", url],
                capture_output=True,
                text=True,
                timeout=10
            )
            for line in result.stdout.split('\n'):
                if line.lower().startswith('content-length:'):
                    return int(line.split(':')[1].strip())
        except Exception:
            pass
        
        return 0


# Global instance
_engine = None

def get_engine() -> DownloadEngine:
    """Get the global download engine instance"""
    global _engine
    if _engine is None:
        _engine = DownloadEngine()
    return _engine
