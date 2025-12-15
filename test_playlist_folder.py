
import sys
import os
sys.path.append(os.getcwd())
import shutil
from pathlib import Path
from gui.file_organizer import FileOrganizer

# Mock setup
test_dir = Path("/tmp/ftd_test_playlist")
if test_dir.exists():
    shutil.rmtree(test_dir)
test_dir.mkdir()

organizer = FileOrganizer(str(test_dir), category_mode='idm')

# Test 1: Standard Playlist
print("Test 1: Standard Playlist (IDM Mode)")
path, tmpl = organizer.get_download_path("video.mp4", playlist_name="MyPlaylist")
print(f"Path: {path}")
expected = test_dir / "Videos" / "MyPlaylist"
if path == expected:
    print("PASS")
else:
    print(f"FAIL. Expected {expected}, got {path}")

# Test 2: Standard Playlist (Flat Mode)
print("\nTest 2: Standard Playlist (Flat Mode)")
organizer.category_mode = 'flat'
path, tmpl = organizer.get_download_path("video.mp4", playlist_name="MyPlaylist")
print(f"Path: {path}")
expected = test_dir / "MyPlaylist"
if path == expected:
    print("PASS")
else:
    print(f"FAIL. Expected {expected}, got {path}")

# Test 3: Custom Folder Override (Simulating _spooler logic)
print("\nTest 3: Custom Folder Override")
custom_dir = test_dir / "Custom"
organizer.base_dir = custom_dir
organizer.category_mode = 'idm'
path, tmpl = organizer.get_download_path("video.mp4", playlist_name="MyPlaylist")
print(f"Path: {path}")
expected = custom_dir / "Videos" / "MyPlaylist"
if path == expected:
    print("PASS")
else:
    print(f"FAIL. Expected {expected}, got {path}")

