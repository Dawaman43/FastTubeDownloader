#!/usr/bin/env python3
"""
File Organizer Module for FastTubeDownloader v2
Handles intelligent file categorization and playlist organization
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple


class FileOrganizer:
    """Organizes downloads by file type and handles playlist folder creation"""
    
    # File type categories with their extensions
    CATEGORIES = {
        'Videos': [
            'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v',
            'mpg', 'mpeg', '3gp', 'f4v', 'ts', 'mts', 'm2ts'
        ],
        'Music': [
            'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a',
            'opus', 'ape', 'alac'
        ],
        'Documents': [
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'txt', 'rtf', 'odt', 'ods', 'odp', 'epub', 'mobi'
        ],
        'Archives': [
            'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'iso', 'dmg'
        ],
        'Programs': [
            'exe', 'msi', 'deb', 'rpm', 'appimage', 'apk', 'pkg', 'sh', 'bin'
        ],
        'Pictures': [
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp',
            'ico', 'tiff', 'tif', 'psd', 'raw', 'cr2', 'nef'
        ]
    }
    
    def __init__(self, base_dir: str, category_mode: str = 'idm'):
        """
        Initialize the file organizer
        
        Args:
            base_dir: Base download directory
            category_mode: 'idm' for categorized folders, 'flat' for no categorization
        """
        self.base_dir = Path(base_dir)
        self.category_mode = category_mode.lower()
        
    def get_category_for_extension(self, extension: str) -> Optional[str]:
        """Get the category for a file extension"""
        ext = extension.lower().lstrip('.')
        
        for category, extensions in self.CATEGORIES.items():
            if ext in extensions:
                return category
        
        return None
    
    def detect_file_type(self, filename: str, url: str = '') -> str:
        """
        Detect file type from filename or URL
        
        Returns:
            Category name or 'Videos' as default
        """
        # Try to get extension from filename
        if filename:
            ext = Path(filename).suffix.lstrip('.')
            category = self.get_category_for_extension(ext)
            if category:
                return category
        
        # Check URL patterns for video sites
        video_sites = [
            'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
            'twitch.tv', 'facebook.com/watch', 'instagram.com',
            'twitter.com', 'tiktok.com'
        ]
        
        if url and any(site in url.lower() for site in video_sites):
            return 'Videos'
        
        return 'Videos'  # Default
    
    def sanitize_folder_name(self, name: str) -> str:
        """Sanitize playlist/folder name for filesystem"""
        # Remove invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace multiple spaces with single space
        name = re.sub(r'\s+', ' ', name)
        # Trim and limit length
        name = name.strip()[:100]
        
        return name or 'Unnamed'
    
    def create_playlist_folder(self, playlist_name: str, category: str = 'Videos') -> Path:
        """
        Create a folder for playlist downloads
        
        Args:
            playlist_name: Name of the playlist
            category: File category (Videos, Music, etc.)
            
        Returns:
            Path to the playlist folder
        """
        sanitized_name = self.sanitize_folder_name(playlist_name)
        
        if self.category_mode == 'idm':
            # Create: Downloads/Videos/[PlaylistName]/
            folder_path = self.base_dir / category / sanitized_name
        else:
            # Create: Downloads/[PlaylistName]/
            folder_path = self.base_dir / sanitized_name
        
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path
    
    def get_download_path(self, 
                         filename: str,
                         url: str = '',
                         playlist_name: Optional[str] = None,
                         format_type: str = '') -> Tuple[Path, str]:
        """
        Get the appropriate download path for a file
        
        Args:
            filename: Name of the file to download
            url: URL being downloaded
            playlist_name: Optional playlist name for organization
            format_type: Format type hint ('audio', 'video', etc.)
            
        Returns:
            Tuple of (download_directory, output_template)
        """
        # Determine category
        if 'audio' in format_type.lower():
            category = 'Music'
        else:
            category = self.detect_file_type(filename, url)
        
        # Handle playlist downloads
        if playlist_name:
            download_dir = self.create_playlist_folder(playlist_name, category)
            output_template = '%(title)s.%(ext)s'
        else:
            # Regular downloads
            if self.category_mode == 'idm':
                download_dir = self.base_dir / category
                download_dir.mkdir(parents=True, exist_ok=True)
                output_template = '%(title)s.%(ext)s'
            else:
                download_dir = self.base_dir
                output_template = '%(title)s.%(ext)s'
        
        return download_dir, output_template
    
    def organize_existing_file(self, filepath: str) -> Optional[Path]:
        """
        Move an existing file to its appropriate category folder
        
        Args:
            filepath: Path to the file to organize
            
        Returns:
            New path if moved, None if not moved
        """
        if self.category_mode != 'idm':
            return None
        
        source = Path(filepath)
        if not source.exists() or not source.is_file():
            return None
        
        # Detect category
        category = self.detect_file_type(source.name)
        if not category:
            return None
        
        # Create category folder
        category_dir = self.base_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        # Move file
        destination = category_dir / source.name
        
        # Handle name conflicts
        counter = 1
        while destination.exists():
            stem = source.stem
            suffix = source.suffix
            destination = category_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        try:
            source.rename(destination)
            return destination
        except Exception as e:
            print(f"Failed to organize {filepath}: {e}")
            return None
    
    def get_category_stats(self) -> Dict[str, int]:
        """Get file count statistics for each category"""
        stats = {}
        
        for category in self.CATEGORIES.keys():
            category_dir = self.base_dir / category
            if category_dir.exists():
                files = list(category_dir.rglob('*'))
                stats[category] = len([f for f in files if f.is_file()])
            else:
                stats[category] = 0
        
        return stats


def is_playlist_url(url: str) -> bool:
    """
    Check if a URL appears to be a playlist
    
    Args:
        url: URL to check
        
    Returns:
        True if appears to be a playlist URL
    """
    playlist_patterns = [
        r'[?&]list=',  # YouTube playlist
        r'/playlists?/',  # Generic playlist path
        r'/album/',  # Music album
        r'/sets?/',  # SoundCloud sets
        r'/collection/',  # Collection/playlist
    ]
    
    return any(re.search(pattern, url, re.IGNORECASE) for pattern in playlist_patterns)


def extract_playlist_name_from_url(url: str) -> Optional[str]:
    """
    Try to extract playlist name from URL
    
    Args:
        url: Playlist URL
        
    Returns:
        Playlist name if detectable, None otherwise
    """
    # This is a simple extraction, actual implementation should use yt-dlp
    # to get the real playlist name
    
    # YouTube playlist ID
    match = re.search(r'[?&]list=([^&]+)', url)
    if match:
        return f"Playlist_{match.group(1)[:20]}"
    
    return None


if __name__ == '__main__':
    # Test the organizer
    organizer = FileOrganizer('/tmp/test_downloads', 'idm')
    
    # Test category detection
    print("Category detection tests:")
    print(f"video.mp4: {organizer.detect_file_type('video.mp4', '')}")
    print(f"song.mp3: {organizer.detect_file_type('song.mp3', '')}")
    print(f"document.pdf: {organizer.detect_file_type('document.pdf', '')}")
    
    # Test playlist folder creation
    print("\nPlaylist folder creation:")
    playlist_folder = organizer.create_playlist_folder("My Awesome Playlist", "Videos")
    print(f"Created: {playlist_folder}")
    
    # Test download path
    print("\nDownload path generation:")
    path, template = organizer.get_download_path(
        'test.mp4',
        'https://youtube.com/watch?v=test',
        playlist_name='My Playlist'
    )
    print(f"Path: {path}")
    print(f"Template: {template}")
