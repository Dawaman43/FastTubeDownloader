#!/usr/bin/env sh
LOGDIR="${XDG_CACHE_HOME:-$HOME/.cache}"
mkdir -p "$LOGDIR" 2>/dev/null || true
exec python3 /opt/FastTubeDownloader/gui/main_window.py "$@" 2>>"$LOGDIR/fasttube-downloader.log"
