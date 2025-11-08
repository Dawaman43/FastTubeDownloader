#!/usr/bin/env bash
# FastTube Downloader helper script
# CLI (GUI) args:
#   fast_ytdl.sh URL DOWNLOAD_FOLDER FORMAT QUALITY SUBS SPEED_KBPS ARIA_CONNECTIONS ARIA_SPLITS FRAGMENT_CONCURRENCY CATEGORY_MODE
# If invoked with no positional args it enters Native Messaging mode (reads length-prefixed JSON requests from stdin).

set -o pipefail

CONFIG_DIR="$HOME/.config/FastTubeDownloader"
CONFIG_FILE="$CONFIG_DIR/config.json"

load_defaults() {
    if [ -f "$CONFIG_FILE" ]; then
        DOWNLOAD_FOLDER=$(jq -r '.download_folder // "."' "$CONFIG_FILE")
    else
        DOWNLOAD_FOLDER="."
    fi
}

send_json() {
    local json="$1"
    local len=${#json}
    printf "\x%02x\x%02x\x%02x\x%02x" $((len & 0xFF)) $(((len >> 8) & 0xFF)) $(((len >> 16) & 0xFF)) $(((len >> 24) & 0xFF))
    printf "%s" "$json"
}

############################################
# CLI MODE
############################################
if [ $# -ge 1 ]; then
    URL="$1"; DOWNLOAD_FOLDER="${2:-.}"; FORMAT="${3:-Best (default)}"; QUALITY="${4:-}"; SUBS="${5:-n}"; SPEED_LIMIT_KBPS="${6:-}"; ARIA_CONNECTIONS="${7:-32}"; ARIA_SPLITS="${8:-32}"; FRAGMENT_CONCURRENCY="${9:-16}"; CATEGORY_MODE="${10:-idm}";

    mkdir -p "$DOWNLOAD_FOLDER" || { echo "Cannot create folder: $DOWNLOAD_FOLDER"; exit 1; }
    cd "$DOWNLOAD_FOLDER" || { echo "Cannot enter folder: $DOWNLOAD_FOLDER"; exit 1; }

        [[ "$ARIA_CONNECTIONS" =~ ^[0-9]+$ ]] || ARIA_CONNECTIONS=32
    [[ "$ARIA_SPLITS" =~ ^[0-9]+$ ]] || ARIA_SPLITS=32
    [[ "$FRAGMENT_CONCURRENCY" =~ ^[0-9]+$ ]] || FRAGMENT_CONCURRENCY=16
    [ "$ARIA_CONNECTIONS" -gt 0 ] || ARIA_CONNECTIONS=32
    [ "$ARIA_SPLITS" -gt 0 ] || ARIA_SPLITS=32
    [ "$FRAGMENT_CONCURRENCY" -gt 0 ] || FRAGMENT_CONCURRENCY=16
        # Clamp aria2 max connections per server to its allowed range (1-16)
        if [ "$ARIA_CONNECTIONS" -gt 16 ]; then ARIA_CONNECTIONS=16; fi
        if [ "$ARIA_CONNECTIONS" -lt 1 ]; then ARIA_CONNECTIONS=1; fi

    CATEGORY_MODE=$(echo "$CATEGORY_MODE" | tr '[:upper:]' '[:lower:]')
    [ "$CATEGORY_MODE" = "flat" ] || CATEGORY_MODE="idm"

    FORMAT_LC=$(echo "$FORMAT" | tr '[:upper:]' '[:lower:]')
    SUBDIR=""
        if [ "$CATEGORY_MODE" = "idm" ]; then
                # Route Audio Only to Music; everything else to Videos
                if [ "$FORMAT_LC" = "audio only" ]; then SUBDIR="Music"; else SUBDIR="Videos"; fi
                mkdir -p "$SUBDIR"
        fi
    OUTPUT_TEMPLATE="%(title)s.%(ext)s"
    [ -n "$SUBDIR" ] && OUTPUT_TEMPLATE="$SUBDIR/%(title)s.%(ext)s"

        SPEED_ARG=""; [ -n "$SPEED_LIMIT_KBPS" ] && SPEED_ARG="--max-overall-download-limit=${SPEED_LIMIT_KBPS}K"

        # Quick sanity checks to fail fast with helpful messages
        if ! command -v yt-dlp >/dev/null 2>&1; then
                echo "ERROR: yt-dlp is not installed or not in PATH. Please install it: pip install yt-dlp or your package manager." >&2
                exit 127
        fi
        # aria2c is optional; if missing we'll let Python path drop back to internal downloader automatically
        if ! command -v aria2c >/dev/null 2>&1; then
                echo "WARN: aria2c not found. Falling back to yt-dlp's internal downloader (slower)." >&2
        fi

    if [[ "$URL" =~ ^magnet: ]] || [[ "$URL" == *.torrent ]]; then
        echo "[FastTube] Torrent/magnet detected; aria2c direct mode.";
        TORR_DIR="${SUBDIR:-Torrents}"; mkdir -p "$TORR_DIR"; cd "$TORR_DIR" || exit 1
        aria2c -x "$ARIA_CONNECTIONS" -s "$ARIA_SPLITS" -j "$ARIA_SPLITS" -k 1M --min-split-size=1M --file-allocation=none ${SPEED_ARG:+$SPEED_ARG} "$URL"
        exit $?
    fi

        echo "=== FastTube CLI Debug ==="
    echo "URL: $URL"
    echo "Folder: $(pwd)"
    echo "Format: $FORMAT"
    echo "Quality: $QUALITY"
    echo "Subs: $SUBS"
    echo "Speed KB/s: ${SPEED_LIMIT_KBPS:-unlimited}"
    echo "Aria connections: $ARIA_CONNECTIONS splits: $ARIA_SPLITS"
    echo "Fragment concurrency: $FRAGMENT_CONCURRENCY"
    echo "Category mode: $CATEGORY_MODE (subdir=${SUBDIR:-none})"
    echo "Output template: $OUTPUT_TEMPLATE"
    echo "=============================================="

        # Build shell-side opts for CLI fallback if Python path fails
        SUBS_OPT=""; [ "$SUBS" = "y" ] || [ "$SUBS" = "Y" ] || [ "$SUBS" = "true" ] && SUBS_OPT="--write-subs --sub-lang en --convert-subs srt"
        FORMAT_OPT=""
        case "$FORMAT" in
                "Best Video + Audio") FORMAT_OPT="-f bestvideo+bestaudio --merge-output-format mp4" ;;
                "Audio Only") FORMAT_OPT="-f bestaudio/best --audio-format mp3" ;;
                "Best (default)") FORMAT_OPT="" ;;
                *) FORMAT_OPT="-f $FORMAT" ;;
        esac
        if [[ "$FORMAT" != *"audio"* ]] && [ -n "$QUALITY" ]; then
                # Cap by height if quality provided and not audio-only
                FORMAT_OPT="-f best[height<=$QUALITY]"
        fi
        ARIA_ARGS="-x $ARIA_CONNECTIONS -s $ARIA_SPLITS -k 1M --min-split-size=1M --file-allocation=none"
        [ -n "$SPEED_ARG" ] && ARIA_ARGS="$ARIA_ARGS $SPEED_ARG"

    PY_ENV_OUTTMPL="$OUTPUT_TEMPLATE" \
    PY_ENV_FORMAT="$FORMAT" \
    PY_ENV_QUALITY="$QUALITY" \
    PY_ENV_SUBS="$SUBS" \
    PY_ENV_SPEED_ARG="$SPEED_ARG" \
    PY_ENV_ARIA_CONN="$ARIA_CONNECTIONS" \
    PY_ENV_ARIA_SPLITS="$ARIA_SPLITS" \
    PY_ENV_FRAG_CONC="$FRAGMENT_CONCURRENCY" \
        PY_ENV_BASE_DIR="$(pwd)" \
        python3 - "$URL" <<'PY'
