from __future__ import annotations
import json
from typing import Iterable, List, Set

def parse_flat_playlist_lines(lines: Iterable[str]) -> List[str]:
    urls: List[str] = []
    seen: Set[str] = set()
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        vid_id = data.get('id') or data.get('url')
        if not vid_id or vid_id in seen:
            continue
        seen.add(vid_id)
        urls.append(f"https://www.youtube.com/watch?v={vid_id}")
    return urls

__all__ = ["parse_flat_playlist_lines"]
