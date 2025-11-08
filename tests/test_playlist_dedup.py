#!/usr/bin/env python3
"""
Lightweight test for playlist deduplication logic.
Run with: python3 -m tests.test_playlist_dedup
"""
from gui.playlist_utils import parse_flat_playlist_lines

# Simulate yt-dlp --flat-playlist --dump-json output with duplicates and noise
sample_lines = [
    '{"_type": "url", "id": "VID123", "url": "VID123", "title": "First"}',
    '{"_type": "url", "id": "VID456", "url": "VID456", "title": "Second"}',
    '   ',  # blank
    '{"_type": "url", "id": "VID123", "url": "VID123", "title": "First Duplicate"}',
    '{malformed json}',
    '{"_type": "url", "url": "VID789", "title": "Third (no id key)"}',
]

expected = [
    "https://www.youtube.com/watch?v=VID123",
    "https://www.youtube.com/watch?v=VID456",
    "https://www.youtube.com/watch?v=VID789",
]

result = parse_flat_playlist_lines(sample_lines)

assert result == expected, f"Expected {expected}, got {result}"

print("PASS: Playlist dedup produced unique canonical URLs:")
for u in result:
    print(" -", u)