import os, sys
try:
        import yt_dlp
except Exception as e:
        print(f"ERROR: yt-dlp not installed: {e}", file=sys.stderr)
        sys.exit(1)
import shutil

def coerce(val, default):
        try:
                iv = int(val); return iv if iv > 0 else default
        except Exception: return default

outtmpl = os.environ.get('PY_ENV_OUTTMPL','%(title)s.%(ext)s')
fmt = os.environ.get('PY_ENV_FORMAT','Best (default)')
quality = os.environ.get('PY_ENV_QUALITY','')
subs_flag = os.environ.get('PY_ENV_SUBS','n').lower()
speed_arg = os.environ.get('PY_ENV_SPEED_ARG','')
aria_conn = str(coerce(os.environ.get('PY_ENV_ARIA_CONN','32'),32))
aria_splits = str(coerce(os.environ.get('PY_ENV_ARIA_SPLITS','32'),32))
frag_conc = coerce(os.environ.get('PY_ENV_FRAG_CONC','16'),16)
base_dir = os.environ.get('PY_ENV_BASE_DIR', os.getcwd())

external_args = None
# Only configure aria2c if present, else let yt-dlp use its internal downloader
if shutil.which('aria2c'):
        external_args = ['-x', aria_conn, '-s', aria_splits, '-k','1M','--min-split-size=1M','--file-allocation=none']
        if speed_arg:
                external_args.append(speed_arg)

