#!/usr/bin/env python3
import sys
import json
import socket
import struct
import threading
import subprocess
import time
import os

HOST = '127.0.0.1'
PORT = 47653


def send_native_message(msg: dict):
    data = json.dumps(msg).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('<I', len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.flush()


def read_native_message():
    raw_len = sys.stdin.buffer.read(4)
    if not raw_len or len(raw_len) < 4:
        return None
    (msg_len,) = struct.unpack('<I', raw_len)
    if msg_len == 0:
        return None
    data = sys.stdin.buffer.read(msg_len)
    if not data:
        return None
    try:
        return json.loads(data.decode('utf-8'))
    except Exception:
        return None


def _connect_and_send(payload: dict, timeout: float = 2.0):
    # Open a socket to the GUI control server, send the payload and stream any
    # JSON-lines received back to the connected extension process.
    last = None
    try:
        s = socket.create_connection((HOST, PORT), timeout=timeout)
        try:
            s.sendall((json.dumps(payload) + '\n').encode('utf-8'))
            # Read repeatedly until the GUI closes the connection. Each line is
            # expected to be a JSON object followed by a newline. Forward each
            # parsed object to the browser extension via native messaging.
            s.settimeout(0.5)
            buf = b''
            while True:
                try:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                    while b'\n' in buf:
                        line, buf = buf.split(b'\n', 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line.decode('utf-8'))
                            last = obj
                            send_native_message(obj)
                        except Exception:
                            # ignore malformed lines
                            pass
                except socket.timeout:
                    # continue reading until closed
                    continue
        finally:
            try:
                s.close()
            except Exception:
                pass
    except Exception:
        pass
    return last or {"status": "queued"}

def _retry_connect(payload: dict, total_wait: float = 5.0):
    deadline = time.time() + total_wait
    attempt = 0
    last_err = None
    while time.time() < deadline:
        attempt += 1
        try:
            return _connect_and_send(payload, timeout=1.6)
        except Exception as e:
            last_err = e
            time.sleep(0.4)
    # If we never connected, propagate an error status (so extension can surface problem)
    return {"status": "error", "message": f"GUI unreachable after {attempt} attempts: {last_err}"}


def forward_to_gui(payload: dict) -> dict:
    """
    Forward a request to the GUI control server.

    Behaviour:
    - If a GUI instance is already listening on HOST:PORT, send the payload and
      stream responses back to the browser.
    - If not reachable, attempt to launch the GUI and then retry connecting for
      a short period.
    """
    # Quick reachability probe (separate from _connect_and_send, which swallows errors)
    try:
        s = socket.create_connection((HOST, PORT), timeout=0.2)
        try:
            s.close()
        except Exception:
            pass
        # Server is up; use the streaming helper
        return _connect_and_send(payload, timeout=0.2)
    except Exception:
        # Not reachable; try to launch the GUI
        try:
            launcher = '/usr/bin/fasttube-downloader'
            if os.path.exists(launcher) and os.access(launcher, os.X_OK):
                subprocess.Popen([launcher], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            else:
                # Fallback to running from source tree (development mode)
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                gui_path = os.path.join(script_dir, 'gui', 'main_window.py')
                subprocess.Popen(['python3', gui_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

            # After launching, wait a bit and retry connecting
            return _retry_connect(payload, total_wait=6.0)
        except Exception as e:
            return {"status": "error", "message": f"GUI launch failed: {e}"}


def main():
    while True:
        req = read_native_message()
        if req is None:
            break
        if not isinstance(req, dict):
            send_native_message({"status": "error", "message": "Invalid request"})
            continue
        # Handle probe request via yt-dlp JSON output
        if req.get('action') == 'probe' and req.get('url'):
            try:
                import subprocess, json as _json
                p = subprocess.run(['yt-dlp', '-J', '--no-warnings', '--no-playlist', req['url']], capture_output=True, text=True, timeout=15)
                if p.returncode != 0:
                    raise RuntimeError(p.stderr.strip() or 'yt-dlp failed')
                info = _json.loads(p.stdout)
                fmts = info.get('formats') or []
                heights = sorted({ f.get('height') for f in fmts if f.get('height') }, reverse=True)
                qualities = [h for h in heights if isinstance(h, int)]
                audio_only = any((f.get('vcodec') in (None, 'none')) for f in fmts)
                def _size_mb(f):
                    sz = f.get('filesize') or f.get('filesize_approx')
                    return round(sz/1024/1024, 1) if isinstance(sz, (int,float)) else None
                fmt_list = []
                for f in fmts:
                    fid = f.get('format_id')
                    if not fid:
                        continue
                    h = f.get('height')
                    ext = f.get('ext')
                    vcodec = f.get('vcodec')
                    acodec = f.get('acodec')
                    fps = f.get('fps')
                    size = _size_mb(f)
                    progressive = (vcodec not in (None,'none')) and (acodec not in (None,'none'))
                    fmt_list.append({
                        'id': str(fid),
                        'height': h,
                        'ext': ext,
                        'fps': fps,
                        'sizeMB': size,
                        'vcodec': vcodec,
                        'acodec': acodec,
                        'progressive': progressive
                    })
                send_native_message({ 'status': 'ok', 'qualities': qualities, 'audio_only': audio_only, 'formats': fmt_list })
            except Exception as e:
                send_native_message({ 'status': 'error', 'message': str(e) })
            continue

        # Normalize enqueue fields
        payload = {
            'action': 'enqueue',
            'url': req.get('url'),
            'title': req.get('title'),
            'format': req.get('format'),
            'formatId': req.get('formatId'),
            'quality': req.get('quality'),
            'subs': req.get('subs'),
            'show': True,
            'confirm': bool(req.get('confirm'))
        }
        if not payload['url']:
            send_native_message({"status": "error", "message": "No URL"})
            continue
        result = forward_to_gui(payload)
        send_native_message(result)


if __name__ == '__main__':
    main()
