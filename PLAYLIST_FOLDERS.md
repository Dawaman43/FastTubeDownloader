# Playlist Folder Organization Feature

## Overview
Added automatic playlist folder organization to FastTube Downloader. When downloading videos from a YouTube playlist, each playlist now gets its own dedicated folder, keeping your downloads organized.

## How It Works

### 1. Playlist Detection & Title Extraction
When you add a playlist URL, the application:
- Detects it's a playlist (not a single video)
- Extracts the playlist title from yt-dlp metadata
- Cleans the title to make it filesystem-safe (removes invalid characters like `<>:"/\|?*`)
- Limits the folder name to 100 characters to avoid path issues

**File**: `gui/main_window.py` - `add_playlist()` function (lines 2945-3020)

### 2. Playlist Title Sources
The app tries multiple methods to get the playlist name:
1. **Primary**: Extracts from `playlist_title` or `playlist` field in yt-dlp JSON output
2. **Fallback**: Uses `yt-dlp --flat-playlist --print playlist_title` command
3. **Final Fallback**: Creates a timestamped name like `Playlist_1700000000`

### 3. Folder Creation
When each video in the playlist is downloaded:
- The download manager checks if the item has a `playlist_name` attribute
- If yes, creates a subfolder: `Downloads/PlaylistName/`
- All videos from that playlist are saved in this folder
- The folder is created recursively with `os.makedirs(folder, exist_ok=True)`

**File**: `gui/main_window.py` - `_start_item_download()` function (lines 1338-1360)

## Code Changes

### Modified Files

#### 1. gui/main_window.py - `add_playlist()` function

**What Changed**:
- Added playlist title extraction logic
- Set `item.playlist_name` attribute for each video in the playlist

**Key Code**:
```python
# Extract playlist title from first entry
for raw in lines:
    data = json.loads(raw)
    if not playlist_title and (data.get('playlist_title') or data.get('playlist')):
        playlist_title = data.get('playlist_title') or data.get('playlist')
        # Clean up for filesystem
        playlist_title = re.sub(r'[<>:"/\\|?*]', '', playlist_title)
        if len(playlist_title) > 100:
            playlist_title = playlist_title[:100]
        break

# Assign to each video
for full_url in urls:
    item = DownloadItem(full_url, "Fetching title...")
    item.kind = 'media'
    item.playlist_name = playlist_title  # ← Store playlist name
```

#### 2. gui/main_window.py - `_start_item_download()` function

**What Changed**:
- Added check for `playlist_name` attribute
- Creates playlist folder before starting download
- Downloads file to playlist folder instead of root Downloads folder

**Key Code**:
```python
def _start_item_download(self, item):
    self._set_status(item, "Downloading...")
    folder = os.path.expanduser(self.config["download_folder"])
    
    # Create playlist subfolder if this item is part of a playlist
    if getattr(item, 'playlist_name', None):
        try:
            playlist_folder = os.path.join(folder, item.playlist_name)
            os.makedirs(playlist_folder, exist_ok=True)
            folder = playlist_folder
            print(f"[GUI] Downloading to playlist folder: {folder}", file=sys.stderr)
        except Exception as e:
            print(f"[GUI] Failed to create playlist folder: {e}", file=sys.stderr)
    
    # Continue with normal download using the modified folder path
    ...
```

## Example Usage

### Before
```
~/Downloads/
  ├── Cool Video 1.mp4
  ├── Cool Video 2.mp4
  ├── Cool Video 3.mp4
  ├── Another Video.mp4
  └── Random Download.mp4
```

### After
```
~/Downloads/
  ├── My Awesome Playlist/
  │   ├── Cool Video 1.mp4
  │   ├── Cool Video 2.mp4
  │   └── Cool Video 3.mp4
  ├── Tutorial Series/
  │   ├── Lesson 1.mp4
  │   ├── Lesson 2.mp4
  │   └── Lesson 3.mp4
  └── Another Video.mp4  (single video, not from playlist)
```

## Testing

### Test Cases
1. **Standard Playlist**: Download a normal YouTube playlist → Videos should be in a folder named after the playlist
2. **Long Playlist Name**: Test with a playlist having a very long title → Should be truncated to 100 chars
3. **Special Characters**: Test with playlist containing `<>:"/\|?*` → Should be sanitized
4. **Single Video**: Download a single video (not from playlist) → Should download to root folder as before
5. **Mixed Download**: Queue both playlist and single videos → Each should go to correct location

### Verification
```bash
# After downloading a playlist, check folder structure
ls -la ~/Downloads/
# Should see playlist folder names

tree ~/Downloads/
# Should show nested structure with playlist folders
```

## Benefits

✅ **Organization**: Videos from the same playlist are grouped together  
✅ **Easy Management**: Find all videos from a series in one place  
✅ **No Conflicts**: Playlist folders prevent filename collisions  
✅ **Backward Compatible**: Single videos still download to root folder  
✅ **Safe Names**: Automatic sanitization prevents filesystem errors  

## Technical Details

### Attributes Added
- `DownloadItem.playlist_name` (string, optional): Stores the sanitized playlist name

### Error Handling
- If playlist title extraction fails, uses timestamped fallback name
- If folder creation fails, logs error but continues download to root folder
- Preserves existing behavior for non-playlist downloads

### Performance Impact
- Minimal: Only adds one subprocess call per playlist (not per video)
- Folder creation is fast (uses `os.makedirs` with `exist_ok=True`)

## Future Enhancements

Possible improvements for future versions:
1. **Custom Folder Templates**: Let users define naming patterns like `{PlaylistName} - {Date}`
2. **Nested Organization**: Support playlist categories (e.g., `Music/Rock/Best Hits/`)
3. **Merge Playlists**: Option to merge multiple small playlists into one folder
4. **Playlist Metadata**: Save playlist info (description, URL) in folder as `.nfo` file

---

## Summary

The playlist folder organization feature makes FastTube Downloader much more organized and user-friendly, especially for users who download multiple playlists. Videos are automatically grouped by their source playlist, making it easy to manage large download collections.