ydl_opts = {
        'outtmpl': outtmpl,
        # Configure external downloader only if available
        **({'external_downloader': 'aria2c', 'external_downloader_args': external_args} if external_args else {}),
        'continuedl': True,
        'ignoreerrors': True,
        'yesplaylist': True,
        'concurrent_fragment_downloads': frag_conc,
}

if subs_flag in ('y','yes','true','1'):
        ydl_opts['writesubtitles'] = True
        ydl_opts['subtitleslangs'] = ['en']
        pp = ydl_opts.get('postprocessors', [])
        pp.append({'key':'FFmpegSubtitlesConvertor','format':'srt'})
        ydl_opts['postprocessors'] = pp

fmt_clean = fmt.strip()
fmt_lower = fmt_clean.lower()
qual_digits = ''.join(ch for ch in quality if ch.isdigit())
if fmt_clean == 'Best Video + Audio':
        ydl_opts['format'] = 'bestvideo+bestaudio'
        ydl_opts['merge_output_format'] = 'mp4'
elif fmt_clean == 'Audio Only':
        ydl_opts['format'] = 'bestaudio/best'
        pp = ydl_opts.get('postprocessors', [])
        pp.append({'key':'FFmpegExtractAudio','preferredcodec':'mp3'})
        ydl_opts['postprocessors'] = pp
elif fmt_clean and fmt_clean != 'Best (default)':
        ydl_opts['format'] = fmt_clean
elif qual_digits and 'audio' not in fmt_lower:
        ydl_opts['format'] = f'best[height<={qual_digits}]'

def hook(d):
        st = d.get('status')
        if st == 'downloading':
                pct = d.get('_percent_str','0%')
                title = d.get('title') or (d.get('info_dict') or {}).get('title') or 'Unknown'
                print(f'PROGRESS: {pct}')
                print(f'TITLE: {title}')
                sp = d.get('_speed_str') or ''
                eta = d.get('_eta_str') or ''
                total = d.get('_total_bytes_str') or d.get('_total_bytes_estimate_str') or ''
                down = d.get('_downloaded_bytes_str') or ''
                meta=[]
                if sp: meta.append(f'speed={sp}')
                if eta: meta.append(f'eta={eta}')
                if down: meta.append(f'downloaded={down}')
                if total: meta.append(f'total={total}')
                if meta: print('META: ' + ' '.join(meta))
                sys.stdout.flush()
        elif st == 'finished':
                fn = d.get('filename') or (d.get('info_dict') or {}).get('_filename') or ''
                if fn and not os.path.isabs(fn): fn = os.path.join(base_dir, fn)
                if fn:
                        print(f'FILE: {fn}')
                        sys.stdout.flush()

ydl_opts['progress_hooks'] = [hook]

# Graceful format fallback logic: retry with safer formats if the requested one isn't available
import copy
try:
        url = sys.argv[1]
        candidates = []
        base_fmt = ydl_opts.get('format')
        if base_fmt:
                candidates.append(base_fmt)
        # Build sensible fallbacks
        if fmt_clean == 'Audio Only':
                candidates += ['bestaudio/best', 'best']
        elif fmt_clean == 'Best Video + Audio' or qual_digits:
                candidates += ['bestvideo+bestaudio/best', 'best']
        else:
                candidates += ['bestvideo+bestaudio/best', 'best']
        # de-duplicate while preserving order
        seen = set(); fmt_chain = []
        for f in candidates:
                if f and f not in seen:
                        seen.add(f); fmt_chain.append(f)

        last_err = None
        success = False
        for f in fmt_chain:
                try_opts = copy.deepcopy(ydl_opts)
                try_opts['format'] = f
                # Only enforce mp4 merge when asking explicit bestvideo+bestaudio
                if 'bestvideo+bestaudio' in f:
                        try_opts['merge_output_format'] = 'mp4'
                else:
                        try_opts.pop('merge_output_format', None)
                print(f'RETRY: format={f}')
                with yt_dlp.YoutubeDL(try_opts) as ydl:
                        ret = ydl.download([url])
                        if ret == 0:
                                success = True
                                last_err = None
                                break
                        else:
                                last_err = RuntimeError(f'yt-dlp exited with code {ret}')
                                continue
        if last_err or not success:
                raise last_err
