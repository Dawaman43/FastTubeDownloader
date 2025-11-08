# FastTube Downloader

Fast, extensible desktop + browser extension YouTube & generic file downloader.

## Features
- Desktop GTK app with queue, history, parallel downloads
- High-speed media via yt-dlp; segmented generic downloads via aria2 (RPC optional)
- Generic file support with automatic folder categorisation by extension
- Playlist expansion with deduplication
- Native messaging bridge: Chrome (MV3) + Firefox (MV2) manifests
- Permanent extension ID tooling (stable across machines)
- Pause / resume for aria2 RPC generic downloads
- Auto-start option, clipboard detection, size persistence

## Quick Install (Linux)
```bash
./setup.sh
```
Then load the unpacked extension:
- Chrome: chrome://extensions (Developer Mode) > Load unpacked > project root
- Firefox: web-ext run (see Packaging below)

## Stable Extension ID
Generate and inject a key (produces a stable ID):
```bash
python3 tools/generate_extension_key.py
```
Reload extension. Re-run `./setup.sh` (the script auto-detects ID for native messaging).

## Packaging
Use the provided build script to produce Chrome and Firefox extension archives in `dist/`:
```bash
scripts/build.sh
```
Outputs:
- `dist/fasttube_chrome.zip` (Manifest V3)
- `dist/fasttube_firefox.zip` (Manifest V2)

You can also load unpacked directly from the repo during development.

## Native Messaging
Setup script installs the host JSON for Chrome/Chromium (and prompts or auto-computes extension ID). For Firefox, copy the same host file into:
```
~/.mozilla/native-messaging-hosts/com.fasttube.downloader.json
```
Adjust `allowed_extensions` (Firefox) / `allowed_origins` (Chrome) accordingly.

## Generic File Downloads
Select "Generic File" in the format combo or paste a direct URL (.zip/.apk/etc.). Categorisation uses `generic_extensions_map` in config.
If aria2 RPC enabled: pause/resume works from the queue.
If aria2 missing: (TODO) fallback will attempt curl / wget.

## Configuration File
Stored at `~/.config/FastTubeDownloader/config.json`.
Notable keys:
- enable_generic (bool)
- auto_start (bool)
- aria2_rpc_enabled (bool)
- aria2_rpc_port (int)
- generic_extensions_map (dict category -> [extensions])
- window_width / window_height (persisted)

## Developer Utilities
- `tools/generate_extension_key.py` – produce stable ID, patch manifest
- `tests/test_playlist_dedup.py` – simple playlist dedup test

## Future Enhancements
- In-app settings UI for toggles and extension map editing
- aria2 absence fallback to curl/wget
- Firefox native host installer section in setup.sh

## Troubleshooting
| Issue | Fix |
|-------|-----|
| Extension ID changed | Re-run key script; ensure manifest.key kept; never overwrite private key unless intending ID change |
| Native host error in popup | Rerun `./setup.sh`; check extension ID alignment; inspect `~/.cache/fasttube-downloader.log` |
| Downloads not starting | Confirm control server log: `Control server listening on 127.0.0.1:47653` |
| Playlist duplicates | Already fixed via JSON flat playlist parser |

## License
MIT (add license file if distributing).
