# Contributing to FastTube Downloader

Thanks for your interest in contributing! This guide explains how to get set up, propose changes, and submit pull requests.

## Table of Contents
1. Code of Conduct
2. Getting Started
3. Development Workflow
4. Style & Conventions
5. Issue Labels
6. Pull Request Checklist
7. Release Process
8. Questions & Help

## 1. Code of Conduct
Be respectful. Harassment or abuse is not tolerated. If in doubt: be kind.

## 2. Getting Started
```bash
# Clone
git clone https://github.com/Dawaman43/FastTubeDownloader.git
cd FastTubeDownloader

# (Optional) Create virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Install runtime deps (Debian-based)
sudo apt install python3-gi gir1.2-gtk-3.0 yt-dlp aria2

# Run app
python3 gui/main_window.py
```
For other distros install equivalent GTK3 GI bindings, yt-dlp, and aria2.

## 3. Development Workflow
1. Fork the repository.
2. Create a branch: `git checkout -b feature/my-improvement`.
3. Make changes with minimal diff noise (avoid unrelated formatting).
4. Run quick checks:
   - `python -m py_compile gui/main_window.py`
   - `PYTHONPATH=. python tests/test_playlist_dedup.py`
5. Commit: `git commit -m "feat: add XYZ"`.
6. Push & open PR.

## 4. Style & Conventions
- Python: Keep imports compact and avoid excessive comments. Clear, direct code preferred over verbose docstrings.
- Shell scripts: `set -euo pipefail` when appropriate.
- Commit messages: Conventional commits style encouraged (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`).
- Avoid adding heavy dependencies.

## 5. Issue Labels
| Label | Purpose |
|-------|---------|
| good first issue | Low-risk tasks for newcomers |
| bug | Incorrect behavior or errors |
| enhancement | Feature requests |
| packaging | Distribution-related items |
| help wanted | Needs contributor assistance |
| question | Clarifications |

## 6. Pull Request Checklist
Before requesting review:
- [ ] Code compiles (no syntax errors)
- [ ] Basic test(s) pass
- [ ] No accidental secrets or large binaries
- [ ] README / Help updated if behavior changes
- [ ] No stray debug prints

## 7. Release Process
1. Update `version.txt` if bumping version.
2. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
3. Push: `git push origin main --tags`.
4. GitHub Actions (future) will build artifacts; otherwise run `scripts/build.sh` manually and attach zips.
5. Publish GitHub Release with notes & binaries (.deb, .rpm, AppImage, etc.).

## 8. Questions & Help
Open an issue with reproduction steps or desired outcome. Include platform, command output, and logs: `~/.cache/fasttube-downloader.log`.

----
Thanks for helping improve FastTube Downloader!