except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
PY
    status=$?
        if [ $status -ne 0 ]; then
                # Last-resort fallback via yt-dlp CLI (no custom PROGRESS/TITLE markers, but UI can parse standard output)
                echo "[FastTube] Python path failed; attempting CLI fallback..."
                # If aria2c isn't available, don't instruct yt-dlp to use it
                if command -v aria2c >/dev/null 2>&1; then
                    yt-dlp --yes-playlist --ignore-errors \
                                             --output "$OUTPUT_TEMPLATE" \
                                             $FORMAT_OPT $SUBS_OPT \
                                             --external-downloader aria2c \
                                             --external-downloader-args "$ARIA_ARGS" \
                                             --newline --progress --concurrent-fragments "$FRAGMENT_CONCURRENCY" \
                                             "$URL"
                else
                    yt-dlp --yes-playlist --ignore-errors \
                                             --output "$OUTPUT_TEMPLATE" \
                                             $FORMAT_OPT $SUBS_OPT \
                                             --newline --progress --concurrent-fragments "$FRAGMENT_CONCURRENCY" \
                                             "$URL"
                fi
                status=$?
        fi
        [ $status -eq 0 ] && echo "Download complete." || echo "Download failed.";
        exit $status
fi

############################################
# Native Messaging MODE
############################################
load_defaults
while true; do
    read -r -n 4 LEN_BYTES || break
    [ ${#LEN_BYTES} -eq 4 ] || break
    LEN=$(( (($(printf '%d' "'${LEN_BYTES:3:1}")) << 24) + (($(printf '%d' "'${LEN_BYTES:2:1}")) << 16) + (($(printf '%d' "'${LEN_BYTES:1:1}")) << 8) + $(printf '%d' "'${LEN_BYTES:0:1}" ) ))
    [ $LEN -gt 0 ] || break
    read -r -n $LEN INPUT_JSON || break

    URL=$(echo "$INPUT_JSON" | jq -r '.url // empty')
    if [ -z "$URL" ]; then send_json '{"status":"error","message":"No URL provided"}'; continue; fi
    FORMAT=$(echo "$INPUT_JSON" | jq -r '.format // "Best (default)"')
    QUALITY=$(echo "$INPUT_JSON" | jq -r '.quality // ""')
    SUBS=$(echo "$INPUT_JSON" | jq -r '.subs // "n"')
    DOWNLOAD_FOLDER_INPUT=$(echo "$INPUT_JSON" | jq -r '.download_folder // "'$DOWNLOAD_FOLDER'"')

    mkdir -p "$DOWNLOAD_FOLDER_INPUT" 2>/dev/null
    cd "$DOWNLOAD_FOLDER_INPUT" 2>/dev/null || { send_json '{"status":"error","message":"Invalid download folder"}'; continue; }

    SUBS_OPT=""; [ "$SUBS" = "y" ] || [ "$SUBS" = "true" ] && SUBS_OPT="--write-subs --sub-lang en --convert-subs srt"
    case "$FORMAT" in
        "Best Video + Audio") FORMAT_OPT="-f 'bestvideo+bestaudio' --merge-output-format mp4" ;;
        "Audio Only") FORMAT_OPT="-f 'bestaudio/best' --audio-format mp3" ;;
        "Best (default)") FORMAT_OPT="" ;;
        *) FORMAT_OPT="-f '$FORMAT'" ;;
    esac
    if [[ "$FORMAT" != *"audio"* ]] && [ -n "$QUALITY" ]; then FORMAT_OPT="-f 'best[height<=${QUALITY}]'"; fi

    OUTPUT_TEMPLATE="%(title)s.%(ext)s"
    ARIA_ARGS="-x 16 -s 16 -k 1M --min-split-size=1M --file-allocation=none"
    OPTIONS="--yes-playlist --ignore-errors --output '$OUTPUT_TEMPLATE' $FORMAT_OPT --external-downloader aria2c --external-downloader-args '$ARIA_ARGS' $SUBS_OPT --newline --progress --concurrent-fragments 10"

    send_json '{"status":"started","url":"'"$URL"'"}'
    yt-dlp $OPTIONS "$URL" 2>&1 | while IFS= read -r line; do
        if [[ "$line" =~ \[download\].*([0-9]+\.[0-9]+)% ]]; then
            pct=$(echo "$line" | grep -o '[0-9]\+\.[0-9]\+%' | cut -d% -f1)
            send_json '{"status":"progress","url":"'"$URL"'","percent":'"$pct"'}'
        fi
    done
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        send_json '{"status":"finished","url":"'"$URL"'"}'
    else
        send_json '{"status":"error","message":"Download failed"}'
    fi
done
