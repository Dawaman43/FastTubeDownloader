#!/usr/bin/env python3
import os, sys, json, subprocess, threading, gi, re, urllib.request, urllib.parse, socket, time
from pathlib import Path
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
try:
    gi.require_version("Pango", "1.0")
except Exception:
    pass
try:
    gi.require_version("Notify", "0.7")
except Exception:
    pass
from gi.repository import Gtk, GLib, Gdk, Pango
try:
    from gi.repository import Notify; _HAS_NOTIFY = True
except Exception:
    _HAS_NOTIFY = False
try:
    from .playlist_utils import parse_flat_playlist_lines
except Exception:
    parse_flat_playlist_lines = None
try:
    from .file_organizer import FileOrganizer
except Exception:
    FileOrganizer = None

try:
    from .download_engine import get_engine
    DOWNLOAD_ENGINE = get_engine()
except Exception:
    DOWNLOAD_ENGINE = None

try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
except Exception:
    AppIndicator3 = None

GLib.set_application_name("FastTube Downloader")
try:
    Gdk.set_program_class("FastTubeDownloader")
except Exception:
    pass
try:
    GLib.set_prgname("fasttube-downloader")
except Exception:
    pass

CONFIG_DIR = os.path.expanduser("~/.config/FastTubeDownloader")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAST_YTDL_LOCAL = os.path.join(_BASE_DIR, "fast_ytdl.sh")
FAST_YTDL_ALT = "/opt/FastTubeDownloader/fast_ytdl.sh"
if os.path.exists(FAST_YTDL_LOCAL):
    try:
        st = os.stat(FAST_YTDL_LOCAL)
        if not (st.st_mode & 0o111):
            os.chmod(FAST_YTDL_LOCAL, st.st_mode | 0o755)
    except Exception:
        pass
    FAST_YTDL = FAST_YTDL_LOCAL
elif os.path.exists(FAST_YTDL_ALT):
    FAST_YTDL = FAST_YTDL_ALT
else:
    FAST_YTDL = FAST_YTDL_LOCAL

class DownloadItem:
    def __init__(self, url: str, title: str):
        self.url = url
        self.title = title or "Unknown"
        self.progress = 0
        self.status = "Queued"
        self.process = None
        self.dest_path = None
        self.treeiter = None
        self.kind = 'media'
        self.req_format = None
        self.req_quality = None
        self.req_subs = None
        self.speed = ''
        self.eta = ''
        self.total = ''
        self.downloaded = ''
        self.gid = None
        self.client_conn = None
        self.client_req_id = None

    def __repr__(self):
        return f"<DownloadItem {self.title!r} {self.progress}% {self.status}>"

class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="FastTube Downloader")
        self.set_border_width(10)
        try:
            icon_path = os.path.join(_BASE_DIR, 'icon128.png')
            if os.path.exists(icon_path):
                try:
                    Gtk.Window.set_default_icon_from_file(icon_path)
                except Exception:
                    pass
                self.set_icon_from_file(icon_path)
                try:
                    if hasattr(self, 'set_wmclass'):
                        self.set_wmclass("FastTubeDownloader", "FastTube Downloader")
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.set_resizable(True)
        except Exception:
            pass
        self._set_initial_window_size()
        self.config = self.load_config()
        if not self.config:
            try:
                setup_path = os.path.join(_BASE_DIR, "gui", "first_time_setup.py")
                subprocess.run([sys.executable, setup_path], check=False)
                self.config = self.load_config()
            except Exception:
                self.config = None
        if not self.config:
            self.config = {}
        self._apply_config_defaults()
        if FileOrganizer:
            self.file_organizer = FileOrganizer(self.config.get("download_folder"), self.config.get("category_mode", "idm"))
        else:
            self.file_organizer = None
        self.build_ui()
        # Tray icon and delete-event will be initialized in build_ui or after

    def _set_initial_window_size(self):
        try:
            sw, sh = self._get_screen_dimensions()
            cfg_w = int(self.config.get("window_width", 0)) if isinstance(getattr(self, 'config', {}), dict) else 0
            cfg_h = int(self.config.get("window_height", 0)) if isinstance(getattr(self, 'config', {}), dict) else 0
            if cfg_w > 0 and cfg_h > 0:
                w, h = cfg_w, cfg_h
            else:
                w = int(sw * 0.35)
                h = int(sh * 0.85)
            if w < 640: w = 640
            if h < 400: h = 400
            max_w = sw - 40
            max_h = sh - 60
            if w > max_w: w = max_w
            if h > max_h: h = max_h
            try:
                geom = Gdk.Geometry()
                geom.max_width = max_w
                geom.max_height = max_h
                self.set_geometry_hints(self, geom, Gdk.WindowHints.MAX_SIZE)
            except Exception:
                pass
            self.set_default_size(w, h)
            GLib.idle_add(lambda: (self.resize(w, h), False)[1])
            try:
                print(f"[GUI] Screen {sw}x{sh} -> initial {w}x{h} (max {max_w}x{max_h})")
            except Exception:
                pass
            try:
                self.set_position(Gtk.WindowPosition.CENTER)
            except Exception:
                pass
        except Exception:
            self.set_default_size(800, 500)
            
    def _get_screen_dimensions(self):
        try:
            display = Gdk.Display.get_default()
            if display:
                try:
                    monitor = display.get_primary_monitor()
                except Exception:
                    monitor = None
                if monitor:
                    try:
                        rect = monitor.get_workarea()
                    except Exception:
                        rect = monitor.get_geometry()
                    try:
                        scale = int(getattr(monitor, 'get_scale_factor', lambda: 1)()) or 1
                    except Exception:
                        scale = 1
                    return int(rect.width // scale), int(rect.height // scale)
        except Exception:
            pass
        try:
            scr = self.get_screen()
            return int(scr.get_width()), int(scr.get_height())
        except Exception:
            return 1024, 768

    def _apply_config_defaults(self):
        defaults = {
            "download_folder": os.path.expanduser("~/Downloads"),
            "default_format": "Best (default)",
            "preferred_quality": "",
            "subs": False,
            "clipboard_auto": False,
            "speed_limit_kbps": "",
            "max_concurrent": 2,
            "aria_connections": 32,
            "aria_splits": 32,
            "fragment_concurrency": 16,
            "category_mode": "idm",
            "show_big_popup": False,  # Disabled annoying flashing popup
            "enable_generic": True,
            "aria2_rpc_enabled": False,
            "aria2_rpc_port": 6800,
            "minimize_to_tray": True,
            "auto_start": True,
            "generic_extensions_map": {
                "Videos": [".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".wmv"],
                "Music": [".mp3", ".m4a", ".aac", ".flac", ".wav", ".ogg"],
                "Pictures": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
                "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"],
                "Archives": [".zip", ".rar", ".7z", ".tar", ".tar.gz", ".tgz", ".tar.bz2"],
                "ISO": [".iso", ".img"],
                "Other": []
            }
        }
        if not isinstance(self.config, dict):
            self.config = {}
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        self.config["download_folder"] = os.path.expanduser(self.config.get("download_folder", "~/Downloads"))
        try:
            self.config["aria_connections"] = int(self.config.get("aria_connections", 32))
        except Exception:
            self.config["aria_connections"] = 32
        if self.config["aria_connections"] < 1:
            self.config["aria_connections"] = 1
        if self.config["aria_connections"] > 16:
            self.config["aria_connections"] = 16
        try:
            self.config["aria_splits"] = int(self.config.get("aria_splits", 32))
        except Exception:
            self.config["aria_splits"] = 32
        try:
            self.config["fragment_concurrency"] = int(self.config.get("fragment_concurrency", 16))
        except Exception:
            self.config["fragment_concurrency"] = 16
        if self.config.get("category_mode") not in ("idm", "flat"):
            self.config["category_mode"] = "idm"
            
        # FORCE disable annoying popup for v2
        self.config["show_big_popup"] = False
        
        os.makedirs(self.config["download_folder"], exist_ok=True)

    def build_ui(self):
        self.set_title("FastTube Downloader")
        try:
            header = Gtk.HeaderBar()
            header.set_show_close_button(True)
            header.props.title = "FastTube Downloader"
            self.set_titlebar(header)
            refresh_btn = Gtk.Button.new_from_icon_name("view-refresh", Gtk.IconSize.BUTTON)
            refresh_btn.set_tooltip_text("Refresh queue progress")
            refresh_btn.connect("clicked", lambda *_: self.update_dashboard_counts())
            header.pack_start(refresh_btn)
            stats_btn = Gtk.Button(label="Dashboard")
            stats_btn.connect("clicked", lambda *_: self.notebook.set_current_page(0))
            header.pack_end(stats_btn)
        except Exception:
            pass

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.header_box.set_border_width(12)
        self.lbl_counts = Gtk.Label(label="Queued: 0 | Downloading: 0 | Completed: 0")
        self.lbl_counts.get_style_context().add_class("fasttube-header")
        self.header_box.pack_start(self.lbl_counts, False, False, 0)
        vbox.pack_start(self.header_box, False, False, 0)

        self.notebook = Gtk.Notebook()
        vbox.pack_start(self.notebook, True, True, 0)

        queue_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        hbox_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.url_entry = Gtk.Entry(placeholder_text="Paste YouTube URL here...")
        self.url_entry.set_hexpand(True)
        add_btn = Gtk.Button(label="Add to Queue")
        add_btn.get_style_context().add_class("suggested-action")
        add_btn.connect("clicked", self.on_add_download)
        start_btn = Gtk.Button(label="Start Downloads")
        start_btn.get_style_context().add_class("suggested-action")
        start_btn.connect("clicked", self.on_start_downloads)
        stop_btn = Gtk.Button(label="Stop")
        stop_btn.connect("clicked", self.on_stop_downloads)
        clear_btn = Gtk.Button(label="Clear Queue")
        clear_btn.get_style_context().add_class("destructive-action")
        clear_btn.connect("clicked", self.clear_queue)
        remove_btn = Gtk.Button(label="Remove Selected")
        remove_btn.get_style_context().add_class("destructive-action")
        remove_btn.connect("clicked", self.on_remove_selected)
        pause_btn = Gtk.Button(label="Pause Selected")
        pause_btn.connect("clicked", self.on_pause_selected)
        resume_btn = Gtk.Button(label="Resume Selected")
        resume_btn.connect("clicked", self.on_resume_selected)
        open_folder_btn = Gtk.Button(label="Open Folder")
        open_folder_btn.connect("clicked", self.on_open_folder)
        hbox_top.pack_start(self.url_entry, True, True, 0)
        hbox_top.pack_start(add_btn, False, False, 0)
        hbox_top.pack_start(start_btn, False, False, 0)
        hbox_top.pack_start(stop_btn, False, False, 0)
        hbox_top.pack_start(remove_btn, False, False, 0)
        hbox_top.pack_start(pause_btn, False, False, 0)
        hbox_top.pack_start(resume_btn, False, False, 0)
        hbox_top.pack_start(open_folder_btn, False, False, 0)
        hbox_top.pack_start(clear_btn, False, False, 0)
        queue_page.pack_start(hbox_top, False, False, 0)

        self.settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.settings_box.get_style_context().add_class("settings-strip")
        self.format_combo = Gtk.ComboBoxText()
        for opt in ("Best Video + Audio", "Audio Only", "Best (default)", "Generic File"):
            self.format_combo.append_text(opt)
        fmt_idx = {"Best Video + Audio": 0, "Audio Only": 1, "Best (default)": 2, "Generic File": 3}.get(self.config.get("default_format"), 2)
        self.format_combo.set_active(fmt_idx)
        self.format_combo.connect("changed", self.on_format_changed)
        self.quality_entry = Gtk.Entry()
        self.quality_entry.set_placeholder_text(self.config.get("preferred_quality", "1080"))
        if self.config.get("preferred_quality"):
            self.quality_entry.set_text(str(self.config.get("preferred_quality")))
        self.subs_check = Gtk.CheckButton(label="Subtitles")
        self.subs_check.set_active(self.config.get("subs", False))
        self.clipboard_check = Gtk.CheckButton(label="Auto-add from Clipboard")
        self.clipboard_check.set_active(self.config.get("clipboard_auto", False))
        self.speed_entry = Gtk.Entry()
        self.speed_entry.set_placeholder_text("Speed limit KB/s (empty = unlimited)")
        if self.config.get("speed_limit_kbps"):
            self.speed_entry.set_text(str(self.config.get("speed_limit_kbps")))
        save_defaults_btn = Gtk.Button(label="Save Defaults")
        save_defaults_btn.connect("clicked", self.on_save_defaults)
        change_folder_btn = Gtk.Button(label="Change Folder")
        change_folder_btn.connect("clicked", self.on_change_folder)

        self.settings_box.pack_start(Gtk.Label(label="Format:"), False, False, 0)
        self.settings_box.pack_start(self.format_combo, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Quality:"), False, False, 0)
        self.settings_box.pack_start(self.quality_entry, False, False, 0)
        self.settings_box.pack_start(self.subs_check, False, False, 0)
        self.settings_box.pack_start(self.clipboard_check, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Speed KB/s:"), False, False, 0)
        self.settings_box.pack_start(self.speed_entry, False, False, 0)
        self.conn_adj = Gtk.Adjustment(value=float(self.config.get("aria_connections", 16)), lower=1, upper=16, step_increment=1, page_increment=4)
        self.conn_spin = Gtk.SpinButton()
        self.conn_spin.set_adjustment(self.conn_adj)
        self.conn_spin.set_numeric(True)
        self.split_adj = Gtk.Adjustment(value=float(self.config.get("aria_splits", 32)), lower=4, upper=64, step_increment=1, page_increment=4)
        self.split_spin = Gtk.SpinButton()
        self.split_spin.set_adjustment(self.split_adj)
        self.split_spin.set_numeric(True)
        self.frag_adj = Gtk.Adjustment(value=float(self.config.get("fragment_concurrency", 16)), lower=1, upper=32, step_increment=1, page_increment=2)
        self.frag_spin = Gtk.SpinButton()
        self.frag_spin.set_adjustment(self.frag_adj)
        self.frag_spin.set_numeric(True)
        self.category_combo = Gtk.ComboBoxText()
        self.category_combo.append("idm", "Categorized (videos/audio)")
        self.category_combo.append("flat", "Single folder")
        self.category_combo.set_active_id(self.config.get("category_mode", "idm"))
        self.max_concurrent_adj = Gtk.Adjustment(value=float(self.config.get("max_concurrent", 2)), lower=1, upper=10, step_increment=1, page_increment=1)
        self.max_concurrent_spin = Gtk.SpinButton()
        self.max_concurrent_spin.set_adjustment(self.max_concurrent_adj)
        self.max_concurrent_spin.set_numeric(True)
        self.settings_box.pack_start(Gtk.Label(label="Connections:"), False, False, 0)
        self.settings_box.pack_start(self.conn_spin, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Splits:"), False, False, 0)
        self.settings_box.pack_start(self.split_spin, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Fragments:"), False, False, 0)
        self.settings_box.pack_start(self.frag_spin, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Folders:"), False, False, 0)
        self.settings_box.pack_start(self.category_combo, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Max concurrent:"), False, False, 0)
        self.settings_box.pack_start(self.max_concurrent_spin, False, False, 0)
        self.settings_box.pack_start(save_defaults_btn, False, False, 0)
        self.settings_box.pack_start(change_folder_btn, False, False, 0)
        sc_settings = Gtk.ScrolledWindow()
        sc_settings.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        sc_settings.set_hexpand(True)
        sc_settings.add(self.settings_box)
        sc_settings.set_min_content_height(70)
        queue_page.pack_start(sc_settings, False, False, 0)

        self.liststore = Gtk.ListStore(str, str, int, str, str, str, str, str)
        self.treeview = Gtk.TreeView(model=self.liststore)
        self.treeview.set_rules_hint(True)
        title_renderer = Gtk.CellRendererText()
        try:
            title_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        except Exception:
            pass
        title_col = Gtk.TreeViewColumn(title="Title")
        title_col.set_resizable(True)
        title_col.set_min_width(200)
        title_col.pack_start(title_renderer, True)
        title_col.add_attribute(title_renderer, 'text', 1)
        self.treeview.append_column(title_col)
        
        prog_renderer = Gtk.CellRendererProgress()
        prog_col = Gtk.TreeViewColumn(title="Progress")
        prog_col.set_min_width(120)
        prog_col.pack_start(prog_renderer, True)
        prog_col.add_attribute(prog_renderer, 'value', 2)
        prog_col.add_attribute(prog_renderer, 'text', 3)
        self.treeview.append_column(prog_col)
        
        status_renderer = Gtk.CellRendererText()
        status_col = Gtk.TreeViewColumn(title="Status")
        status_col.set_min_width(100)
        status_col.pack_start(status_renderer, True)
        status_col.set_cell_data_func(status_renderer, self._status_cell_data_func)
        self.treeview.append_column(status_col)

        speed_renderer = Gtk.CellRendererText()
        speed_col = Gtk.TreeViewColumn(title="Speed")
        speed_col.pack_start(speed_renderer, True)
        speed_col.add_attribute(speed_renderer, 'text', 5)
        self.treeview.append_column(speed_col)

        eta_renderer = Gtk.CellRendererText()
        eta_col = Gtk.TreeViewColumn(title="ETA")
        eta_col.pack_start(eta_renderer, True)
        eta_col.add_attribute(eta_renderer, 'text', 6)
        self.treeview.append_column(eta_col)

        size_renderer = Gtk.CellRendererText()
        size_col = Gtk.TreeViewColumn(title="Size")
        size_col.pack_start(size_renderer, True)
        size_col.add_attribute(size_renderer, 'text', 7)
        self.treeview.append_column(size_col)
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.treeview)
        queue_page.pack_start(scrolled, True, True, 0)
        self.notebook.append_page(queue_page, Gtk.Label(label="Queue"))

        history_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        hist_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_hist_open = Gtk.Button(label="Open File")
        btn_hist_open.connect("clicked", self.on_hist_open_file)
        btn_hist_folder = Gtk.Button(label="Open Folder")
        btn_hist_folder.connect("clicked", self.on_hist_open_folder)
        btn_hist_retry = Gtk.Button(label="Retry")
        btn_hist_retry.connect("clicked", self.on_hist_retry)
        btn_hist_clear = Gtk.Button(label="Clear History")
        btn_hist_clear.connect("clicked", self.on_hist_clear)
        hist_actions.pack_start(btn_hist_open, False, False, 0)
        hist_actions.pack_start(btn_hist_folder, False, False, 0)
        hist_actions.pack_start(btn_hist_retry, False, False, 0)
        hist_actions.pack_end(btn_hist_clear, False, False, 0)
        history_page.pack_start(hist_actions, False, False, 0)

        self.hist_store = Gtk.ListStore(str, str, str, str, str)
        self.hist_view = Gtk.TreeView(model=self.hist_store)
        for (title_txt, idx) in [("Time", 0), ("Title", 1), ("Status", 2), ("Path", 3)]:
            r = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(title=title_txt)
            col.pack_start(r, True)
            col.add_attribute(r, 'text', idx)
            self.hist_view.append_column(col)
        sc_hist = Gtk.ScrolledWindow()
        sc_hist.add(self.hist_view)
        history_page.pack_start(sc_hist, True, True, 0)
        self.notebook.append_page(history_page, Gtk.Label(label="History"))

        help_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        help_page.set_border_width(10)
        help_scrolled = Gtk.ScrolledWindow()
        help_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        help_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        help_scrolled.add(help_vbox)

        def _make_block(title, body_lines):
            frame = Gtk.Frame()
            frame.set_shadow_type(Gtk.ShadowType.IN)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.set_border_width(8)
            title_lbl = Gtk.Label(label=title)
            title_lbl.set_xalign(0.0)
            title_lbl.get_style_context().add_class("help-title")
            body_lbl = Gtk.Label(label="\n".join(body_lines))
            body_lbl.set_xalign(0.0)
            body_lbl.set_selectable(True)
            body_lbl.set_line_wrap(True)
            body_lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            box.pack_start(title_lbl, False, False, 0)
            box.pack_start(body_lbl, False, False, 0)
            frame.add(box)
            return frame, body_lbl

        chrome_ext_dir = os.path.join(_BASE_DIR)
        firefox_ext_dir = os.path.join(_BASE_DIR)
        unpack_paths = [chrome_ext_dir, firefox_ext_dir]
        manifest_hint = os.path.join(_BASE_DIR, 'manifest.json')
        native_host_path = os.path.join(_BASE_DIR, 'native_host', 'com.fasttube.downloader.json')

        blocks = [
            ("Quick Start", [
                "1. Paste a YouTube link and press 'Add to Queue'.",
                "2. Press 'Start Downloads' to begin.",
                "3. Use 'Pause', 'Resume', or 'Remove Selected' as needed.",
                "4. Generic File: choose 'Generic File' format before adding a direct URL (e.g. .zip, .mp4)."
            ]),
            ("Formats", [
                "Best Video + Audio: Merges highest quality video+audio.",
                "Audio Only: Extracts best available audio track.",
                "Best (default): Lets yt-dlp decide optimal stream.",
                "Generic File: Direct file download via aria2c (or future fallback)."
            ]),
            ("Speed & Concurrency", [
                "Speed KB/s: Limit overall download rate; empty = unlimited.",
                "Connections / Splits (generic): Parallel segments (aria2).",
                "Max concurrent: Number of active items in queue simultaneously." 
            ]),
            ("Subtitles & Quality", [
                "Quality: Enter resolution (e.g. 1080, 720). Empty = best.",
                "Subtitles: Attempts to include available subtitles if enabled." 
            ]),
            ("Clipboard Auto-Add", [
                "When enabled, copying a supported URL auto-enqueues it.",
                "Recognizes YouTube watch, playlist, shorts, youtu.be links and many direct file URLs." 
            ]),
            ("Download Folder", [
                f"Current: {self.config.get('download_folder')}",
                "Change Folder: Sets new base destination.",
                "Categorized mode: Places files into subfolders (Videos, Music, etc).",
                "Flat mode: Everything in one folder." 
            ]),
            ("Extension (Chrome)", [
                "1. Open Chrome -> Extensions -> Enable Developer Mode.",
                "2. Click 'Load unpacked'.",
                f"3. Select project root containing manifest.json: {manifest_hint}",
                "4. Extension icon appears; open the popup to send URLs.",
                "5. If GUI closed, loading a URL will raise it (native messaging)." 
            ]),
            ("Extension (Firefox)", [
                "1. Open about:debugging -> This Firefox -> 'Load Temporary Add-on'.",
                f"2. Select manifest.json from project root: {manifest_hint}",
                "3. For permanent install, package and sign (future step).",
                "4. Native host JSON must be in ~/.mozilla/native-messaging-hosts (setup script will automate)." 
            ]),
            ("Native Messaging Host", [
                f"Spec file: {native_host_path}",
                "Allows browser extension to enqueue downloads and raise GUI.",
                "Setup script registers host path automatically for Chrome; Firefox path coming soon." 
            ]),
            ("Where Things Are", [
                f"Config: {CONFIG_FILE}",
                f"History: {HISTORY_FILE}",
                f"Fast script: {FAST_YTDL}",
                f"Icon: {os.path.join(_BASE_DIR,'icon128.png')}",
                f"Extension root: {_BASE_DIR}" 
            ]),
            ("Copy Paths", [
                "Use buttons below to copy frequently needed directories." 
            ])
        ]

        copy_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        path_map = {
            "Config": CONFIG_FILE,
            "History": HISTORY_FILE,
            "Extension Root": _BASE_DIR,
            "Native Host": native_host_path,
            "Manifest": manifest_hint
        }
        def _copy_path(_btn, p):
            try:
                self.clipboard.set_text(p, -1)
            except Exception:
                pass
        for label, pth in path_map.items():
            btn = Gtk.Button(label=f"Copy {label}")
            btn.connect("clicked", lambda b, p=pth: _copy_path(b, p))
            copy_buttons_box.pack_start(btn, False, False, 0)

        for title, body in blocks:
            frame, body_lbl = _make_block(title, body)
            help_vbox.pack_start(frame, False, False, 0)
        help_vbox.pack_start(copy_buttons_box, False, False, 0)
        help_page.pack_start(help_scrolled, True, True, 0)
        self.notebook.append_page(help_page, Gtk.Label(label="Help"))

        self.queue = []
        self.is_downloading = False
        self.already_seen_urls = set()
        self._last_clip_text = ""
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._mini_popup = None
        self._mini_title_lbl = None
        self._mini_status_lbl = None
        self._mini_progress_bar = None
        self._mini_idx = None
        self._big_popup = None
        self._big_list = None
        self._big_rows = {}
        self._big_header_label = None
        self.history = self.load_history()
        self.populate_history_view()

        targets = [Gtk.TargetEntry.new("text/uri-list", 0, 0), Gtk.TargetEntry.new("text/plain", 0, 1)]
        self.treeview.drag_dest_set(Gtk.DestDefaults.ALL, targets, Gdk.DragAction.COPY)
        self.treeview.connect("drag-data-received", self.on_drag_data_received)
        self.treeview.connect("button-press-event", self.on_treeview_button_press)

        GLib.timeout_add_seconds(2, self.check_clipboard_periodic)
        self.show_all()
        GLib.idle_add(self._enforce_max_window_size)
        try:
            self._clamp_checks_left = 10
        except Exception:
            self._clamp_checks_left = 0
        GLib.timeout_add(200, self._clamp_window_size_periodic)
        self.update_dashboard_counts()
        # CSS styling is now applied later        self.update_dashboard_counts()
        GLib.timeout_add(2000, self.check_clipboard_periodic)
        threading.Thread(target=self._start_control_server, daemon=True).start()
        
        # Initialize tray icon and set up window close behavior
        # Temporarily disabled due to segfault - will fix in next update
        # self._init_tray_icon()
        # self.connect("delete-event", self.on_delete_event)
        self.connect("configure-event", self._on_configure)
        try:
            self.on_format_changed(self.format_combo)
        except Exception:
            pass

    def _status_cell_data_func(self, column, cell, model, iter, data):
        status = model.get_value(iter, 4)
        cell.set_property('text', status)
        if status == 'Downloading...':
            cell.set_property('foreground', '#3d8bfd')
        elif status == 'Completed':
            cell.set_property('foreground', '#28a745')
        elif status == 'Paused':
            cell.set_property('foreground', '#ffc107')
        elif 'Error' in status or 'Failed' in status:
            cell.set_property('foreground', '#dc3545')
        else:
            cell.set_property('foreground', '#a8b3c1')

    def on_format_changed(self, combo):
        try:
            fmt = combo.get_active_text() or ''
            is_generic = (fmt == 'Generic File')
            self.quality_entry.set_sensitive(not is_generic)
            self.subs_check.set_sensitive(not is_generic)
        except Exception:
            pass

    def _enforce_max_window_size(self):
        try:
            sw, sh = self._get_screen_dimensions()
            max_w = int(sw) - 40
            max_h = int(sh) - 60
            try:
                geom_w, geom_h = self.get_size()
            except Exception:
                geom_w = self.get_allocated_width()
                geom_h = self.get_allocated_height()
            new_w = min(geom_w, max_w)
            new_h = min(geom_h, max_h)
            if new_w != geom_w or new_h != geom_h:
                self.resize(new_w, new_h)
        except Exception:
            pass
        return False

    def _on_configure(self, widget, event):
        try:
            sw, sh = self._get_screen_dimensions()
            max_w = int(sw) - 40
            max_h = int(sh) - 60
            try:
                geom_w, geom_h = self.get_size()
            except Exception:
                geom_w = widget.get_allocated_width()
                geom_h = widget.get_allocated_height()
            if geom_w > max_w or geom_h > max_h:
                widget.resize(min(geom_w, max_w), min(geom_h, max_h))
            try:
                if not hasattr(self, '_size_save_pending') or not self._size_save_pending:
                    self._size_save_pending = True
                    def _save_size():
                        try:
                            w, h = self.get_size()
                            if isinstance(self.config, dict):
                                self.config['window_width'] = int(w)
                                self.config['window_height'] = int(h)
                                os.makedirs(CONFIG_DIR, exist_ok=True)
                                with open(CONFIG_FILE, 'w') as f:
                                    json.dump(self.config, f, indent=4)
                        except Exception:
                            pass
                        finally:
                            self._size_save_pending = False
                        return False
                    GLib.timeout_add(400, _save_size)
            except Exception:
                pass
        except Exception:
            pass
        return False

    def _clamp_window_size_periodic(self):
        try:
            if getattr(self, '_clamp_checks_left', 0) <= 0:
                return False
            self._clamp_checks_left -= 1
            self._enforce_max_window_size()
        except Exception:
            return False
        return True

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return None

    def load_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    return json.load(f) or []
        except Exception:
            pass
        return []

    def save_history(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def populate_history_view(self):
        self.hist_store.clear()
        for rec in self.history:
            self.hist_store.append([
                rec.get('time',''),
                rec.get('title','Unknown'),
                rec.get('status',''),
                rec.get('path',''),
                rec.get('url',''),
            ])

    def append_history(self, title, url, status, path):
        import datetime
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rec = { 'time': ts, 'title': title or 'Unknown', 'url': url, 'status': status, 'path': path or '' }
        self.history.append(rec)
        self.save_history()
        self.hist_store.append([rec['time'], rec['title'], rec['status'], rec['path'], rec['url']])
        self.update_dashboard_counts()

    def update_dashboard_counts(self):
        queued = sum(1 for it in self.queue if it.status == 'Queued')
        downloading = sum(1 for it in self.queue if it.status == 'Downloading...')
        completed = sum(1 for rec in self.history if rec.get('status') == 'Completed')
        try:
            self.lbl_counts.set_text(f"Queued: {queued} | Downloading: {downloading} | Completed: {completed}")
        except Exception:
            pass

    def _get_selected_history(self):
        sel = self.hist_view.get_selection()
        model, itr = sel.get_selected()
        if itr is None:
            return None
        time_s, title, status, path, url = model[itr]
        return { 'time': time_s, 'title': title, 'status': status, 'path': path, 'url': url, 'iter': itr }

    def on_hist_open_file(self, widget):
        rec = self._get_selected_history()
        if not rec or not rec['path']:
            return
        try:
            subprocess.Popen(["xdg-open", rec['path']])
        except Exception as e:
            self.show_message(f"Unable to open file: {e}")

    def on_hist_open_folder(self, widget):
        rec = self._get_selected_history()
        if not rec:
            return
        path = rec['path']
        folder = os.path.dirname(path) if path else os.path.expanduser(self.config.get("download_folder", "~"))
        try:
            subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            self.show_message(f"Unable to open folder: {e}")

    def on_hist_retry(self, widget):
        rec = self._get_selected_history()
        if not rec or not rec['url']:
            return
        self.add_url(rec['url'])
        if not self.is_downloading:
            self.on_start_downloads(None)
        self.notebook.set_current_page(0)

    def on_hist_clear(self, widget):
        self.history = []
        self.save_history()
        self.populate_history_view()
        self.update_dashboard_counts()

    def on_setup_complete(self, widget):
        self.config = self.load_config()
        if self.config:
            for child in self.get_children():
                self.remove(child)
            self.build_ui()
            self.show_all()

    def get_video_title(self, url):
        try:
            oembed_url = "https://www.youtube.com/oembed?%s" % urllib.parse.urlencode({
                "url": url,
                "format": "json"
            })
            req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                title = (data.get("title") or "").strip()
                if title:
                    return title
        except Exception:
            pass
        try:
            result = subprocess.run(["yt-dlp", "--no-playlist", "--get-title", url], capture_output=True, text=True, check=True, timeout=45)
            title = result.stdout.strip()
            return next((line for line in title.splitlines() if line.strip()), "Unknown") or "Unknown"
        except Exception as e:
            print(f"Title fetch error: {e}")
            return "Unknown"

    def fetch_title_background(self, item):
        try:
            result = subprocess.run(["yt-dlp", "--no-playlist", "--get-title", item.url], capture_output=True, text=True, check=True, timeout=45)
            title = result.stdout.strip()
            title = next((line for line in title.splitlines() if line.strip()), None)
            if title:
                try:
                    idx = self.queue.index(item)
                except ValueError:
                    return
                self.update_title(idx, title)
        except Exception:
            pass

    def on_add_download(self, widget):
        url = self.url_entry.get_text().strip()
        if not url:
            self.show_message("Please enter a URL!")
            return
        self.add_url(url)
        self.url_entry.set_text("")

    def add_url(self, url: str, fmt: str = None, qual: str = None, subs_active: bool = None):
        try:
            if self._is_playlist_url(url):
                self.add_playlist(url)
                return
        except Exception:
            pass
        try:
            if self.config.get("enable_generic", True):
                chosen_fmt = fmt or self.format_combo.get_active_text()
                if chosen_fmt == 'Generic File' or self._looks_like_direct_file(url):
                    self.add_generic_file(url)
                    return
        except Exception:
            pass
        item = DownloadItem(url, "Fetching title...")
        item.kind = 'media'
        item.req_format = fmt or self.format_combo.get_active_text()
        print(f"[GUI] queued media URL {url}", file=sys.stderr)
        item.req_quality = qual or (self.quality_entry.get_text() or "")
        if subs_active is None:
            subs_active = self.subs_check.get_active()
        item.req_subs = subs_active
        self.queue.append(item)
        item.treeiter = self.liststore.append([item.url, item.title, item.progress, f"{item.progress}%", item.status, "", "", ""])
        threading.Thread(target=self.fetch_title_background, args=(item,), daemon=True).start()
        if self.config.get("auto_start", True) and not self.is_downloading:
            self.on_start_downloads(None)

    def add_playlist(self, url):
        probe_cmd = ["yt-dlp", "--flat-playlist", "--dump-json", url]
        added = 0
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().splitlines()
            urls = []
            if parse_flat_playlist_lines:
                urls = parse_flat_playlist_lines(lines)
            else:
                seen_ids = set()
                for raw in lines:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        data = json.loads(raw)
                    except Exception:
                        continue
                    vid_id = data.get('id') or data.get('url')
                    if not vid_id or vid_id in seen_ids:
                        continue
                    seen_ids.add(vid_id)
                    urls.append(f"https://www.youtube.com/watch?v={vid_id}")
            if not urls:
                self.show_message("Playlist appears empty or inaccessible.")
                return
            for full_url in urls:
                item = DownloadItem(full_url, "Fetching title...")
                item.kind = 'media'
                self.queue.append(item)
                item.treeiter = self.liststore.append([item.url, item.title, item.progress, f"{item.progress}%", item.status, "", "", ""])
                threading.Thread(target=self.fetch_title_background, args=(item,), daemon=True).start()
                added += 1
            if self.config.get("auto_start", True) and not self.is_downloading:
                self.on_start_downloads(None)
        except subprocess.CalledProcessError:
            self.show_message("Error detecting playlist; treating as single video.")
            self.add_url(url)

    def _is_playlist_url(self, url: str) -> bool:
        try:
            p = urllib.parse.urlparse(url)
            netloc = (p.netloc or '').lower()
            path = (p.path or '').lower()
            qs = urllib.parse.parse_qs(p.query or '')

            def has_video_id() -> bool:
                if qs.get('v') and qs['v'][0].strip():
                    return True
                seg = path.strip('/')
                if 'youtu.be' in netloc and seg and not seg.startswith('playlist'):
                    return True
                if '/shorts/' in path:
                    return True
                return False

            if 'youtube.com' in netloc and path.startswith('/playlist'):
                return True
            if 'list' in qs and not has_video_id():
                return True
        except Exception:
            pass
        return False

    def _looks_like_direct_file(self, url: str) -> bool:
        try:
            p = urllib.parse.urlparse(url)
            path = p.path or ''
            path = path.rstrip('/')
            if not path:
                return False
            _, ext = os.path.splitext(path.lower())
            if not ext:
                return False
            for exts in self.config.get('generic_extensions_map', {}).values():
                if ext in exts:
                    return True
            return False
        except Exception:
            return False

    def _guess_filename(self, url: str) -> str:
        try:
            p = urllib.parse.urlparse(url)
            name = os.path.basename(p.path) or 'download'
            if '?' in name:
                name = name.split('?',1)[0]
            return name
        except Exception:
            return 'download'

    def add_generic_file(self, url: str):
        title = self._guess_filename(url)
        item = DownloadItem(url, title)
        item.kind = 'generic'
        item.req_format = 'Generic File'
        self.queue.append(item)
        item.treeiter = self.liststore.append([item.url, item.title, item.progress, f"{item.progress}%", item.status, "", "", ""])
        threading.Thread(target=self._probe_generic_metadata, args=(item,), daemon=True).start()
        if self.config.get("auto_start", True) and not self.is_downloading:
            self.on_start_downloads(None)

    def _probe_generic_metadata(self, item):
        import urllib.request
        try:
            req = urllib.request.Request(item.url, method='HEAD', headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                disp = resp.headers.get('Content-Disposition','')
                if 'filename=' in disp:
                    fn = disp.split('filename=')[1].strip('"')
                    if fn:
                        self._update_item_title(item, fn)
                clen = resp.headers.get('Content-Length')
                if clen and clen.isdigit():
                    sz = int(clen)
                    units = ['B','KiB','MiB','GiB','TiB']
                    u = 0
                    val = float(sz)
                    while val >= 1024 and u < len(units)-1:
                        val /= 1024.0; u += 1
                    item.total = f"{val:.1f}{units[u]}"
                    self._update_progress_text(item)
        except Exception:
            pass

    def on_start_downloads(self, widget):
        if self.is_downloading:
            return
        self.is_downloading = True
        threading.Thread(target=self._spooler, daemon=True).start()

    def on_stop_downloads(self, widget):
        self.is_downloading = False
        for item in self.queue:
            if item.process and item.process.poll() is None:
                try:
                    item.process.terminate()
                except Exception:
                    pass
        for it in self.queue:
            if it.status == "Downloading...":
                it.status = "Paused"
                if it.treeiter:
                    self.liststore.set(it.treeiter, 4, "Paused")
        self.update_dashboard_counts()

    def on_remove_selected(self, widget):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        url = model[treeiter][0]
        for i, qi in enumerate(list(self.queue)):
            if qi.url == url:
                if qi.process and qi.process.poll() is None:
                    try:
                        qi.process.terminate()
                    except Exception:
                        pass
                self.queue.pop(i)
                break
        self.liststore.remove(treeiter)
        self.update_dashboard_counts()

    def on_open_folder(self, widget):
        folder = os.path.expanduser(self.config.get("download_folder", "~"))
        try:
            subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            self.show_message(f"Unable to open folder: {e}")

    def on_save_defaults(self, widget):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.config["default_format"] = self.format_combo.get_active_text()
        self.config["preferred_quality"] = self.quality_entry.get_text()
        self.config["subs"] = self.subs_check.get_active()
        self.config["clipboard_auto"] = self.clipboard_check.get_active()
        sp = self.speed_entry.get_text().strip()
        self.config["speed_limit_kbps"] = int(sp) if sp.isdigit() else ""
        self.config["max_concurrent"] = int(self.max_concurrent_spin.get_value())
        self.config["aria_connections"] = int(self.conn_spin.get_value())
        self.config["aria_splits"] = int(self.split_spin.get_value())
        self.config["fragment_concurrency"] = int(self.frag_spin.get_value())
        active_id = self.category_combo.get_active_id() or "idm"
        self.config["category_mode"] = active_id
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=4)
        self.show_message("Defaults saved.")

    def on_change_folder(self, widget):
        dialog = Gtk.FileChooserDialog(title="Select Download Folder", parent=self,
                                       action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           "Select", Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            folder = os.path.expanduser(folder)
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as exc:
                self.show_message(f"Unable to use folder: {exc}")
                dialog.destroy()
                return
            self.config["download_folder"] = folder
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        dialog.destroy()
        self.update_dashboard_counts()

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        text = data.get_text() if data else None
        if not text:
            drag_context.finish(False, False, time)
            return
        urls = []
        for token in re.split(r"[\s\r\n]+", text.strip()):
            if token.startswith("http://") or token.startswith("https://"):
                urls.append(token)
        for u in urls:
            self.add_url(u)
        drag_context.finish(True, False, time)
        self.update_dashboard_counts()

    def on_treeview_button_press(self, widget, event):
        if event.button == 3:
            selection = self.treeview.get_selection()
            model, treeiter = selection.get_selected()
            menu = Gtk.Menu()
            copy_item = Gtk.MenuItem(label="Copy URL")
            open_folder_item = Gtk.MenuItem(label="Open Folder")
            copy_item.connect("activate", lambda *_: self.copy_selected_url())
            open_folder_item.connect("activate", self.on_open_folder)
            menu.append(copy_item)
            menu.append(open_folder_item)
            menu.show_all()
            try:
                menu.popup_at_pointer(event)
            except Exception:
                menu.popup(None, None, None, None, event.button, event.time)
            return True
        return False

    def copy_selected_url(self):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        url = model[treeiter][0]
        self.clipboard.set_text(url, -1)

    def check_clipboard_periodic(self):
        if not self.clipboard_check.get_active():
            return True
        try:
            def _on_text(clip, text):
                try:
                    text = text or ""
                    if text and text != self._last_clip_text:
                        self._last_clip_text = text
                        m = re.search(r"https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=[^\s&]+|playlist\?list=[^\s&]+)|youtu\.be/[^\s&]+)", text)
                        url = None
                        if m:
                            url = m.group(0)
                        else:
                            gm = re.search(r"https?://[^\s]+\.(?:zip|rar|7z|tar|gz|tar\.gz|tgz|bz2|iso|img|pdf|docx?|xlsx?|pptx?|mp3|m4a|aac|flac|wav|ogg|mp4|mkv|webm|avi|mov|flv|wmv|jpg|jpeg|png|gif|bmp|webp)(?:\?[^\s]*)?", text, re.IGNORECASE)
                            if gm:
                                url = gm.group(0)
                        if url and url not in self.already_seen_urls:
                            self.already_seen_urls.add(url)
                            self.add_url(url)
                            self.update_dashboard_counts()
                except Exception:
                    pass
            self.clipboard.request_text(_on_text)
        except Exception:
            pass
        return True

    def _start_control_server(self):
        HOST, PORT = '127.0.0.1', 47653
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((HOST, PORT))
            sock.listen(5)
        except Exception as e:
            print(f"Control server bind failed: {e}")
            return
        print(f"Control server listening on {HOST}:{PORT}")
        while True:
            try:
                conn, _ = sock.accept()
            except Exception:
                break
            threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def _handle_client(self, conn):
        try:
            conn.settimeout(5.0)
            buf = b''
            while b'\n' not in buf and len(buf) < 65536:
                try:
                    chunk = conn.recv(4096)
                except socket.timeout:
                    break
                if not chunk:
                    break
                buf += chunk
            conn.settimeout(None)
            if not buf:
                return
            if b'\n' in buf:
                line_bytes = buf.split(b'\n', 1)[0]
            else:
                line_bytes = buf
            line = line_bytes.decode('utf-8', errors='ignore').strip()
            if not line:
                return
            try:
                req = json.loads(line)
            except Exception:
                req = {"action": "enqueue", "url": line}
            if req.get('action') == 'show':
                def _bring():
                    try:
                        self.show_all()
                        try:
                            self.deiconify()
                        except Exception:
                            pass
                        try:
                            if hasattr(self, 'present_with_time'):
                                self.present_with_time(Gdk.CURRENT_TIME)
                            else:
                                self.present()
                            gdk_win = self.get_window()
                            if gdk_win is not None:
                                try:
                                    gdk_win.raise_()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        try:
                            self.set_urgency_hint(True)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    return False
                GLib.idle_add(_bring)
                try:
                    conn.sendall((json.dumps({"status": "ok"}) + '\n').encode('utf-8'))
                except Exception:
                    pass
                return
            if req.get('action') == 'enqueue' and req.get('url'):
                fmt_id = req.get('formatId')
                fmt = fmt_id or req.get('format') or self.format_combo.get_active_text()
                qual = "" if fmt_id else (req.get('quality') or self.quality_entry.get_text())
                subs = req.get('subs')

                # Auto-detect generic file type from request
                ft = req.get('fileType')
                if ft in ('document', 'archive', 'program', 'image', 'other', 'unknown'):
                     if not fmt_id and fmt not in ("Best Video + Audio", "Audio Only"):
                         fmt = "Generic File"

                if isinstance(subs, str):
                    subs_active = subs.lower().startswith('y') or subs.lower() == 'true'
                else:
                    subs_active = bool(subs) if subs is not None else self.subs_check.get_active()

                def _enqueue():
                    prev_fmt = self.format_combo.get_active_text()
                    prev_qual = self.quality_entry.get_text()
                    prev_subs = self.subs_check.get_active()
                    try:
                        for i, label in enumerate(["Best Video + Audio", "Audio Only", "Best (default)"]):
                            if label == fmt:
                                self.format_combo.set_active(i)
                                break
                        self.quality_entry.set_text(qual or '')
                        self.subs_check.set_active(subs_active)
                        if req.get('confirm'):
                            try:
                                if req.get('show'):
                                    self.present()
                                    self.set_urgency_hint(True)
                            except Exception:
                                pass
                            dlg = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.NONE, "Start download?")
                            title = req.get('title') or self.get_video_title(req['url']) or 'Unknown'
                            details = f"Title: {title}\nFormat: {fmt}\nQuality: {qual or 'Best'}\nSubtitles: {'On' if subs_active else 'Off'}\n\nURL:\n{req['url']}"
                            dlg.format_secondary_text(details)
                            dlg.add_button("Cancel", Gtk.ResponseType.CANCEL)
                            dlg.add_button("Start", Gtk.ResponseType.OK)
                            resp = dlg.run()
                            dlg.destroy()
                            if resp != Gtk.ResponseType.OK:
                                return
                        self.add_url(req['url'], fmt=fmt, qual=qual, subs_active=subs_active)
                        if not self.is_downloading:
                            self.on_start_downloads(None)
                        if req.get('show') and not req.get('confirm'):
                            # User requested no disturbance, so we do not raise the window
                            # System notification from background.js is sufficient
                            try:
                                # self.present()  # DISABLE raising window
                                self.set_urgency_hint(True)  # Just flash entry in taskbar/dock
                            except Exception:
                                pass
                    finally:
                        for i, label in enumerate(["Best Video + Audio", "Audio Only", "Best (default)"]):
                            if label == prev_fmt:
                                self.format_combo.set_active(i)
                                break
                        self.quality_entry.set_text(prev_qual)
                        self.subs_check.set_active(prev_subs)

                GLib.idle_add(_enqueue)
                resp = {"status": "queued"}
            else:
                resp = {"status": "error", "message": "Invalid request"}
            conn.sendall((json.dumps(resp) + '\n').encode('utf-8'))
        except Exception as e:
            try:
                conn.sendall((json.dumps({"status": "error", "message": str(e)}) + '\n').encode('utf-8'))
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def process_queue(self):
        folder = os.path.expanduser(self.config["download_folder"])
        for idx, item in enumerate(self.queue):
            if not self.is_downloading: break
            self.update_status(idx, "Downloading...")
            cmd = [FAST_YTDL, item.url, folder, self.format_combo.get_active_text(), self.quality_entry.get_text() or "", "y" if self.subs_check.get_active() else "n", str(self.config.get("speed_limit_kbps") or ""), str(self.config.get("aria_connections", 32)), str(self.config.get("aria_splits", 32)), str(self.config.get("fragment_concurrency", 16)), self.config.get("category_mode", "idm")]
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
                item.process = proc
                for line in iter(proc.stdout.readline, ""):
                    line = line.strip()
                    self.parse_progress(line, idx)
                proc.wait()
                if proc.returncode == 0:
                    self.update_status(idx, "Completed")
                    self.append_history(item.title, item.url, "Completed", item.dest_path or "")
                else:
                    self.update_status(idx, "Failed")
                    self.append_history(item.title, item.url, "Failed", item.dest_path or "")
            except Exception as e:
                self.update_status(idx, f"Error: {str(e)}")
        self.is_downloading = False

    def on_pause_selected(self, widget):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        url = model[treeiter][0]
        for it in self.queue:
            if it.url == url:
                self._pause_item(it)
                break

    def on_resume_selected(self, widget):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        url = model[treeiter][0]
        for it in self.queue:
            if it.url == url:
                self._resume_item(it)
                break

    def _spooler(self):
        try:
            while self.is_downloading:
                maxc = int(self.config.get('max_concurrent', 2))
                active = sum(1 for it in self.queue if it.process and it.process.poll() is None)
                for it in self.queue:
                    if active >= maxc: break
                    if it.status in ("Queued", "Paused") and (not it.process or it.process.poll() is not None):
                        self._start_item_download(it); active += 1
                if active == 0 and not any(it.status in ("Queued", "Paused") for it in self.queue): break
                GLib.usleep(200_000)
        finally:
            self.is_downloading = False
            self.update_dashboard_counts()

    def _start_item_download(self, item):
        self._set_status(item, "Downloading...")
    # Use FileOrganizer to determine path
        folder = os.path.expanduser(self.config["download_folder"])
        
        if self.file_organizer:
            # Update organizer with current config
            self.file_organizer.base_dir = Path(folder)
            self.file_organizer.category_mode = self.config.get("category_mode", "idm")
            
            # Determine target folder name (playlist or default)
            playlist_name = getattr(item, 'playlist_name', None)
            
            # Get appropriate path
            # For generic items, we detect type from URL/filename
            # For yt-dlp items, we default to Videos or Music based on format
            
            fmt_hint = getattr(item, 'req_format', '') or self.format_combo.get_active_text()
            
            target_path, _ = self.file_organizer.get_download_path(
                filename=self._guess_filename(item.url),
                url=item.url,
                playlist_name=playlist_name,
                format_type=fmt_hint
            )
            folder = str(target_path)
            
            # Create directory
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception:
                pass

        fmt = item.req_format or self.format_combo.get_active_text()
        qual = item.req_quality or (self.quality_entry.get_text() or "")
        subs_flag = 'y' if (item.req_subs if item.req_subs is not None else self.subs_check.get_active()) else 'n'
        if getattr(item, 'kind', 'media') == 'generic':
            if self.config.get('aria2_rpc_enabled', False):
                try:
                    self._start_aria2_rpc_if_needed()
                    out_name = self._guess_filename(item.url)
                    gid = self._aria2_add_uri(item.url, folder, out_name)
                    item.gid = gid
                    threading.Thread(target=self._aria2_poll_item, args=(item,), daemon=True).start()
                    return
                except Exception as e:
                    print(f"[aria2rpc] fallback to process: {e}")
            aria_conn = int(self.config.get("aria_connections", 16))
            if aria_conn < 1: aria_conn = 1
            if aria_conn > 16: aria_conn = 16
            aria_splits = int(self.config.get("aria_splits", 32))
            if aria_splits < 4: aria_splits = 4
            speed_limit = str(self.config.get("speed_limit_kbps") or "")
            speed_arg = []
            if speed_limit.isdigit():
                speed_arg = [f"--max-overall-download-limit={speed_limit}K"]
            out_name = self._guess_filename(item.url)
            output_path = os.path.join(folder, out_name)
            
            # Try Rust engine first, fallback to aria2c
            if DOWNLOAD_ENGINE:
                try:
                    print(f"[Rust] Downloading {item.url} with {aria_conn} connections...")
                    success = DOWNLOAD_ENGINE.download_file(
                        url=item.url,
                        output_path=output_path,
                        connections=aria_conn,
                        speed_limit_kbps=int(speed_limit) if speed_limit.isdigit() else None
                    )
                    if success:
                        self._set_status(item, "Completed")
                        self.append_history(item.title, item.url, "Completed", output_path)
                    else:
                        self._set_status(item, "Failed")
                        self.append_history(item.title, item.url, "Failed", output_path)
                    return
                except Exception as e:
                    print(f"[Rust engine failed]: {e}, fallback to aria2c")
            
            # Fallback to aria2c command
            cmd = ["aria2c", "-x", str(aria_conn), "-s", str(aria_splits), "-k", "1M", "--min-split-size=1M", "--file-allocation=none"] + speed_arg + ["-d", folder, "-o", out_name, item.url]
        else:
            # For yt-dlp, we pass 'flat' to category_mode because we already determined the folder
            cmd = [
                FAST_YTDL, item.url, folder,
                fmt,
                qual,
                subs_flag,
                str(self.config.get("speed_limit_kbps") or ""),
                str(self.config.get("aria_connections", 32)),
                str(self.config.get("aria_splits", 32)),
                str(self.config.get("fragment_concurrency", 16)),
                "flat"  # Force flat mode in script since we handled organization here
            ]
        print("[Downloader]", " ".join(cmd))
        def _reader(proc, it):
            for line in iter(proc.stdout.readline, ""):
                line = line.strip()
                if line:
                    print(f"[DL:{it.url[:20]}] {line}")
                self._parse_item_progress(line, it)
                GLib.idle_add(self._add_or_update_big_row, it)
            proc.wait()
            if it.status == "Paused":
                return
            if proc.returncode == 0:
                self._set_status(it, "Completed")
                GLib.idle_add(self._remove_big_row, it)
                self.append_history(it.title, it.url, "Completed", it.dest_path or "")
            else:
                self._set_status(it, "Failed")
                GLib.idle_add(self._remove_big_row, it)
                self.append_history(it.title, it.url, "Failed", it.dest_path or "")
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            item.process = proc
            threading.Thread(target=_reader, args=(proc, item), daemon=True).start()
        except Exception as e:
            self._set_status(item, f"Error: {e}")
            self.append_history(item.title, item.url, f"Error: {e}", item.dest_path or "")

    def _set_status(self, item, status):
        item.status = status
        if item.treeiter:
            GLib.idle_add(self.liststore.set, item.treeiter, 4, status)
        try:
            idx = self.queue.index(item)
        except ValueError:
            idx = None
        if status == "Downloading..." and idx is not None:
            GLib.idle_add(self._show_mini_popup, idx)
        if status in ("Completed", "Failed") and idx is not None and self._mini_idx == idx:
            GLib.idle_add(self._hide_mini_popup)
        self.update_dashboard_counts()
        if status in ("Completed", "Failed"):
            GLib.idle_add(self._remove_big_row, item)
            # Stream terminal status to native client and close connection
            try:
                self._stream_client_update(item, {
                    "status": "finished" if status == "Completed" else "error",
                    "url": item.url,
                    "title": item.title
                }, close_after=True)
            except Exception:
                pass
        else:
            GLib.idle_add(self._add_or_update_big_row, item)
        GLib.idle_add(self._update_big_counts)
        try:
            if _HAS_NOTIFY and status in ("Completed", "Failed"):
                Notify.init("FastTube Downloader")
                n = Notify.Notification.new(status, item.title, None)
                n.show()
        except Exception:
            pass

    def _parse_item_progress(self, line, item):
        for marker in ("PROGRESS:", "TITLE:", "META:", "FILE:"):
            if marker in line and not line.startswith(marker):
                seg = marker + line.split(marker, 1)[1]
                self._parse_item_progress(seg, item)
                line = line.split(marker, 1)[0].strip()
        if not line:
            return
        if line.startswith("ERROR:"):
            try:
                msg = line.split(":",1)[1].strip()
            except Exception:
                msg = "Error"
            self._set_status(item, f"Error: {msg}")
            GLib.idle_add(self._add_or_update_big_row, item)
            return
        if line.startswith("WARN:") or line.startswith("WARNING:"):
            try:
                msg = line.split(":",1)[1].strip()
            except Exception:
                msg = "Warning"
            self._set_status(item, f"Warning: {msg}")
            GLib.idle_add(self._add_or_update_big_row, item)
        if line.startswith("META:"):
            try:
                parts = line.split(":", 1)[1].strip().split()
                for p in parts:
                    if '=' in p:
                        k, v = p.split('=', 1)
                        if k == 'speed': item.speed = v
                        elif k == 'eta': item.eta = v
                        elif k == 'total': item.total = v
                        elif k == 'downloaded': item.downloaded = v
                # Trigger update
                self._update_item_progress(item, item.progress)
            except Exception:
                pass
            return
        if line.startswith("PROGRESS:"):
            try:
                pct_str = line.split(":", 1)[1].strip().rstrip("% ")
                pct = float(pct_str)
                self._update_item_progress(item, int(pct))
                return
            except Exception:
                pass
        if line.startswith("[download]"):
            try:
                # Standard yt-dlp output: [download]  12.3% of 10.00MiB at 1.23MiB/s ETA 00:05
                parts = line.split()
                pct = 0
                for p in parts:
                    if '%' in p:
                        try:
                            pct = float(p.rstrip('%'))
                            break
                        except: pass
                if pct > 0:
                    if 'at' in parts:
                        try:
                            idx = parts.index('at')
                            if idx + 1 < len(parts):
                                item.speed = parts[idx+1]
                        except: pass
                    if 'ETA' in parts:
                        try:
                            idx = parts.index('ETA')
                            if idx + 1 < len(parts):
                                item.eta = parts[idx+1]
                        except: pass
                    if 'of' in parts:
                        try:
                            idx = parts.index('of')
                            if idx + 1 < len(parts):
                                item.total = parts[idx+1]
                        except: pass
                    self._update_item_progress(item, int(pct))
                return
            except Exception:
                pass
        return

    def _categorize_generic(self, url: str) -> str:
        try:
            p = urllib.parse.urlparse(url)
            ext = os.path.splitext((p.path or '').lower())[-1]
            mapping = self.config.get('generic_extensions_map', {})
            for folder, exts in mapping.items():
                if ext in exts:
                    return folder
            return 'Other'
        except Exception:
            return 'Other'

    def _start_aria2_rpc_if_needed(self):
        if not self.config.get('aria2_rpc_enabled', False):
            return
        if getattr(self, '_aria2_rpc_started', False):
            return
        port = int(self.config.get('aria2_rpc_port', 6800))
        try:
            cmd = ["aria2c", "--enable-rpc", f"--rpc-listen-port={port}", "--rpc-max-request-size=1024M", "--continue", "--max-concurrent-downloads=64", "-j", "64"]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._aria2_rpc_started = True
            time.sleep(0.4)
        except Exception as e:
            print(f"[aria2rpc] failed to start daemon: {e}")

    def _aria2_rpc_call(self, method: str, params):
        port = int(self.config.get('aria2_rpc_port', 6800))
        payload = json.dumps({"jsonrpc": "2.0", "id": "ftdl", "method": method, "params": params}).encode('utf-8')
        import urllib.request
        req = urllib.request.Request(f"http://127.0.0.1:{port}/jsonrpc", data=payload, headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='ignore'))
            if 'error' in data:
                raise RuntimeError(data['error'])
            return data.get('result')

    def _aria2_add_uri(self, url: str, folder: str, out_name: str):
        opts = {"dir": folder, "out": out_name, "max-connection-per-server": str(self.config.get('aria_connections',16)), "split": str(self.config.get('aria_splits',32)), "min-split-size": "1M"}
        speed_limit = str(self.config.get('speed_limit_kbps') or '')
        if speed_limit.isdigit():
            opts['max-overall-download-limit'] = f"{speed_limit}K"
        result = self._aria2_rpc_call('aria2.addUri', [[url], opts])
        return result

    def _aria2_poll_item(self, item):
        try:
            while item.status in ("Queued", "Downloading...") and item.gid and self.config.get('aria2_rpc_enabled', False):
                try:
                    st = self._aria2_rpc_call('aria2.tellStatus', [item.gid, ["status", "completedLength", "totalLength", "downloadSpeed"]])
                except Exception:
                    st = None
                if not st:
                    break
                status = st.get('status','')
                comp = st.get('completedLength') or '0'
                total = st.get('totalLength') or '0'
                try:
                    comp_i = int(comp)
                    total_i = int(total) if total.isdigit() else 0
                    if total_i > 0:
                        pct = int((comp_i/total_i)*100)
                        item.downloaded = self._human_bytes(self._bytes_to_str(comp_i))
                        item.total = self._human_bytes(self._bytes_to_str(total_i))
                        self._update_item_progress(item, pct)
                except Exception:
                    pass
                spd = st.get('downloadSpeed')
                if spd and spd.isdigit():
                    item.speed = self._human_bytes(self._bytes_to_str(int(spd))) + '/s'
                self._update_progress_text(item)
                if status == 'complete':
                    self._set_status(item, 'Completed')
                    break
                if status == 'error':
                    self._set_status(item, 'Failed')
                    break
                if item.status == 'Paused':
                    break
                time.sleep(1.0)
        except Exception:
            pass

    def _bytes_to_str(self, val: int) -> str:
        try:
            units = ['B','KiB','MiB','GiB','TiB']
            v = float(val)
            u = 0
            while v >= 1024 and u < len(units)-1:
                v /= 1024.0; u += 1
            return f"{v:.1f}{units[u]}"
        except Exception:
            return ''

    def _update_item_progress(self, item, progress):
        item.progress = progress
        if item.treeiter is None:
            return
        dots = '.' * ((progress // 5) % 3 + 1)
        size_str = f"{item.downloaded}/{item.total}" if item.total else item.downloaded
        GLib.idle_add(self.liststore.set, item.treeiter, 2, int(progress), 5, item.speed or "", 6, item.eta or "", 7, size_str or "")
        self._update_progress_text(item)
        # Stream progress to native client if attached
        try:
            self._stream_client_update(item, {
                "status": "progress",
                "percent": int(progress),
                "url": item.url,
                "title": item.title
            })
        except Exception:
            pass
        if self._mini_popup is not None and self._mini_idx is not None:
            def _upd_bar():
                try:
                    try:
                        idx = self.queue.index(item)
                    except ValueError:
                        return False
                    if self._mini_popup is None or self._mini_idx != idx:
                        return False
                    bar = self._mini_popup.get_child().get_children()[1]
                    bar.set_fraction(max(0.0, min(1.0, progress/100.0)))
                    bar.set_text(f"{int(progress)}%")
                except Exception:
                    pass
                return False
            GLib.idle_add(_upd_bar)

    def _stream_client_update(self, item, obj: dict, close_after: bool = False):
        conn = getattr(item, 'client_conn', None)
        if conn is None:
            return
        try:
            payload = dict(obj)
            if getattr(item, 'client_req_id', None) is not None:
                payload['requestId'] = item.client_req_id
            conn.sendall((json.dumps(payload) + '\n').encode('utf-8'))
        except Exception:
            pass
        finally:
            if close_after:
                try:
                    conn.close()
                except Exception:
                    pass
                try:
                    item.client_conn = None
                except Exception:
                    pass

    def _update_item_title(self, item, title):
        item.title = title
        if item.treeiter is None:
            return
        GLib.idle_add(self.liststore.set, item.treeiter, 1, title)
        if self._mini_popup is not None and self._mini_idx is not None:
            def _upd_title():
                try:
                    try:
                        idx = self.queue.index(item)
                    except ValueError:
                        return False
                    if self._mini_popup is None or self._mini_idx != idx:
                        return False
                    header = self._mini_popup.get_child().get_children()[0]
                    header.set_text(title)
                except Exception:
                    pass
                return False
            GLib.idle_add(_upd_title)

    def parse_progress(self, line, idx):
        for marker in ("PROGRESS:", "TITLE:", "META:", "FILE:"):
            if marker in line and not line.startswith(marker):
                seg = marker + line.split(marker, 1)[1]
                self.parse_progress(seg, idx)
                line = line.split(marker, 1)[0].strip()
        if not line:
            return
        if line.startswith("ERROR:"):
            try:
                msg = line.split(":",1)[1].strip()
            except Exception:
                msg = "Error"
            self.update_status(idx, f"Error: {msg}")
            return
        if line.startswith("WARN:") or line.startswith("WARNING:"):
            try:
                msg = line.split(":",1)[1].strip()
            except Exception:
                msg = "Warning"
            self.update_status(idx, f"Warning: {msg}")
        if line.startswith("PROGRESS:"):
            try:
                pct_str = line.split(":", 1)[1].strip().rstrip("% ")
                pct = float(pct_str)
                self.update_progress(idx, int(pct))
                return
            except Exception:
                pass
        if line.startswith("TITLE:"):
            try:
                title = line.split(":", 1)[1].strip()
                if title:
                    self.update_title(idx, title)
                return
            except Exception:
                pass
        try:
            if '%' in line and '(' in line and ')' in line and '[' in line:
                import re as _re
                pm = _re.search(r"\((\d+(?:\.\d+)?)%\)", line)
                if pm:
                    self.update_progress(idx, int(float(pm.group(1))))
                sm = _re.search(r"DL:([^\] ]+)", line)
                em = _re.search(r"ETA:([0-9:]+)", line)
                dtm = _re.search(r"\s([0-9.]+[A-Za-z]+)\/((?:N\/A)|[0-9.]+[A-Za-z]+)\(", line)
                it = self.queue[idx]
                if sm:
                    it.speed = sm.group(1)
                if em:
                    it.eta = em.group(1)
                if dtm:
                    it.downloaded = dtm.group(1)
                    it.total = dtm.group(2)
                prog = f"{it.progress}%"
                extra = " ".join([s for s in [it.speed or '', it.eta or ''] if s])
                if extra and it.treeiter is not None:
                    GLib.idle_add(self.liststore.set, it.treeiter, 3, f"{prog} • {extra}")
        except Exception:
            pass
        if "[download]" in line and "%" in line:
            try:
                import re as _re
                m = _re.search(r"(\d+(?:\.\d+)?)%", line)
                if m:
                    self.update_progress(idx, int(float(m.group(1))))
            except Exception:
                pass
        if "Destination:" in line:
            try:
                dest = line.split("Destination: ")[1].strip()
                title = dest.split(".")[-2].split(" - ")[-1] if " - " in dest else dest.split(".")[0].replace("NA - ", "")
                self.update_title(idx, title)
                try:
                    self.queue[idx].dest_path = dest
                except Exception:
                    pass
            except:
                pass
        if line.startswith("META:"):
            try:
                parts = line.split(None, 1)[1] if ' ' in line else ''
                kv = {}
                for tok in parts.split():
                    if '=' in tok:
                        k,v = tok.split('=',1)
                        kv[k]=v
                item = self.queue[idx]
                item.speed = kv.get('speed','')
                item.eta = kv.get('eta','')
                item.total = kv.get('total','')
                item.downloaded = kv.get('downloaded','')
                self._update_progress_text(item)
            except Exception:
                pass
        if line.startswith("FILE:"):
            try:
                path = line.split(":",1)[1].strip()
                self.queue[idx].dest_path = path
            except Exception:
                pass

    def update_progress(self, idx, progress):
        self.queue[idx].progress = progress
        item = self.queue[idx]
        if item.treeiter is None:
            return
        dots = '.' * ((progress // 5) % 3 + 1)
        GLib.idle_add(self.liststore.set, item.treeiter, 2, int(progress))
        self._update_progress_text(item)
        if self._mini_idx == idx and self._mini_popup is not None:
            try:
                bar = self._mini_popup.get_child().get_children()[1]
                bar.set_fraction(max(0.0, min(1.0, progress/100.0)))
                bar.set_text(f"{int(progress)}%")
            except Exception:
                pass

    def _human_bytes(self, val):
        try:
            if not val: return ''
            return val
        except Exception:
            return ''

    def _compose_progress_summary(self, item):
        pct = f"{item.progress}%"
        size_part = ''
        try:
            if item.downloaded or item.total:
                size_part = f"{self._human_bytes(item.downloaded)}/{self._human_bytes(item.total)}".strip('/')
        except Exception:
            size_part = ''
        speed_part = item.speed or ''
        eta_part = item.eta or ''
        pieces = [pct]
        if size_part:
            pieces.append(size_part)
        if speed_part:
            pieces.append(speed_part)
        if eta_part:
            pieces.append(f"ETA {eta_part}")
        return ' • '.join(pieces)

    def _update_progress_text(self, item):
        try:
            text = self._compose_progress_summary(item)
            if item.treeiter is not None:
                GLib.idle_add(self.liststore.set, item.treeiter, 3, text)
            if self._mini_popup is not None and self._mini_idx is not None:
                try:
                    if self.queue[self._mini_idx] is item and self._mini_status_lbl is not None:
                        GLib.idle_add(self._mini_status_lbl.set_text, text)
                except Exception:
                    pass
        except Exception:
            pass

    def update_title(self, idx, title):
        self.queue[idx].title = title
        item = self.queue[idx]
        if item.treeiter is None:
            return
        GLib.idle_add(self.liststore.set, item.treeiter, 1, title)
        if self._mini_idx == idx and self._mini_popup is not None:
            try:
                header = self._mini_popup.get_child().get_children()[0]
                header.set_text(title)
            except Exception:
                pass

    def update_status(self, idx, status):
        self.queue[idx].status = status
        item = self.queue[idx]
        if item.treeiter is None:
            return
        GLib.idle_add(self.liststore.set, item.treeiter, 4, status)
        if status == "Downloading...":
            GLib.idle_add(self._show_mini_popup, idx)
        if status in ("Completed", "Failed") and self._mini_idx == idx:
            GLib.idle_add(self._hide_mini_popup)
        self.update_dashboard_counts()
        try:
            if _HAS_NOTIFY and status in ("Completed", "Failed"):
                Notify.init("FastTube Downloader")
                n = Notify.Notification.new(f"{status}", self.queue[idx].title, None)
                n.show()
        except Exception:
            pass

    def _show_mini_popup(self, idx):
        try:
            item = self.queue[idx]
            if self._mini_popup is None:
                win = Gtk.Window(title="FastTube Downloading")
                win.set_keep_above(True)
                win.set_decorated(False)
                win.set_default_size(300, 80)
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                box.set_border_width(10)
                title_lbl = Gtk.Label(label=item.title)
                title_lbl.set_ellipsize(3)
                status_lbl = Gtk.Label(label=self._compose_progress_summary(item))
                status_lbl.set_halign(Gtk.Align.START)
                status_lbl.set_ellipsize(3)
                bar = Gtk.ProgressBar()
                if item.progress:
                    bar.set_fraction(item.progress/100.0)
                    bar.set_text(f"{int(item.progress)}%")
                    bar.set_show_text(True)
                box.pack_start(title_lbl, False, False, 0)
                box.pack_start(status_lbl, False, False, 0)
                box.pack_start(bar, True, True, 0)
                win.add(box)
                css = Gtk.CssProvider()
                css.load_from_data(b".mini-popup { background: #1e1e1e; color: #eee; border-radius: 8px; }")
                box.get_style_context().add_class("mini-popup")
                Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_USER)
                self._mini_popup = win
                self._mini_title_lbl = title_lbl
                self._mini_status_lbl = status_lbl
                self._mini_progress_bar = bar
            else:
                if self._mini_title_lbl is not None:
                    self._mini_title_lbl.set_text(item.title)
                if self._mini_status_lbl is not None:
                    self._mini_status_lbl.set_text(self._compose_progress_summary(item))
            self._mini_idx = idx
            self._mini_popup.show_all()
            try:
                self._mini_popup.present()
                self._mini_popup.set_opacity(0.0)
                def _fade(step=0):
                    try:
                        if self._mini_popup is None:
                            return False
                        new_op = min(1.0, step/10.0)
                        self._mini_popup.set_opacity(new_op)
                        return False if new_op >= 1.0 else True
                    except Exception:
                        return False
                for i in range(1,11):
                    GLib.timeout_add(25*i, lambda s=i: _fade(s))
            except Exception:
                pass
        except Exception:
            pass

    def _pulse_progress_rows(self):
        return True

    def _hide_mini_popup(self):
        if self._mini_popup is not None:
            try:
                self._mini_popup.hide()
            except Exception:
                pass
            self._mini_idx = None
            self._mini_title_lbl = None
            self._mini_status_lbl = None
            self._mini_progress_bar = None

    def _ensure_big_popup(self):
        if not self.config.get("show_big_popup", True):
            return
        if getattr(self, '_big_popup', None):
            return
        win = Gtk.Window(title="FastTube Downloads")
        win.set_default_size(580, 360)
        win.set_keep_above(True)
        win.set_decorated(True)
        win.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        win.set_skip_taskbar_hint(True)
        win.set_skip_pager_hint(True)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_border_width(10)
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        controls.set_hexpand(True)
        controls.get_style_context().add_class("big-controls")
        self._big_header_label = Gtk.Label(label="")
        self._big_header_label.set_halign(Gtk.Align.START)
        pause_all_btn = Gtk.Button(label="Pause All")
        pause_all_btn.connect("clicked", self._pause_all)
        resume_all_btn = Gtk.Button(label="Start All")
        resume_all_btn.connect("clicked", self._resume_all)
        clear_btn = Gtk.Button(label="Clear Finished")
        clear_btn.connect("clicked", self._clear_finished_rows)
        controls.pack_start(self._big_header_label, True, True, 0)
        controls.pack_start(pause_all_btn, False, False, 0)
        controls.pack_start(resume_all_btn, False, False, 0)
        controls.pack_start(clear_btn, False, False, 0)
        vbox.pack_start(controls, False, False, 0)
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        listbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        sc.add(listbox)
        vbox.pack_start(sc, True, True, 0)
        win.add(vbox)
        css = Gtk.CssProvider()
        css.load_from_data(b".big-popup { background:#10151a; color:#e9eef5; } .rowbox{ background:#181d22; border-radius:8px; padding:10px;} .rowtitle{ font-weight:700; font-size:13px;} .rowstatus{ color:#a8b3be; font-size:11px; } .big-controls { background:#0e1318; padding:6px 8px; border-radius:6px; } .big-controls button { background:#1f2630; color:#d5dde6; border:1px solid #2d3641; border-radius:6px; padding:4px 10px; } .big-controls button:hover { background:#2a333f; }")
        vbox.get_style_context().add_class("big-popup")
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        self._big_popup = win
        self._big_list = listbox
        self._update_big_counts()

    def _add_or_update_big_row(self, item):
        self._ensure_big_popup()
        row = self._big_rows.get(item)
        if not row:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.get_style_context().add_class("rowbox")
            title = Gtk.Label(label=item.title or item.url)
            title.set_halign(Gtk.Align.START)
            title.get_style_context().add_class("rowtitle")
            status = Gtk.Label(label=self._compose_progress_summary(item))
            status.set_halign(Gtk.Align.START)
            status.get_style_context().add_class("rowstatus")
            hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            bar = Gtk.ProgressBar()
            bar.set_show_text(True)
            pb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            btn_pause = Gtk.Button(label="Pause")
            btn_resume = Gtk.Button(label="Start")
            btn_pause.connect("clicked", lambda _b, it=item: self._pause_item(it))
            btn_resume.connect("clicked", lambda _b, it=item: self._resume_item(it))
            pb.pack_start(btn_pause, False, False, 0)
            pb.pack_start(btn_resume, False, False, 0)
            hb.pack_start(bar, True, True, 0)
            hb.pack_end(pb, False, False, 0)
            box.pack_start(title, False, False, 0)
            box.pack_start(status, False, False, 0)
            box.pack_start(hb, False, False, 0)
            self._big_list.pack_start(box, False, False, 0)
            self._big_rows[item] = {
                'box': box,
                'title': title,
                'status': status,
                'bar': bar,
                'pause': btn_pause,
                'resume': btn_resume
            }
            self._big_popup.show_all()
        else:
            box = row['box']
            title = row['title']
            status = row['status']
            bar = row['bar']
            btn_pause = row['pause']
            btn_resume = row['resume']
        row = self._big_rows[item]
        row['title'].set_text(item.title or item.url)
        row['status'].set_text(self._compose_progress_summary(item))
        row['bar'].set_fraction(max(0.0, min(1.0, (item.progress or 0)/100.0)))
        row['bar'].set_text(f"{int(item.progress or 0)}%")
        
        if item.status == "Downloading...":
            row['bar'].get_style_context().add_class("pulse")
        else:
            row['bar'].get_style_context().remove_class("pulse")

        running = bool(item.process and item.process.poll() is None)
        row['pause'].set_sensitive(running)
        row['resume'].set_sensitive(not running)
        self._update_big_counts()

    def _remove_big_row(self, item):
        row = getattr(self, '_big_rows', {}).get(item)
        if not row:
            return
        try:
            self._big_list.remove(row['box'])
        except Exception:
            pass
        self._big_rows.pop(item, None)
        if self._big_rows == {} and getattr(self, '_big_popup', None):
            try:
                self._big_popup.hide()
            except Exception:
                pass
        self._update_big_counts()

    def _update_big_counts(self):
        if not getattr(self, '_big_header_label', None):
            return
        queued = sum(1 for it in self.queue if it.status == 'Queued')
        active = sum(1 for it in self.queue if it.status == 'Downloading...')
        paused = sum(1 for it in self.queue if it.status == 'Paused')
        text = f"Active: {active} | Paused: {paused} | Queue: {queued}"
        try:
            self._big_header_label.set_text(text)
        except Exception:
            pass

    def _pause_all(self, *_args):
        for item in list(self.queue):
            self._pause_item(item)
        self._update_big_counts()

    def _resume_all(self, *_args):
        for item in list(self.queue):
            if item.status == "Paused":
                self._resume_item(item)
        self._update_big_counts()

    def _clear_finished_rows(self, *_args):
        for item in list(getattr(self, '_big_rows', {}).keys()):
            if item.status in ("Completed", "Failed"):
                self._remove_big_row(item)
        self._update_big_counts()

    def _pause_item(self, item):
        if item.status in ("Completed", "Failed"):
            return
        if getattr(item, 'kind', 'media') == 'generic' and self.config.get('aria2_rpc_enabled', False) and item.gid:
            try:
                self._aria2_rpc_call('aria2.pause', [item.gid])
                self._set_status(item, "Paused")
                return
            except Exception:
                pass
        if item.process and item.process.poll() is None:
            try:
                item.process.terminate()
            except Exception:
                pass
        self._set_status(item, "Paused")

    def _resume_item(self, item):
        if item.status == "Paused":
            if getattr(item, 'kind', 'media') == 'generic' and self.config.get('aria2_rpc_enabled', False) and item.gid:
                try:
                    self._aria2_rpc_call('aria2.unpause', [item.gid])
                    self._set_status(item, "Downloading...")
                    return
                except Exception:
                    pass
            self._set_status(item, "Queued")
            if not self.is_downloading:
                self.is_downloading = True
                threading.Thread(target=self._spooler, daemon=True).start()

    def clear_queue(self, widget):
        self.liststore.clear()
        self.queue.clear()
        for item in list(getattr(self, '_big_rows', {}).keys()):
            self._remove_big_row(item)
        self._update_big_counts()
        self.update_dashboard_counts()

    def show_message(self, msg):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, msg)
        dialog.run()
        dialog.destroy()

    def quit_app(self, widget=None):
        if self.is_downloading:
            for item in self.queue:
                if item.process:
                    item.process.terminate()
        Gtk.main_quit()

def run_app():
    force_new = any(arg in ('--new-instance','-N') for arg in sys.argv[1:])
    if not force_new:
        try:
            import socket as _s
            s = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(('127.0.0.1', 47653))
            try:
                s.sendall((json.dumps({"action":"show"})+'\n').encode('utf-8'))
            except Exception:
                pass
            s.close()
            return
        except Exception:
            pass
    win = MainWindow()
    if isinstance(win, MainWindow) and getattr(win, 'config', None):
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()

if __name__ == "__main__":
    run_app()
#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import threading
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
try:
    gi.require_version("Pango", "1.0")
except Exception:
    pass
try:
    gi.require_version("Notify", "0.7")
except Exception:
    pass
from gi.repository import Gtk, GLib, Gdk, Pango
try:
    from gi.repository import Notify
    _HAS_NOTIFY = True
except Exception:
    _HAS_NOTIFY = False
import re
import urllib.request
import urllib.parse
import socket
import threading
import time
try:
    from .playlist_utils import parse_flat_playlist_lines
except Exception:
    parse_flat_playlist_lines = None

GLib.set_application_name("FastTube Downloader")
try:
    Gdk.set_program_class("FastTubeDownloader")
except Exception:
    pass
try:
    GLib.set_prgname("fasttube-downloader")
except Exception:
    pass

CONFIG_DIR = os.path.expanduser("~/.config/FastTubeDownloader")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")

# Resolve path to helper downloader script (fast_ytdl.sh) both in dev tree and when installed under /opt
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root when running from source
FAST_YTDL_LOCAL = os.path.join(_BASE_DIR, "fast_ytdl.sh")
FAST_YTDL_ALT = "/opt/FastTubeDownloader/fast_ytdl.sh"
# Prefer local script if present; ensure it's executable
if os.path.exists(FAST_YTDL_LOCAL):
    try:
        st = os.stat(FAST_YTDL_LOCAL)
        if not (st.st_mode & 0o111):
            os.chmod(FAST_YTDL_LOCAL, st.st_mode | 0o755)
    except Exception:
        pass
    FAST_YTDL = FAST_YTDL_LOCAL
elif os.path.exists(FAST_YTDL_ALT):
    FAST_YTDL = FAST_YTDL_ALT
else:
    FAST_YTDL = FAST_YTDL_LOCAL

class DownloadItem:
    def __init__(self, url: str, title: str):
        self.url = url
        self.title = title or "Unknown"
        self.progress = 0
        self.status = "Queued"
        self.process = None
        self.dest_path = None
        self.treeiter = None
        self.kind = 'media'
        self.req_format = None
        self.req_quality = None
        self.req_subs = None
        self.speed = ''
        self.eta = ''
        self.total = ''
        self.downloaded = ''
        self.gid = None

    def __repr__(self):
        return f"<DownloadItem {self.title!r} {self.progress}% {self.status}>"

class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="FastTube Downloader")
        self.set_border_width(10)
        try:
            icon_path = os.path.join(_BASE_DIR, 'icon128.png')
            if os.path.exists(icon_path):
                try:
                    Gtk.Window.set_default_icon_from_file(icon_path)
                except Exception:
                    pass
                self.set_icon_from_file(icon_path)
                try:
                    if hasattr(self, 'set_wmclass'):
                        self.set_wmclass("FastTubeDownloader", "FastTube Downloader")
                except Exception:
                    pass
        except Exception:
            pass
        # Ensure window is user-resizable
        try:
            self.set_resizable(True)
        except Exception:
            pass
        # Initial size: scale with screen so it always fits comfortably
        self._set_initial_window_size()
        # Load config; if missing, run setup wizard as a subprocess and retry once
        self.config = self.load_config()
        if not self.config:
            try:
                setup_path = os.path.join(_BASE_DIR, "gui", "first_time_setup.py")
                subprocess.run([sys.executable, setup_path], check=False)
                # Reload config after setup exits
                self.config = self.load_config()
            except Exception:
                self.config = None
        if not self.config:
            # As a last resort, start from an empty config and apply defaults
            self.config = {}
        self._apply_config_defaults()
        # Build full UI for normal runs
        self.build_ui()

    def _set_initial_window_size(self):
        """Pick an initial size strictly within screen bounds (no overflow)."""
        try:
            sw, sh = self._get_screen_dimensions()
            # If user has a saved size, prefer it (clamped below). Otherwise use ratios.
            cfg_w = int(self.config.get("window_width", 0)) if isinstance(getattr(self, 'config', {}), dict) else 0
            cfg_h = int(self.config.get("window_height", 0)) if isinstance(getattr(self, 'config', {}), dict) else 0
            if cfg_w > 0 and cfg_h > 0:
                w, h = cfg_w, cfg_h
            else:
                # Use a narrower width ratio to avoid horizontal overflow; user can resize larger.
                # Height: be generous so the queue/history are visible by default.
                w = int(sw * 0.35)
                h = int(sh * 0.85)
            # Enforce minimums for usability
            if w < 640: w = 640
            if h < 400: h = 400
            # Never exceed screen minus margins
            max_w = sw - 40
            max_h = sh - 60
            if w > max_w: w = max_w
            if h > max_h: h = max_h
            # Apply hard maximum hints so WM won't allow oversize
            try:
                geom = Gdk.Geometry()
                geom.max_width = max_w
                geom.max_height = max_h
                # Pass self for geometry_widget to ensure hints are respected
                self.set_geometry_hints(self, geom, Gdk.WindowHints.MAX_SIZE)
            except Exception:
                pass
            self.set_default_size(w, h)
            # One-shot enforce after widgets pack
            GLib.idle_add(lambda: (self.resize(w, h), False)[1])
            # Debug: print computed size to help verify path
            try:
                print(f"[GUI] Screen {sw}x{sh} -> initial {w}x{h} (max {max_w}x{max_h})")
            except Exception:
                pass
            try:
                self.set_position(Gtk.WindowPosition.CENTER)
            except Exception:
                pass
        except Exception:
            self.set_default_size(800, 500)
            
    def _get_screen_dimensions(self):
        """Return (width, height) in logical units of the primary monitor workarea.

        We convert device-pixel geometry to logical coordinates using the monitor
        scale factor so comparisons with Gtk.Window.get_size() remain consistent.
        """
        try:
            display = Gdk.Display.get_default()
            if display:
                try:
                    monitor = display.get_primary_monitor()
                except Exception:
                    monitor = None
                if monitor:
                    try:
                        rect = monitor.get_workarea()
                    except Exception:
                        rect = monitor.get_geometry()
                    # Convert to logical units using scale factor if available
                    try:
                        scale = int(getattr(monitor, 'get_scale_factor', lambda: 1)()) or 1
                    except Exception:
                        scale = 1
                    return int(rect.width // scale), int(rect.height // scale)
        except Exception:
            pass
        # Fallback to deprecated Gdk.Screen API (already logical)
        try:
            scr = self.get_screen()
            return int(scr.get_width()), int(scr.get_height())
        except Exception:
            return 1024, 768

    def _apply_config_defaults(self):
        defaults = {
            "download_folder": os.path.expanduser("~/Downloads"),
            "default_format": "Best (default)",
            "preferred_quality": "",
            "subs": False,
            "clipboard_auto": False,
            "speed_limit_kbps": "",
            "max_concurrent": 2,
            "aria_connections": 32,
            "aria_splits": 32,
            "fragment_concurrency": 16,
            "category_mode": "idm",
            "show_big_popup": True,
            # Generic file support
            "enable_generic": True,
            "aria2_rpc_enabled": False,
            "aria2_rpc_port": 6800,
            # Auto start downloads upon adding to queue
            "auto_start": True,
            # Extension-based categorization for generic downloads
            "generic_extensions_map": {
                "Videos": [".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".wmv"],
                "Music": [".mp3", ".m4a", ".aac", ".flac", ".wav", ".ogg"],
                "Pictures": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
                "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"],
                "Archives": [".zip", ".rar", ".7z", ".tar", ".tar.gz", ".tgz", ".tar.bz2"],
                "ISO": [".iso", ".img"],
                "Other": []
            }
        }
        if not isinstance(self.config, dict):
            self.config = {}
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        # Normalize values
        self.config["download_folder"] = os.path.expanduser(self.config.get("download_folder", "~/Downloads"))
        try:
            self.config["aria_connections"] = int(self.config.get("aria_connections", 32))
        except Exception:
            self.config["aria_connections"] = 32
        # Clamp to aria2 allowed range 1-16
        if self.config["aria_connections"] < 1:
            self.config["aria_connections"] = 1
        if self.config["aria_connections"] > 16:
            self.config["aria_connections"] = 16
        try:
            self.config["aria_splits"] = int(self.config.get("aria_splits", 32))
        except Exception:
            self.config["aria_splits"] = 32
        try:
            self.config["fragment_concurrency"] = int(self.config.get("fragment_concurrency", 16))
        except Exception:
            self.config["fragment_concurrency"] = 16
        if self.config.get("category_mode") not in ("idm", "flat"):
            self.config["category_mode"] = "idm"
        os.makedirs(self.config["download_folder"], exist_ok=True)

    def build_ui(self):
        # Use a modern layout: Gtk.HeaderBar + main content box
        self.set_title("FastTube Downloader")
        try:
            header = Gtk.HeaderBar()
            header.set_show_close_button(True)
            header.props.title = "FastTube Downloader"
            self.set_titlebar(header)
            # Header actions
            refresh_btn = Gtk.Button.new_from_icon_name("view-refresh", Gtk.IconSize.BUTTON)
            refresh_btn.set_tooltip_text("Refresh queue progress")
            refresh_btn.connect("clicked", lambda *_: self.update_dashboard_counts())
            header.pack_start(refresh_btn)
            stats_btn = Gtk.Button(label="Dashboard")
            stats_btn.connect("clicked", lambda *_: self.notebook.set_current_page(0))
            header.pack_end(stats_btn)
        except Exception:
            pass

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        # Dashboard header
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.header_box.set_border_width(12)
        self.lbl_counts = Gtk.Label(label="Queued: 0 | Downloading: 0 | Completed: 0")
        self.lbl_counts.get_style_context().add_class("fasttube-header")
        self.header_box.pack_start(self.lbl_counts, False, False, 0)
        vbox.pack_start(self.header_box, False, False, 0)

        # Notebook
        self.notebook = Gtk.Notebook()
        vbox.pack_start(self.notebook, True, True, 0)

        # ===== Queue tab =====
        queue_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        hbox_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.url_entry = Gtk.Entry(placeholder_text="Paste YouTube URL here...")
        self.url_entry.set_hexpand(True)
        add_btn = Gtk.Button(label="Add to Queue")
        add_btn.connect("clicked", self.on_add_download)
        start_btn = Gtk.Button(label="Start Downloads")
        start_btn.connect("clicked", self.on_start_downloads)
        stop_btn = Gtk.Button(label="Stop")
        stop_btn.connect("clicked", self.on_stop_downloads)
        clear_btn = Gtk.Button(label="Clear Queue")
        clear_btn.connect("clicked", self.clear_queue)
        remove_btn = Gtk.Button(label="Remove Selected")
        remove_btn.connect("clicked", self.on_remove_selected)
        pause_btn = Gtk.Button(label="Pause Selected")
        pause_btn.connect("clicked", self.on_pause_selected)
        resume_btn = Gtk.Button(label="Resume Selected")
        resume_btn.connect("clicked", self.on_resume_selected)
        open_folder_btn = Gtk.Button(label="Open Folder")
        open_folder_btn.connect("clicked", self.on_open_folder)
        hbox_top.pack_start(self.url_entry, True, True, 0)
        hbox_top.pack_start(add_btn, False, False, 0)
        hbox_top.pack_start(start_btn, False, False, 0)
        hbox_top.pack_start(stop_btn, False, False, 0)
        hbox_top.pack_start(remove_btn, False, False, 0)
        hbox_top.pack_start(pause_btn, False, False, 0)
        hbox_top.pack_start(resume_btn, False, False, 0)
        hbox_top.pack_start(open_folder_btn, False, False, 0)
        hbox_top.pack_start(clear_btn, False, False, 0)
        queue_page.pack_start(hbox_top, False, False, 0)

        # Settings strip: wrap in a scrolled window to prevent forcing very wide main window.
        self.settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.settings_box.get_style_context().add_class("settings-strip")
        self.format_combo = Gtk.ComboBoxText()
        for opt in ("Best Video + Audio", "Audio Only", "Best (default)", "Generic File"):
            self.format_combo.append_text(opt)
        fmt_idx = {"Best Video + Audio": 0, "Audio Only": 1, "Best (default)": 2, "Generic File": 3}.get(self.config.get("default_format"), 2)
        self.format_combo.set_active(fmt_idx)
        self.format_combo.connect("changed", self.on_format_changed)
        self.quality_entry = Gtk.Entry()
        self.quality_entry.set_placeholder_text(self.config.get("preferred_quality", "1080"))
        if self.config.get("preferred_quality"):
            self.quality_entry.set_text(str(self.config.get("preferred_quality")))
        self.subs_check = Gtk.CheckButton(label="Subtitles")
        self.subs_check.set_active(self.config.get("subs", False))
        self.clipboard_check = Gtk.CheckButton(label="Auto-add from Clipboard")
        self.clipboard_check.set_active(self.config.get("clipboard_auto", False))
        self.speed_entry = Gtk.Entry()
        self.speed_entry.set_placeholder_text("Speed limit KB/s (empty = unlimited)")
        if self.config.get("speed_limit_kbps"):
            self.speed_entry.set_text(str(self.config.get("speed_limit_kbps")))
        save_defaults_btn = Gtk.Button(label="Save Defaults")
        save_defaults_btn.connect("clicked", self.on_save_defaults)
        change_folder_btn = Gtk.Button(label="Change Folder")
        change_folder_btn.connect("clicked", self.on_change_folder)

        self.settings_box.pack_start(Gtk.Label(label="Format:"), False, False, 0)
        self.settings_box.pack_start(self.format_combo, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Quality:"), False, False, 0)
        self.settings_box.pack_start(self.quality_entry, False, False, 0)
        self.settings_box.pack_start(self.subs_check, False, False, 0)
        self.settings_box.pack_start(self.clipboard_check, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Speed KB/s:"), False, False, 0)
        self.settings_box.pack_start(self.speed_entry, False, False, 0)
        self.conn_adj = Gtk.Adjustment(value=float(self.config.get("aria_connections", 16)), lower=1, upper=16, step_increment=1, page_increment=4)
        self.conn_spin = Gtk.SpinButton()
        self.conn_spin.set_adjustment(self.conn_adj)
        self.conn_spin.set_numeric(True)
        # Split count can remain higher (internal segmentation) but clamp minimum sensible values
        self.split_adj = Gtk.Adjustment(value=float(self.config.get("aria_splits", 32)), lower=4, upper=64, step_increment=1, page_increment=4)
        self.split_spin = Gtk.SpinButton()
        self.split_spin.set_adjustment(self.split_adj)
        self.split_spin.set_numeric(True)
        self.frag_adj = Gtk.Adjustment(value=float(self.config.get("fragment_concurrency", 16)), lower=1, upper=32, step_increment=1, page_increment=2)
        self.frag_spin = Gtk.SpinButton()
        self.frag_spin.set_adjustment(self.frag_adj)
        self.frag_spin.set_numeric(True)
        self.category_combo = Gtk.ComboBoxText()
        self.category_combo.append("idm", "Categorized (videos/audio)")
        self.category_combo.append("flat", "Single folder")
        self.category_combo.set_active_id(self.config.get("category_mode", "idm"))
        self.max_concurrent_adj = Gtk.Adjustment(value=float(self.config.get("max_concurrent", 2)), lower=1, upper=10, step_increment=1, page_increment=1)
        self.max_concurrent_spin = Gtk.SpinButton()
        self.max_concurrent_spin.set_adjustment(self.max_concurrent_adj)
        self.max_concurrent_spin.set_numeric(True)
        self.settings_box.pack_start(Gtk.Label(label="Connections:"), False, False, 0)
        self.settings_box.pack_start(self.conn_spin, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Splits:"), False, False, 0)
        self.settings_box.pack_start(self.split_spin, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Fragments:"), False, False, 0)
        self.settings_box.pack_start(self.frag_spin, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Folders:"), False, False, 0)
        self.settings_box.pack_start(self.category_combo, False, False, 0)
        self.settings_box.pack_start(Gtk.Label(label="Max concurrent:"), False, False, 0)
        self.settings_box.pack_start(self.max_concurrent_spin, False, False, 0)
        self.settings_box.pack_start(save_defaults_btn, False, False, 0)
        self.settings_box.pack_start(change_folder_btn, False, False, 0)
        sc_settings = Gtk.ScrolledWindow()
        sc_settings.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        sc_settings.set_hexpand(True)
        sc_settings.add(self.settings_box)
        # Give a minimum height; allow horizontal scrolling if too narrow
        sc_settings.set_min_content_height(70)
        queue_page.pack_start(sc_settings, False, False, 0)

        # Queue model and view
        self.liststore = Gtk.ListStore(str, str, int, str, str)
        self.treeview = Gtk.TreeView(model=self.liststore)
        self.treeview.set_rules_hint(True)
        title_renderer = Gtk.CellRendererText()
        try:
            title_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        except Exception:
            pass
        title_col = Gtk.TreeViewColumn(title="Title")
        title_col.pack_start(title_renderer, True)
        title_col.add_attribute(title_renderer, 'text', 1)
        self.treeview.append_column(title_col)
        prog_renderer = Gtk.CellRendererProgress()
        prog_col = Gtk.TreeViewColumn(title="Progress")
        prog_col.pack_start(prog_renderer, True)
        prog_col.add_attribute(prog_renderer, 'value', 2)
        prog_col.add_attribute(prog_renderer, 'text', 3)
        self.treeview.append_column(prog_col)
        status_renderer = Gtk.CellRendererText()
        status_col = Gtk.TreeViewColumn(title="Status")
        status_col.pack_start(status_renderer, True)
        status_col.add_attribute(status_renderer, 'text', 4)
        self.treeview.append_column(status_col)
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.treeview)
        queue_page.pack_start(scrolled, True, True, 0)
        self.notebook.append_page(queue_page, Gtk.Label(label="Queue"))

        # ===== History tab =====
        history_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        hist_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_hist_open = Gtk.Button(label="Open File")
        btn_hist_open.connect("clicked", self.on_hist_open_file)
        btn_hist_folder = Gtk.Button(label="Open Folder")
        btn_hist_folder.connect("clicked", self.on_hist_open_folder)
        btn_hist_retry = Gtk.Button(label="Retry")
        btn_hist_retry.connect("clicked", self.on_hist_retry)
        btn_hist_clear = Gtk.Button(label="Clear History")
        btn_hist_clear.connect("clicked", self.on_hist_clear)
        hist_actions.pack_start(btn_hist_open, False, False, 0)
        hist_actions.pack_start(btn_hist_folder, False, False, 0)
        hist_actions.pack_start(btn_hist_retry, False, False, 0)
        hist_actions.pack_end(btn_hist_clear, False, False, 0)
        history_page.pack_start(hist_actions, False, False, 0)

        self.hist_store = Gtk.ListStore(str, str, str, str, str)
        self.hist_view = Gtk.TreeView(model=self.hist_store)
        for (title_txt, idx) in [("Time", 0), ("Title", 1), ("Status", 2), ("Path", 3)]:
            r = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(title=title_txt)
            col.pack_start(r, True)
            col.add_attribute(r, 'text', idx)
            self.hist_view.append_column(col)
        sc_hist = Gtk.ScrolledWindow()
        sc_hist.add(self.hist_view)
        history_page.pack_start(sc_hist, True, True, 0)
        self.notebook.append_page(history_page, Gtk.Label(label="History"))

        # State
        self.queue = []
        self.is_downloading = False
        self.already_seen_urls = set()
        self._last_clip_text = ""
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._mini_popup = None
        self._mini_title_lbl = None
        self._mini_status_lbl = None
        self._mini_progress_bar = None
        self._mini_idx = None
        self._big_popup = None
        self._big_list = None
        self._big_rows = {}
        self._big_header_label = None
        self.history = self.load_history()
        self.populate_history_view()

        # DnD and context menu
        targets = [Gtk.TargetEntry.new("text/uri-list", 0, 0), Gtk.TargetEntry.new("text/plain", 0, 1)]
        self.treeview.drag_dest_set(Gtk.DestDefaults.ALL, targets, Gdk.DragAction.COPY)
        self.treeview.connect("drag-data-received", self.on_drag_data_received)
        self.treeview.connect("button-press-event", self.on_treeview_button_press)

        # Clipboard monitor timer
        GLib.timeout_add_seconds(2, self.check_clipboard_periodic)
        self.show_all()
        # Ensure we don't overflow very small screens
        GLib.idle_add(self._enforce_max_window_size)
        # Extra safety: clamp a few more times while widgets settle and WM applies constraints
        try:
            self._clamp_checks_left = 10
        except Exception:
            self._clamp_checks_left = 0
        GLib.timeout_add(200, self._clamp_window_size_periodic)
        # Safe to update counts now
        self.update_dashboard_counts()
        # Inject custom CSS for IDM-style styling
        css = Gtk.CssProvider()
        css_data = b"""
        /* ========================================
           FastTube Downloader - IDM-Style Theme
           Matching Chrome Extension Design
           ======================================== */
        
        /* Color Variables (matching popup.css) */
        /* Primary: #0d6efd, #0b5ed7, #3d8bfd */
        /* Success: #28a745 | Warning: #ffc107 | Danger: #dc3545 */
        /* Backgrounds: #1a1d23, #23262d, #2b2f36, #32363e */
        /* Text: #e8eef4, #a8b3c1, #6c757d */
        /* Borders: #3a3e47, #4a4e57 */
        
        /* ========== Main Window ========== */
        window { 
            background: #1a1d23;
            color: #e8eef4;
        }
        
        /* ========== Header Bar ========== */
        headerbar { 
            background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%); 
            border-bottom: 2px solid #0b5ed7;
            color: #ffffff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        headerbar button { 
            background: rgba(255, 255, 255, 0.12); 
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: 600;
            transition: all 200ms ease;
        }
        headerbar button:hover { 
            background: rgba(255, 255, 255, 0.22);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        headerbar button:active {
            background: rgba(255, 255, 255, 0.3);
        }
        
        /* ========== FastTube Header Section ========== */
        .fasttube-header { 
            font-weight: 600; 
            font-size: 14px; 
            color: #e8eef4;
            letter-spacing: 0.3px;
        }
        
        /* ========== Settings Strip ========== */
        .settings-strip { 
            padding: 14px 16px; 
            border-top: 1px solid #2a2e35; 
            border-bottom: 1px solid #2a2e35;
            background: #23262d;
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.15);
        }
        .settings-strip label { 
            color: #a8b3c1; 
            font-size: 12px;
            font-weight: 500;
        }
        
        /* ========== TreeView - Downloads List ========== */
        treeview { 
            background: #23262d; 
            color: #e8eef4;
            border-radius: 8px;
        }
        treeview.view { 
            background: #23262d;
            border-radius: 8px;
        }
        treeview.view row { 
            padding: 8px 4px;
            border-bottom: 1px solid #2a2e35;
            transition: all 150ms ease;
        }
        treeview.view row:selected { 
            background: linear-gradient(90deg, #0d6efd 0%, #0b5ed7 100%); 
            color: #ffffff;
            box-shadow: 0 2px 4px rgba(13, 110, 253, 0.3);
        }
        treeview.view row:hover { 
            background: #2b2f36;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
        }
        treeview.view row:selected:hover {
            background: linear-gradient(90deg, #3d8bfd 0%, #0d6efd 100%);
        }
        treeview header button {
            background: #2b2f36;
            color: #a8b3c1;
            border: 1px solid #3a3e47;
            border-radius: 0;
            padding: 8px 12px;
            font-weight: 600;
            font-size: 12px;
        }
        treeview header button:hover {
            background: #32363e;
            color: #e8eef4;
        }
        
        /* ========== Progress Bars ========== */
        progressbar { 
            min-height: 22px;
            border-radius: 8px;
        }
        progressbar trough { 
            background: #1a1d23; 
            border: 1px solid #2a2e35;
            border-radius: 8px;
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
        }
        progressbar progress { 
            background: linear-gradient(90deg, #0d6efd 0%, #3d8bfd 100%); 
            border-radius: 7px;
            box-shadow: 0 1px 3px rgba(13, 110, 253, 0.4);
        }
        /* Pulsing effect for active downloads */
        progressbar.pulse progress {
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        /* ========== Buttons ========== */
        button { 
            background: #2d3139; 
            color: #e8eef4; 
            border: 1px solid #3a4048; 
            border-radius: 6px; 
            padding: 8px 14px;
            font-weight: 500;
            font-size: 13px;
            transition: all 150ms ease;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
        button:hover { 
            background: #363c46; 
            border-color: #4a4e57;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            transform: translateY(-1px);
        }
        button:active { 
            background: #3d4350; 
            transform: translateY(0);
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
        }
        
        /* Primary action buttons (Add, Start, etc.) */
        button.suggested-action {
            background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%);
            color: #ffffff;
            border: none;
            box-shadow: 0 2px 6px rgba(13, 110, 253, 0.3);
        }
        button.suggested-action:hover {
            background: linear-gradient(135deg, #3d8bfd 0%, #0d6efd 100%);
            box-shadow: 0 3px 8px rgba(13, 110, 253, 0.4);
            transform: translateY(-1px);
        }
        button.suggested-action:active {
            background: linear-gradient(135deg, #0b5ed7 0%, #0a52c7 100%);
            transform: translateY(0);
        }
        
        /* Danger/Remove buttons */
        button.destructive-action {
            background: transparent;
            color: #dc3545;
            border: 1px solid #dc3545;
        }
        button.destructive-action:hover {
            background: #dc3545;
            color: #ffffff;
            box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
        }
        
        /* ========== Notebook Tabs ========== */
        notebook { 
            background: #1a1d23;
        }
        notebook > header {
            background: #23262d;
            border-bottom: 2px solid #2a2e35;
        }
        notebook tab { 
            background: transparent; 
            color: #a8b3c1;
            border: none;
            border-bottom: 3px solid transparent;
            padding: 12px 20px;
            font-weight: 600;
            font-size: 13px;
            transition: all 150ms ease;
        }
        notebook tab:hover {
            color: #e8eef4;
            background: #2b2f36;
        }
        notebook tab:checked { 
            background: transparent;
            color: #3d8bfd;
            border-bottom-color: #0d6efd;
        }
        
        /* ========== Entry Fields ========== */
        entry { 
            background: #23262d; 
            color: #e8eef4;
            border: 1px solid #3a4048;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            transition: all 150ms ease;
        }
        entry:focus {
            border-color: #0d6efd;
            box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.15);
            background: #2b2f36;
        }
        entry::placeholder {
            color: #6c757d;
        }
        
        /* ========== ComboBox / Dropdown ========== */
        combobox button {
            background: #23262d;
            border: 1px solid #3a4048;
            border-radius: 6px;
        }
        combobox button:hover {
            background: #2b2f36;
            border-color: #4a4e57;
        }
        
        /* ========== SpinButton ========== */
        spinbutton {
            background: #23262d;
            border: 1px solid #3a4048;
            border-radius: 6px;
        }
        spinbutton entry {
            border: none;
        }
        spinbutton button {
            background: #2d3139;
            border: none;
            border-left: 1px solid #3a4048;
        }
        spinbutton button:hover {
            background: #363c46;
        }
        
        /* ========== Scrollbars ========== */
        scrollbar {
            background: transparent;
        }
        scrollbar trough {
            background: #23262d;
            border-radius: 4px;
        }
        scrollbar slider {
            background: #4a4e57;
            border-radius: 4px;
            min-width: 8px;
            min-height: 40px;
        }
        scrollbar slider:hover {
            background: #5a5e67;
        }
        scrollbar slider:active {
            background: #6a6e77;
        }
        scrollbar.vertical slider {
            min-width: 8px;
        }
        scrollbar.horizontal slider {
            min-height: 8px;
        }
        
        /* ========== Checkbutton ========== */
        checkbutton {
            color: #e8eef4;
        }
        checkbutton check {
            background: #23262d;
            border: 1px solid #3a4048;
            border-radius: 4px;
        }
        checkbutton check:checked {
            background: #0d6efd;
            border-color: #0d6efd;
        }
        checkbutton check:hover {
            border-color: #4a4e57;
        }
        
        /* ========== Frame ========== */
        frame {
            border: 1px solid #2a2e35;
            border-radius: 8px;
        }
        frame > border {
            border-radius: 8px;
        }
        
        /* ========== Scrolled Window ========== */
        scrolledwindow {
            border-radius: 8px;
        }
        
        /* ========== Mini Popup Window ========== */
        .mini-popup { 
            background: #23262d; 
            color: #e8eef4;
            border: 1px solid #3a3e47;
            border-radius: 10px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
        }
        
        /* ========== Separator ========== */
        separator {
            background: #2a2e35;
            min-width: 1px;
            min-height: 1px;
        }
        
        /* ========== Utilities ========== */
        .help-title {
            font-weight: 700;
            font-size: 14px;
            color: #0d6efd;
        }
        
        /* Status-based styling helpers */
        .status-downloading {
            color: #3d8bfd;
        }
        .status-completed {
            color: #28a745;
        }
        .status-paused {
            color: #ffc107;
        }
        .status-error {
            color: #dc3545;
        }
        .status-queued {
            color: #6c757d;
        }
        """
        try:
            css.load_from_data(css_data)
            Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        except Exception:
            pass
        # Start progress pulse timer
        GLib.timeout_add(450, self._pulse_progress_rows)

        # Control server
        threading.Thread(target=self._start_control_server, daemon=True).start()

        # Configure-event hook to prevent accidental overflow growth
        self.connect("configure-event", self._on_configure)

        # Apply initial sensitivity for controls based on selected format
        try:
            self.on_format_changed(self.format_combo)
        except Exception:
            pass

    def on_format_changed(self, combo):
        try:
            fmt = combo.get_active_text() or ''
            is_generic = (fmt == 'Generic File')
            # Disable media-specific widgets for generic files
            self.quality_entry.set_sensitive(not is_generic)
            self.subs_check.set_sensitive(not is_generic)
        except Exception:
            pass

    def _enforce_max_window_size(self):
        try:
            sw, sh = self._get_screen_dimensions()
            # Hard maximum (logical units): workarea minus safe margins
            max_w = int(sw) - 40
            max_h = int(sh) - 60
            try:
                geom_w, geom_h = self.get_size()  # logical units
            except Exception:
                geom_w = self.get_allocated_width()
                geom_h = self.get_allocated_height()
            new_w = min(geom_w, max_w)
            new_h = min(geom_h, max_h)
            if new_w != geom_w or new_h != geom_h:
                self.resize(new_w, new_h)
        except Exception:
            pass
        return False

    def _on_configure(self, widget, event):
        try:
            sw, sh = self._get_screen_dimensions()
            max_w = int(sw) - 40
            max_h = int(sh) - 60
            try:
                geom_w, geom_h = self.get_size()  # logical units
            except Exception:
                geom_w = widget.get_allocated_width()
                geom_h = widget.get_allocated_height()
            if geom_w > max_w or geom_h > max_h:
                widget.resize(min(geom_w, max_w), min(geom_h, max_h))
            # Persist latest size so the app remembers user's preference
            try:
                if not hasattr(self, '_size_save_pending') or not self._size_save_pending:
                    self._size_save_pending = True
                    def _save_size():
                        try:
                            w, h = self.get_size()
                            if isinstance(self.config, dict):
                                self.config['window_width'] = int(w)
                                self.config['window_height'] = int(h)
                                os.makedirs(CONFIG_DIR, exist_ok=True)
                                with open(CONFIG_FILE, 'w') as f:
                                    json.dump(self.config, f, indent=4)
                        except Exception:
                            pass
                        finally:
                            self._size_save_pending = False
                        return False
                    GLib.timeout_add(400, _save_size)
            except Exception:
                pass
        except Exception:
            pass
        return False

    def _clamp_window_size_periodic(self):
        try:
            if getattr(self, '_clamp_checks_left', 0) <= 0:
                return False
            self._clamp_checks_left -= 1
            self._enforce_max_window_size()
        except Exception:
            return False
        return True

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return None

    # ===== History persistence and dashboard =====
    def load_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    return json.load(f) or []
        except Exception:
            pass
        return []

    def save_history(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def populate_history_view(self):
        self.hist_store.clear()
        for rec in self.history:
            self.hist_store.append([
                rec.get('time',''),
                rec.get('title','Unknown'),
                rec.get('status',''),
                rec.get('path',''),
                rec.get('url',''),
            ])

    def append_history(self, title, url, status, path):
        import datetime
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rec = { 'time': ts, 'title': title or 'Unknown', 'url': url, 'status': status, 'path': path or '' }
        self.history.append(rec)
        self.save_history()
        self.hist_store.append([rec['time'], rec['title'], rec['status'], rec['path'], rec['url']])
        self.update_dashboard_counts()

    def update_dashboard_counts(self):
        queued = sum(1 for it in self.queue if it.status == 'Queued')
        downloading = sum(1 for it in self.queue if it.status == 'Downloading...')
        completed = sum(1 for rec in self.history if rec.get('status') == 'Completed')
        try:
            self.lbl_counts.set_text(f"Queued: {queued} | Downloading: {downloading} | Completed: {completed}")
        except Exception:
            pass

    # ===== History actions =====
    def _get_selected_history(self):
        sel = self.hist_view.get_selection()
        model, itr = sel.get_selected()
        if itr is None:
            return None
        time_s, title, status, path, url = model[itr]
        return { 'time': time_s, 'title': title, 'status': status, 'path': path, 'url': url, 'iter': itr }

    def on_hist_open_file(self, widget):
        rec = self._get_selected_history()
        if not rec or not rec['path']:
            return
        try:
            subprocess.Popen(["xdg-open", rec['path']])
        except Exception as e:
            self.show_message(f"Unable to open file: {e}")

    def on_hist_open_folder(self, widget):
        rec = self._get_selected_history()
        if not rec:
            return
        path = rec['path']
        folder = os.path.dirname(path) if path else os.path.expanduser(self.config.get("download_folder", "~"))
        try:
            subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            self.show_message(f"Unable to open folder: {e}")

    def on_hist_retry(self, widget):
        rec = self._get_selected_history()
        if not rec or not rec['url']:
            return
        self.add_url(rec['url'])
        if not self.is_downloading:
            self.on_start_downloads(None)
        self.notebook.set_current_page(0)

    def on_hist_clear(self, widget):
        self.history = []
        self.save_history()
        self.populate_history_view()
        self.update_dashboard_counts()

    def on_setup_complete(self, widget):
        # After setup window closes, load config and build UI on this window
        self.config = self.load_config()
        if self.config:
            # Remove any existing children (if any) before building
            for child in self.get_children():
                self.remove(child)
            self.build_ui()
            self.show_all()

    def get_video_title(self, url):
        # Avoid UI blocking: only used from background thread
        # Try fast oEmbed
        try:
            oembed_url = "https://www.youtube.com/oembed?%s" % urllib.parse.urlencode({
                "url": url,
                "format": "json"
            })
            req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                title = (data.get("title") or "").strip()
                if title:
                    return title
        except Exception:
            pass
        # Fallback to yt-dlp with longer timeout
        try:
            result = subprocess.run(["yt-dlp", "--no-playlist", "--get-title", url], capture_output=True, text=True, check=True, timeout=45)
            title = result.stdout.strip()
            return next((line for line in title.splitlines() if line.strip()), "Unknown") or "Unknown"
        except Exception as e:
            print(f"Title fetch error: {e}")
            return "Unknown"

    def fetch_title_background(self, item):
        # Retry title fetch with longer timeout and update UI when available
        try:
            result = subprocess.run(["yt-dlp", "--no-playlist", "--get-title", item.url], capture_output=True, text=True, check=True, timeout=45)
            title = result.stdout.strip()
            title = next((line for line in title.splitlines() if line.strip()), None)
            if title:
                try:
                    idx = self.queue.index(item)
                except ValueError:
                    return
                self.update_title(idx, title)
        except Exception:
            # Keep existing title
            pass

    def on_add_download(self, widget):
        url = self.url_entry.get_text().strip()
        if not url:
            self.show_message("Please enter a URL!")
            return
        self.add_url(url)
        self.url_entry.set_text("")

    def add_url(self, url: str, fmt: str = None, qual: str = None, subs_active: bool = None):
        # Detect playlist more accurately: only treat as playlist if it's a playlist page
        # or a link with list= but without a specific video id.
        try:
            if self._is_playlist_url(url):
                self.add_playlist(url)
                return
        except Exception:
            pass
        # Generic file detection if enabled and format selected
        try:
            if self.config.get("enable_generic", True):
                chosen_fmt = fmt or self.format_combo.get_active_text()
                if chosen_fmt == 'Generic File' or self._looks_like_direct_file(url):
                    self.add_generic_file(url)
                    return
        except Exception:
            pass
        # Non-blocking: add placeholder, fetch title in background
        item = DownloadItem(url, "Fetching title...")
        item.kind = 'media'
        item.req_format = fmt or self.format_combo.get_active_text()
        item.req_quality = qual or (self.quality_entry.get_text() or "")
        if subs_active is None:
            subs_active = self.subs_check.get_active()
        item.req_subs = subs_active
        self.queue.append(item)
        item.treeiter = self.liststore.append([item.url, item.title, item.progress, f"{item.progress}%", item.status])
        # Background title refinement
        threading.Thread(target=self.fetch_title_background, args=(item,), daemon=True).start()
        # Auto start downloads if enabled
        if self.config.get("auto_start", True) and not self.is_downloading:
            self.on_start_downloads(None)

    def add_playlist(self, url):
        # Robust playlist expansion: use yt-dlp JSON flat playlist; avoid duplicates.
        probe_cmd = ["yt-dlp", "--flat-playlist", "--dump-json", url]
        added = 0
        playlist_title = None
        
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().splitlines()
            
            # Extract playlist title from first entry
            for raw in lines:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                    # Get playlist title from metadata
                    if not playlist_title and (data.get('playlist_title') or data.get('playlist')):
                        playlist_title = data.get('playlist_title') or data.get('playlist')
                        # Clean up playlist title for use as folder name
                        if playlist_title:
                            # Remove invalid filename characters
                            playlist_title = re.sub(r'[<>:"/\\|?*]', '', playlist_title)
                            # Limit length to avoid path issues
                            if len(playlist_title) > 100:
                                playlist_title = playlist_title[:100]
                        break
                except Exception:
                    continue
            
            # If no playlist title found, try to extract from URL
            if not playlist_title:
                try:
                    # Try yt-dlp to get playlist info
                    info_cmd = ["yt-dlp", "--flat-playlist", "--print", "playlist_title", url]
                    info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=10)
                    if info_result.returncode == 0 and info_result.stdout.strip():
                        playlist_title = info_result.stdout.strip().splitlines()[0]
                        playlist_title = re.sub(r'[<>:"/\\|?*]', '', playlist_title)
                        if len(playlist_title) > 100:
                            playlist_title = playlist_title[:100]
                except Exception:
                    pass
            
            # Fallback: use generic name with timestamp
            if not playlist_title:
                import time
                playlist_title = f"Playlist_{int(time.time())}"
            
            urls = []
            if parse_flat_playlist_lines:
                urls = parse_flat_playlist_lines(lines)
            else:
                # Minimal inline fallback to avoid tight coupling if import fails
                seen_ids = set()
                for raw in lines:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        data = json.loads(raw)
                    except Exception:
                        continue
                    vid_id = data.get('id') or data.get('url')
                    if not vid_id or vid_id in seen_ids:
                        continue
                    seen_ids.add(vid_id)
                    urls.append(f"https://www.youtube.com/watch?v={vid_id}")

            # Enqueue items
            if not urls:
                self.show_message("Playlist appears empty or inaccessible.")
                return
            
            print(f"[GUI] Adding playlist '{playlist_title}' with {len(urls)} videos", file=sys.stderr)
            
            for full_url in urls:
                item = DownloadItem(full_url, "Fetching title...")
                item.kind = 'media'
                item.playlist_name = playlist_title  # Store playlist name for folder organization
                self.queue.append(item)
                item.treeiter = self.liststore.append([item.url, item.title, item.progress, f"{item.progress}%", item.status])
                # Fetch titles in background for nicer display
                threading.Thread(target=self.fetch_title_background, args=(item,), daemon=True).start()
                added += 1
            # Auto start if setting enabled
            if self.config.get("auto_start", True) and not self.is_downloading:
                self.on_start_downloads(None)
        except subprocess.CalledProcessError:
            self.show_message("Error detecting playlist; treating as single video.")
            # Fallback: enqueue original URL as a single item
            self.add_url(url)

    def _is_playlist_url(self, url: str) -> bool:
        """Return True only for actual playlist links, not single videos that include a list= param.

        Rules:
        - youtube.com/playlist?list=... -> playlist
        - watch URLs: treat as playlist only if they have list= but no explicit video id (v param)
        - youtu.be/<id>[?list=...] is a single video even if list= present
        - shorts URLs are single videos
        """
        try:
            p = urllib.parse.urlparse(url)
            netloc = (p.netloc or '').lower()
            path = (p.path or '').lower()
            qs = urllib.parse.parse_qs(p.query or '')

            def has_video_id() -> bool:
                # watch?v=...
                if qs.get('v') and qs['v'][0].strip():
                    return True
                # youtu.be/<id>
                seg = path.strip('/')
                if 'youtu.be' in netloc and seg and not seg.startswith('playlist'):
                    return True
                # shorts/<id>
                if '/shorts/' in path:
                    return True
                return False

            # Explicit playlist page
            if 'youtube.com' in netloc and path.startswith('/playlist'):
                return True
            # Links with list= but no video id are considered playlist
            if 'list' in qs and not has_video_id():
                return True
        except Exception:
            pass
        return False

    def _looks_like_direct_file(self, url: str) -> bool:
        """Heuristic: URL ends with a known file extension or has one before query fragment."""
        try:
            p = urllib.parse.urlparse(url)
            path = p.path or ''
            # Strip any trailing slashes
            path = path.rstrip('/')
            if not path:
                return False
            _, ext = os.path.splitext(path.lower())
            if not ext:
                return False
            for exts in self.config.get('generic_extensions_map', {}).values():
                if ext in exts:
                    return True
            return False
        except Exception:
            return False

    def _guess_filename(self, url: str) -> str:
        try:
            p = urllib.parse.urlparse(url)
            name = os.path.basename(p.path) or 'download'
            if '?' in name:
                name = name.split('?',1)[0]
            return name
        except Exception:
            return 'download'

    def add_generic_file(self, url: str):
        title = self._guess_filename(url)
        item = DownloadItem(url, title)
        item.kind = 'generic'
        item.req_format = 'Generic File'
        self.queue.append(item)
        item.treeiter = self.liststore.append([item.url, item.title, item.progress, f"{item.progress}%", item.status])
        # Optionally perform HEAD request to refine size/title asynchronously
        threading.Thread(target=self._probe_generic_metadata, args=(item,), daemon=True).start()
        if self.config.get("auto_start", True) and not self.is_downloading:
            self.on_start_downloads(None)

    def _probe_generic_metadata(self, item):
        import urllib.request
        try:
            req = urllib.request.Request(item.url, method='HEAD', headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                disp = resp.headers.get('Content-Disposition','')
                if 'filename=' in disp:
                    fn = disp.split('filename=')[1].strip('"')
                    if fn:
                        self._update_item_title(item, fn)
                clen = resp.headers.get('Content-Length')
                if clen and clen.isdigit():
                    # Store total size in human bytes form (rough MiB/KB)
                    sz = int(clen)
                    units = ['B','KiB','MiB','GiB','TiB']
                    u = 0
                    val = float(sz)
                    while val >= 1024 and u < len(units)-1:
                        val /= 1024.0; u += 1
                    item.total = f"{val:.1f}{units[u]}"
                    self._update_progress_text(item)
        except Exception:
            pass

    def on_start_downloads(self, widget):
        if self.is_downloading:
            return
        self.is_downloading = True
        threading.Thread(target=self._spooler, daemon=True).start()

    def on_stop_downloads(self, widget):
        # Stop queue processing and terminate current process if any
        self.is_downloading = False
        for item in self.queue:
            if item.process and item.process.poll() is None:
                try:
                    item.process.terminate()
                except Exception:
                    pass
        for it in self.queue:
            if it.status == "Downloading...":
                it.status = "Paused"
                if it.treeiter:
                    self.liststore.set(it.treeiter, 4, "Paused")
        self.update_dashboard_counts()

    def on_remove_selected(self, widget):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        # Find and remove from queue if not currently downloading
        url = model[treeiter][0]
        # If downloading, attempt to stop process
        for i, qi in enumerate(list(self.queue)):
            if qi.url == url:
                if qi.process and qi.process.poll() is None:
                    try:
                        qi.process.terminate()
                    except Exception:
                        pass
                self.queue.pop(i)
                break
        self.liststore.remove(treeiter)
        self.update_dashboard_counts()

    def on_open_folder(self, widget):
        folder = os.path.expanduser(self.config.get("download_folder", "~"))
        try:
            subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            self.show_message(f"Unable to open folder: {e}")

    def on_save_defaults(self, widget):
        # Persist current controls as defaults
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.config["default_format"] = self.format_combo.get_active_text()
        self.config["preferred_quality"] = self.quality_entry.get_text()
        self.config["subs"] = self.subs_check.get_active()
        self.config["clipboard_auto"] = self.clipboard_check.get_active()
        sp = self.speed_entry.get_text().strip()
        self.config["speed_limit_kbps"] = int(sp) if sp.isdigit() else ""
        self.config["max_concurrent"] = int(self.max_concurrent_spin.get_value())
        self.config["aria_connections"] = int(self.conn_spin.get_value())
        self.config["aria_splits"] = int(self.split_spin.get_value())
        self.config["fragment_concurrency"] = int(self.frag_spin.get_value())
        active_id = self.category_combo.get_active_id() or "idm"
        self.config["category_mode"] = active_id
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=4)
        self.show_message("Defaults saved.")

    def on_change_folder(self, widget):
        dialog = Gtk.FileChooserDialog(title="Select Download Folder", parent=self,
                                       action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           "Select", Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            folder = os.path.expanduser(folder)
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as exc:
                self.show_message(f"Unable to use folder: {exc}")
                dialog.destroy()
                return
            self.config["download_folder"] = folder
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        dialog.destroy()
        self.update_dashboard_counts()

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        text = data.get_text() if data else None
        if not text:
            drag_context.finish(False, False, time)
            return
        urls = []
        for token in re.split(r"[\s\r\n]+", text.strip()):
            if token.startswith("http://") or token.startswith("https://"):
                urls.append(token)
        for u in urls:
            self.add_url(u)
        drag_context.finish(True, False, time)
        self.update_dashboard_counts()

    def on_treeview_button_press(self, widget, event):
        if event.button == 3:  # Right-click
            selection = self.treeview.get_selection()
            model, treeiter = selection.get_selected()
            menu = Gtk.Menu()
            copy_item = Gtk.MenuItem(label="Copy URL")
            open_folder_item = Gtk.MenuItem(label="Open Folder")
            copy_item.connect("activate", lambda *_: self.copy_selected_url())
            open_folder_item.connect("activate", self.on_open_folder)
            menu.append(copy_item)
            menu.append(open_folder_item)
            menu.show_all()
            try:
                menu.popup_at_pointer(event)
            except Exception:
                menu.popup(None, None, None, None, event.button, event.time)
            return True
        return False

    def copy_selected_url(self):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        url = model[treeiter][0]
        self.clipboard.set_text(url, -1)

    def check_clipboard_periodic(self):
        if not self.clipboard_check.get_active():
            return True
        try:
            # Use async request to avoid blocking the main loop
            def _on_text(clip, text):
                try:
                    text = text or ""
                    if text and text != self._last_clip_text:
                        self._last_clip_text = text
                        m = re.search(r"https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=[^\s&]+|playlist\?list=[^\s&]+)|youtu\.be/[^\s&]+)", text)
                        url = None
                        if m:
                            url = m.group(0)
                        else:
                            # Try generic direct-file detection: ends with a known extension
                            gm = re.search(r"https?://[^\s]+\.(?:zip|rar|7z|tar|gz|tar\.gz|tgz|bz2|iso|img|pdf|docx?|xlsx?|pptx?|mp3|m4a|aac|flac|wav|ogg|mp4|mkv|webm|avi|mov|flv|wmv|jpg|jpeg|png|gif|bmp|webp)(?:\?[^\s]*)?", text, re.IGNORECASE)
                            if gm:
                                url = gm.group(0)
                        if url and url not in self.already_seen_urls:
                            self.already_seen_urls.add(url)
                            self.add_url(url)
                            self.update_dashboard_counts()
                except Exception:
                    pass
            self.clipboard.request_text(_on_text)
        except Exception:
            pass
        return True

    # ============== Control server (extension bridge) ==============
    def _start_control_server(self):
        HOST, PORT = '127.0.0.1', 47653
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((HOST, PORT))
            sock.listen(5)
        except Exception as e:
            print(f"Control server bind failed: {e}")
            return
        print(f"Control server listening on {HOST}:{PORT}")
        while True:
            try:
                conn, _ = sock.accept()
            except Exception:
                break
            threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def _handle_client(self, conn):
        try:
            data = b''
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            text = data.decode('utf-8', errors='ignore').strip()
            if not text:
                return
            try:
                req = json.loads(text.splitlines()[0])
            except Exception:
                req = {"action": "enqueue", "url": text}
            # Bring window to front
            if req.get('action') == 'show':
                def _bring():
                    try:
                        self.show_all()
                        try:
                            self.deiconify()
                        except Exception:
                            pass
                        try:
                            # Best-effort focus/raise
                            if hasattr(self, 'present_with_time'):
                                self.present_with_time(Gdk.CURRENT_TIME)
                            else:
                                self.present()
                            gdk_win = self.get_window()
                            if gdk_win is not None:
                                try:
                                    gdk_win.raise_()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        try:
                            self.set_urgency_hint(True)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    return False
                GLib.idle_add(_bring)
                try:
                    conn.sendall((json.dumps({"status": "ok"}) + '\n').encode('utf-8'))
                except Exception:
                    pass
                return
            if req.get('action') == 'enqueue' and req.get('url'):
                fmt_id = req.get('formatId')
                fmt = fmt_id or req.get('format') or self.format_combo.get_active_text()
                qual = "" if fmt_id else (req.get('quality') or self.quality_entry.get_text())
                subs = req.get('subs')
                if isinstance(subs, str):
                    subs_active = subs.lower().startswith('y') or subs.lower() == 'true'
                else:
                    subs_active = bool(subs) if subs is not None else self.subs_check.get_active()

                # Create the DownloadItem synchronously so we can attach the
                # client connection and stream progress updates back over the
                # same socket. This avoids requiring the extension/user to
                # poll for status.
                try:
                    item = DownloadItem(req['url'], req.get('title') or 'Fetching title...')
                    item.kind = 'media'
                    item.req_format = fmt or self.format_combo.get_active_text()
                    item.req_quality = qual or (self.quality_entry.get_text() or "")
                    item.req_subs = subs_active
                    # Attach client connection and request id if present
                    item.client_conn = conn
                    item.client_req_id = req.get('requestId')
                    # Append to queue and UI
                    self.queue.append(item)
                    item.treeiter = self.liststore.append([item.url, item.title, item.progress, f"{item.progress}%", item.status])
                    threading.Thread(target=self.fetch_title_background, args=(item,), daemon=True).start()
                    print(f"[GUI] accepted enqueue from native host: {req['url']}", file=sys.stderr)
                    # Start downloads if needed
                    if self.config.get("auto_start", True) and not self.is_downloading:
                        self.on_start_downloads(None)
                    # Send initial queued response but keep the socket open for
                    # streaming updates. The caller (bridge) will remain blocked
                    # reading until we close the connection when finished.
                    try:
                        conn.sendall((json.dumps({"status": "queued", "requestId": item.client_req_id}) + '\n').encode('utf-8'))
                    except Exception:
                        # ignore send errors; we will still attempt to stream later
                        pass
                    resp = {"status": "queued"}
                    # Do not close conn here; other code will write updates.
                    return
                except Exception as e:
                    resp = {"status": "error", "message": str(e)}
            else:
                resp = {"status": "error", "message": "Invalid request"}
            try:
                conn.sendall((json.dumps(resp) + '\n').encode('utf-8'))
            except Exception:
                pass
        except Exception as e:
            try:
                conn.sendall((json.dumps({"status": "error", "message": str(e)}) + '\n').encode('utf-8'))
            except Exception:
                pass
        finally:
            # If this connection wasn't attached to a DownloadItem for
            # streaming progress, close it now. If it is attached the item
            # lifecycle will close it when complete.
            try:
                # check whether any queue item references this conn
                attached = any(getattr(it, 'client_conn', None) is conn for it in self.queue)
                if not attached:
                    conn.close()
            except Exception:
                pass

    def process_queue(self):
        folder = os.path.expanduser(self.config["download_folder"])
        for idx, item in enumerate(self.queue):
            if not self.is_downloading:
                break
            self.update_status(idx, "Downloading...")
            cmd = [
                FAST_YTDL, item.url, folder,
                self.format_combo.get_active_text(),
                self.quality_entry.get_text() or "",
                "y" if self.subs_check.get_active() else "n",
                str(self.config.get("speed_limit_kbps") or ""),
                str(self.config.get("aria_connections", 32)),
                str(self.config.get("aria_splits", 32)),
                str(self.config.get("fragment_concurrency", 16)),
                self.config.get("category_mode", "idm")
            ]
            print(f"Running cmd: {' '.join(cmd)}")  # Debug
            try:
                print(f"[GUI] spawn fast_ytdl: {' '.join(cmd)}", file=sys.stderr)
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
                item.process = proc
                for line in iter(proc.stdout.readline, ""):
                    line = line.strip()
                    print(f"Output line: {line}")  # Debug
                    self.parse_progress(line, idx)
                proc.wait()
                print(f"Proc exit code: {proc.returncode}")  # Debug
                if proc.returncode == 0:
                    self.update_status(idx, "Completed")
                    self.append_history(item.title, item.url, "Completed", item.dest_path or "")
                else:
                    self.update_status(idx, "Failed")
                    self.append_history(item.title, item.url, "Failed", item.dest_path or "")
            except Exception as e:
                print(f"Exception: {e}")  # Debug
                self.update_status(idx, f"Error: {str(e)}")
        self.is_downloading = False

    # ================= Concurrency spooler (new) =================
    def on_pause_selected(self, widget):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        url = model[treeiter][0]
        for it in self.queue:
            if it.url == url:
                self._pause_item(it)
                break

    def on_resume_selected(self, widget):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        url = model[treeiter][0]
        for it in self.queue:
            if it.url == url:
                self._resume_item(it)
                break

    def _spooler(self):
        try:
            while self.is_downloading:
                maxc = int(self.config.get('max_concurrent', 2))
                active = sum(1 for it in self.queue if it.process and it.process.poll() is None)
                # Start new items if slots available
                for it in self.queue:
                    if active >= maxc:
                        break
                    if it.status in ("Queued", "Paused") and (not it.process or it.process.poll() is not None):
                        self._start_item_download(it)
                        active += 1
                # Exit if idle and nothing queued
                if active == 0 and not any(it.status in ("Queued", "Paused") for it in self.queue):
                    break
                GLib.usleep(200_000)
        finally:
            self.is_downloading = False
            self.update_dashboard_counts()

    def _start_item_download(self, item):
        self._set_status(item, "Downloading...")
        folder = os.path.expanduser(self.config["download_folder"])
        # Categorize generic items by extension if in idm mode
        if getattr(item, 'kind', 'media') == 'generic' and self.config.get('category_mode','idm') == 'idm':
            try:
                subdir = self._categorize_generic(item.url)
                if subdir:
                    folder = os.path.join(folder, subdir)
                    os.makedirs(folder, exist_ok=True)
            except Exception:
                pass
        fmt = item.req_format or self.format_combo.get_active_text()
        qual = item.req_quality or (self.quality_entry.get_text() or "")
        subs_flag = 'y' if (item.req_subs if item.req_subs is not None else self.subs_check.get_active()) else 'n'
        if getattr(item, 'kind', 'media') == 'generic':
            # Direct aria2c call for generic files
            if self.config.get('aria2_rpc_enabled', False):
                # Use RPC mode: add URI and start polling
                try:
                    self._start_aria2_rpc_if_needed()
                    out_name = self._guess_filename(item.url)
                    gid = self._aria2_add_uri(item.url, folder, out_name)
                    item.gid = gid
                    threading.Thread(target=self._aria2_poll_item, args=(item,), daemon=True).start()
                    return
                except Exception as e:
                    # Fallback to direct aria2c process
                    print(f"[aria2rpc] fallback to process: {e}")
            aria_conn = int(self.config.get("aria_connections", 16))
            if aria_conn < 1: aria_conn = 1
            if aria_conn > 16: aria_conn = 16
            aria_splits = int(self.config.get("aria_splits", 32))
            if aria_splits < 4: aria_splits = 4
            speed_limit = str(self.config.get("speed_limit_kbps") or "")
            speed_arg = []
            if speed_limit.isdigit():
                speed_arg = [f"--max-overall-download-limit={speed_limit}K"]
            out_name = self._guess_filename(item.url)
            cmd = ["aria2c", "-x", str(aria_conn), "-s", str(aria_splits), "-k", "1M", "--min-split-size=1M", "--file-allocation=none"] + speed_arg + ["-d", folder, "-o", out_name, item.url]
        else:
            cmd = [
                FAST_YTDL, item.url, folder,
                fmt,
                qual,
                subs_flag,
                str(self.config.get("speed_limit_kbps") or ""),
                str(self.config.get("aria_connections", 32)),
                str(self.config.get("aria_splits", 32)),
                str(self.config.get("fragment_concurrency", 16)),
                self.config.get("category_mode", "idm")
            ]
        print("[Downloader CMD]", " ".join(cmd))
        def _reader(proc, it):
            for line in iter(proc.stdout.readline, ""):
                line = line.strip()
                if line:
                    print(f"[DL:{it.url[:20]}] {line}")
                self._parse_item_progress(line, it)
                # Update big popup row for this item
                GLib.idle_add(self._add_or_update_big_row, it)
            proc.wait()
            if it.status == "Paused":
                return
            if proc.returncode == 0:
                self._set_status(it, "Completed")
                GLib.idle_add(self._remove_big_row, it)
                self.append_history(it.title, it.url, "Completed", it.dest_path or "")
            else:
                self._set_status(it, "Failed")
                GLib.idle_add(self._remove_big_row, it)
                self.append_history(it.title, it.url, "Failed", it.dest_path or "")
        try:
            print(f"[GUI] spawn fast_ytdl: {' '.join(cmd)}", file=sys.stderr)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            item.process = proc
            threading.Thread(target=_reader, args=(proc, item), daemon=True).start()
        except Exception as e:
            self._set_status(item, f"Error: {e}")
            self.append_history(item.title, item.url, f"Error: {e}", item.dest_path or "")

    def _set_status(self, item, status):
        item.status = status
        if item.treeiter:
            GLib.idle_add(self.liststore.set, item.treeiter, 4, status)
        try:
            idx = self.queue.index(item)
        except ValueError:
            idx = None
        if status == "Downloading..." and idx is not None:
            GLib.idle_add(self._show_mini_popup, idx)
        if status in ("Completed", "Failed") and idx is not None and self._mini_idx == idx:
            GLib.idle_add(self._hide_mini_popup)
        self.update_dashboard_counts()
        if status in ("Completed", "Failed"):
            GLib.idle_add(self._remove_big_row, item)
        else:
            GLib.idle_add(self._add_or_update_big_row, item)
        GLib.idle_add(self._update_big_counts)
        try:
            if _HAS_NOTIFY and status in ("Completed", "Failed"):
                Notify.init("FastTube Downloader")
                n = Notify.Notification.new(status, item.title, None)
                n.show()
        except Exception:
            pass

    def _parse_item_progress(self, line, item):
        # Handle embedded custom markers that may be appended to other lines (e.g. yt-dlp output)
        for marker in ("PROGRESS:", "TITLE:", "META:", "FILE:"):
            if marker in line and not line.startswith(marker):
                seg = marker + line.split(marker, 1)[1]
                # Recursively parse just this marker segment
                self._parse_item_progress(seg, item)
                # Trim processed part and continue fallthrough for any remaining parsable content
                line = line.split(marker, 1)[0].strip()
        if not line:
            return
        # Surface explicit errors/warnings from helper script quickly in UI
        if line.startswith("ERROR:"):
            try:
                msg = line.split(":",1)[1].strip()
            except Exception:
                msg = "Error"
            self._set_status(item, f"Error: {msg}")
            # Also reflect in big popup immediately
            GLib.idle_add(self._add_or_update_big_row, item)
            return
        if line.startswith("WARN:") or line.startswith("WARNING:"):
            # Non-fatal; show as status line while continuing
            try:
                msg = line.split(":",1)[1].strip()
            except Exception:
                msg = "Warning"
            self._set_status(item, f"Warning: {msg}")
            GLib.idle_add(self._add_or_update_big_row, item)
        if line.startswith("PROGRESS:"):
            try:
                pct_str = line.split(":", 1)[1].strip().rstrip("% ")
                pct = float(pct_str)
                self._update_item_progress(item, int(pct))
                return
            except Exception:
                pass
        try:
            p = urllib.parse.urlparse(url)
            ext = os.path.splitext(p.path.lower())[-1]
            mapping = self.config.get('generic_extensions_map', {})
            for folder, exts in mapping.items():
                if ext in exts:
                    return folder
            return 'Other'
        except Exception:
            return 'Other'

    # ===================== Aria2 RPC Support =====================
    def _start_aria2_rpc_if_needed(self):
        if not self.config.get('aria2_rpc_enabled', False):
            return
        if getattr(self, '_aria2_rpc_started', False):
            return
        port = int(self.config.get('aria2_rpc_port', 6800))
    # Launch aria2c daemon
        try:
            cmd = ["aria2c", "--enable-rpc", f"--rpc-listen-port={port}", "--rpc-max-request-size=1024M", "--continue", "--max-concurrent-downloads=64", "-j", "64"]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._aria2_rpc_started = True
            # Give daemon a moment to come up before first call
            time.sleep(0.4)
        except Exception as e:
            print(f"[aria2rpc] failed to start daemon: {e}")

    def _aria2_rpc_call(self, method: str, params):
        """Perform a synchronous aria2 JSON-RPC call; returns result or raises."""
        port = int(self.config.get('aria2_rpc_port', 6800))
        payload = json.dumps({"jsonrpc": "2.0", "id": "ftdl", "method": method, "params": params}).encode('utf-8')
        import urllib.request
        req = urllib.request.Request(f"http://127.0.0.1:{port}/jsonrpc", data=payload, headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='ignore'))
            if 'error' in data:
                raise RuntimeError(data['error'])
            return data.get('result')

    def _aria2_add_uri(self, url: str, folder: str, out_name: str):
        opts = {"dir": folder, "out": out_name, "max-connection-per-server": str(self.config.get('aria_connections',16)), "split": str(self.config.get('aria_splits',32)), "min-split-size": "1M"}
        speed_limit = str(self.config.get('speed_limit_kbps') or '')
        if speed_limit.isdigit():
            opts['max-overall-download-limit'] = f"{speed_limit}K"
        result = self._aria2_rpc_call('aria2.addUri', [[url], opts])
        return result  # gid

    def _aria2_poll_item(self, item):
        # Poll until completion or failure
        try:
            while item.status in ("Queued", "Downloading...") and item.gid and self.config.get('aria2_rpc_enabled', False):
                try:
                    st = self._aria2_rpc_call('aria2.tellStatus', [item.gid, ["status", "completedLength", "totalLength", "downloadSpeed"]])
                except Exception:
                    st = None
                if not st:
                    break
                status = st.get('status','')
                comp = st.get('completedLength') or '0'
                total = st.get('totalLength') or '0'
                try:
                    comp_i = int(comp)
                    total_i = int(total) if total.isdigit() else 0
                    if total_i > 0:
                        pct = int((comp_i/total_i)*100)
                        self._update_item_progress(item, pct)
                        item.downloaded = self._human_bytes(self._bytes_to_str(comp_i))
                        item.total = self._human_bytes(self._bytes_to_str(total_i))
                except Exception:
                    pass
                spd = st.get('downloadSpeed')
                if spd and spd.isdigit():
                    item.speed = self._human_bytes(self._bytes_to_str(int(spd))) + '/s'
                self._update_progress_text(item)
                if status == 'complete':
                    self._set_status(item, 'Completed')
                    break
                if status == 'error':
                    self._set_status(item, 'Failed')
                    break
                if item.status == 'Paused':
                    break
                time.sleep(1.0)
        except Exception:
            pass

    def _bytes_to_str(self, val: int) -> str:
        try:
            units = ['B','KiB','MiB','GiB','TiB']
            v = float(val)
            u = 0
            while v >= 1024 and u < len(units)-1:
                v /= 1024.0; u += 1
            return f"{v:.1f}{units[u]}"
        except Exception:
            return ''
        if line.startswith("TITLE:"):
            try:
                title = line.split(":", 1)[1].strip()
                if title:
                    self._update_item_title(item, title)
                return
            except Exception:
                pass
    # aria2c style progress line, e.g.
        # "[#e8f9f5 2.1MiB/23MiB(9%) CN:4 DL:2.3MiB ETA:00:12]"
        # Extract percent, speed (DL:), ETA and downloaded/total
        try:
            if '%' in line and '(' in line and ')' in line and '[' in line:
                import re as _re
                pm = _re.search(r"\((\d+(?:\.\d+)?)%\)", line)
                if pm:
                    self._update_item_progress(item, int(float(pm.group(1))))
                # Parse DL speed
                sm = _re.search(r"DL:([^\] ]+)", line)
                if sm:
                    item.speed = sm.group(1)
                # Parse ETA
                em = _re.search(r"ETA:([0-9:]+)", line)
                if em:
                    item.eta = em.group(1)
                # Parse downloaded/total
                dtm = _re.search(r"\s([0-9.]+[A-Za-z]+)\/((?:N\/A)|[0-9.]+[A-Za-z]+)\(", line)
                if dtm:
                    item.downloaded = dtm.group(1)
                    item.total = dtm.group(2)
                # Update progress text to include speed/eta if available
                prog = f"{item.progress}%"
                extra = " ".join([s for s in [item.speed or '', item.eta or ''] if s])
                if extra and item.treeiter is not None:
                    GLib.idle_add(self.liststore.set, item.treeiter, 3, f"{prog} • {extra}")
        except Exception:
            pass
        if "[download]" in line and "%" in line:
            try:
                import re as _re
                m = _re.search(r"(\d+(?:\.\d+)?)%", line)
                if m:
                    self._update_item_progress(item, int(float(m.group(1))))
            except Exception:
                pass
        if "Destination:" in line:
            try:
                dest = line.split("Destination: ")[1].strip()
                title = dest.split(".")[-2].split(" - ")[-1] if " - " in dest else dest.split(".")[0].replace("NA - ", "")
                self._update_item_title(item, title)
                item.dest_path = dest
            except Exception:
                pass
        if line.startswith("META:"):
            try:
                parts = line.split(None, 1)[1] if ' ' in line else ''
                kv = {}
                for tok in parts.split():
                    if '=' in tok:
                        k,v = tok.split('=',1)
                        kv[k]=v
                item.speed = kv.get('speed','')
                item.eta = kv.get('eta','')
                item.total = kv.get('total','')
                item.downloaded = kv.get('downloaded','')
                self._update_progress_text(item)
            except Exception:
                pass
        if line.startswith("FILE:"):
            try:
                path = line.split(":",1)[1].strip()
                item.dest_path = path
            except Exception:
                pass

    def _update_item_progress(self, item, progress):
        item.progress = progress
        if item.treeiter is None:
            return
        dots = '.' * ((progress // 5) % 3 + 1)
        # Column 2 numeric value; column 3 composite text built in _update_progress_text
        GLib.idle_add(self.liststore.set, item.treeiter, 2, int(progress))
        self._update_progress_text(item)
        if self._mini_popup is not None and self._mini_idx is not None:
            def _upd_bar():
                try:
                    try:
                        idx = self.queue.index(item)
                    except ValueError:
                        return False
                    if self._mini_popup is None or self._mini_idx != idx:
                        return False
                    bar = self._mini_popup.get_child().get_children()[1]
                    bar.set_fraction(max(0.0, min(1.0, progress/100.0)))
                    bar.set_text(f"{int(progress)}%")
                except Exception:
                    pass
                return False
            GLib.idle_add(_upd_bar)

    def _update_item_title(self, item, title):
        item.title = title
        if item.treeiter is None:
            return
        GLib.idle_add(self.liststore.set, item.treeiter, 1, title)
        if self._mini_popup is not None and self._mini_idx is not None:
            def _upd_title():
                try:
                    try:
                        idx = self.queue.index(item)
                    except ValueError:
                        return False
                    if self._mini_popup is None or self._mini_idx != idx:
                        return False
                    header = self._mini_popup.get_child().get_children()[0]
                    header.set_text(title)
                except Exception:
                    pass
                return False
            GLib.idle_add(_upd_title)

    def parse_progress(self, line, idx):
        # Handle embedded custom markers that may be appended to other lines
        for marker in ("PROGRESS:", "TITLE:", "META:", "FILE:"):
            if marker in line and not line.startswith(marker):
                seg = marker + line.split(marker, 1)[1]
                self.parse_progress(seg, idx)
                line = line.split(marker, 1)[0].strip()
        if not line:
            return
        # Surface explicit errors/warnings
        if line.startswith("ERROR:"):
            try:
                msg = line.split(":",1)[1].strip()
            except Exception:
                msg = "Error"
            self.update_status(idx, f"Error: {msg}")
            return
        if line.startswith("WARN:") or line.startswith("WARNING:"):
            try:
                msg = line.split(":",1)[1].strip()
            except Exception:
                msg = "Warning"
            self.update_status(idx, f"Warning: {msg}")
        # Handle custom progress emitted by fast_ytdl.sh Python hook: "PROGRESS: 12.3%"
        if line.startswith("PROGRESS:"):
            try:
                pct_str = line.split(":", 1)[1].strip().rstrip("% ")
                pct = float(pct_str)
                self.update_progress(idx, int(pct))
                return
            except Exception:
                pass
        # Handle custom title line: "TITLE: Some Video Title"
        if line.startswith("TITLE:"):
            try:
                title = line.split(":", 1)[1].strip()
                if title:
                    self.update_title(idx, title)
                return
            except Exception:
                pass
    # aria2c style progress line: "[#... 2.1MiB/23MiB(9%) CN:4 DL:2.3MiB ETA:00:12]"
        try:
            if '%' in line and '(' in line and ')' in line and '[' in line:
                import re as _re
                pm = _re.search(r"\((\d+(?:\.\d+)?)%\)", line)
                if pm:
                    self.update_progress(idx, int(float(pm.group(1))))
                # Meta: speed and eta
                sm = _re.search(r"DL:([^\] ]+)", line)
                em = _re.search(r"ETA:([0-9:]+)", line)
                # downloaded/total
                dtm = _re.search(r"\s([0-9.]+[A-Za-z]+)\/((?:N\/A)|[0-9.]+[A-Za-z]+)\(", line)
                it = self.queue[idx]
                if sm:
                    it.speed = sm.group(1)
                if em:
                    it.eta = em.group(1)
                if dtm:
                    it.downloaded = dtm.group(1)
                    it.total = dtm.group(2)
                prog = f"{it.progress}%"
                extra = " ".join([s for s in [it.speed or '', it.eta or ''] if s])
                if extra and it.treeiter is not None:
                    GLib.idle_add(self.liststore.set, it.treeiter, 3, f"{prog} • {extra}")
        except Exception:
            pass
        # Fallback: parse yt-dlp standard "[download]  45.6% of ..." lines
        if "[download]" in line and "%" in line:
            try:
                import re as _re
                m = _re.search(r"(\d+(?:\.\d+)?)%", line)
                if m:
                    self.update_progress(idx, int(float(m.group(1))))
            except Exception:
                pass
        if "Destination:" in line:
            # Extract title from "Destination: NA - [Title].ext"
            try:
                dest = line.split("Destination: ")[1].strip()
                title = dest.split(".")[-2].split(" - ")[-1] if " - " in dest else dest.split(".")[0].replace("NA - ", "")
                self.update_title(idx, title)
                try:
                    self.queue[idx].dest_path = dest
                except Exception:
                    pass
            except:
                pass
        if line.startswith("META:"):
            try:
                parts = line.split(None, 1)[1] if ' ' in line else ''
                kv = {}
                for tok in parts.split():
                    if '=' in tok:
                        k,v = tok.split('=',1)
                        kv[k]=v
                item = self.queue[idx]
                item.speed = kv.get('speed','')
                item.eta = kv.get('eta','')
                item.total = kv.get('total','')
                item.downloaded = kv.get('downloaded','')
                self._update_progress_text(item)
            except Exception:
                pass
        if line.startswith("FILE:"):
            try:
                path = line.split(":",1)[1].strip()
                self.queue[idx].dest_path = path
            except Exception:
                pass

    def update_progress(self, idx, progress):
        self.queue[idx].progress = progress
        item = self.queue[idx]
        if item.treeiter is None:
            return
        dots = '.' * ((progress // 5) % 3 + 1)
        GLib.idle_add(self.liststore.set, item.treeiter, 2, int(progress))
        self._update_progress_text(item)
        # Update mini popup if showing this item
        if self._mini_idx == idx and self._mini_popup is not None:
            try:
                bar = self._mini_popup.get_child().get_children()[1]
                bar.set_fraction(max(0.0, min(1.0, progress/100.0)))
                bar.set_text(f"{int(progress)}%")
            except Exception:
                pass

    def _human_bytes(self, val):
        try:
            if not val: return ''
            # yt-dlp already gives e.g. 12.3MiB; keep as-is
            return val
        except Exception:
            return ''

    def _compose_progress_summary(self, item):
        """Return IDM-like status: '45% • 3.2MiB/12.4MiB • 2.1MiB/s • ETA 00:12'"""
        pct = f"{item.progress}%"
        size_part = ''
        try:
            if item.downloaded or item.total:
                size_part = f"{self._human_bytes(item.downloaded)}/{self._human_bytes(item.total)}".strip('/')
        except Exception:
            size_part = ''
        speed_part = item.speed or ''
        eta_part = item.eta or ''
        pieces = [pct]
        if size_part:
            pieces.append(size_part)
        if speed_part:
            pieces.append(speed_part)
        if eta_part:
            pieces.append(f"ETA {eta_part}")
        return ' • '.join(pieces)

    def _update_progress_text(self, item):
        try:
            text = self._compose_progress_summary(item)
            if item.treeiter is not None:
                GLib.idle_add(self.liststore.set, item.treeiter, 3, text)
            # Also mirror into mini popup if showing this item
            if self._mini_popup is not None and self._mini_idx is not None:
                try:
                    if self.queue[self._mini_idx] is item and self._mini_status_lbl is not None:
                        GLib.idle_add(self._mini_status_lbl.set_text, text)
                except Exception:
                    pass
        except Exception:
            pass

    def update_title(self, idx, title):
        self.queue[idx].title = title
        item = self.queue[idx]
        if item.treeiter is None:
            return
        GLib.idle_add(self.liststore.set, item.treeiter, 1, title)
        if self._mini_idx == idx and self._mini_popup is not None:
            try:
                header = self._mini_popup.get_child().get_children()[0]
                header.set_text(title)
            except Exception:
                pass

    def update_status(self, idx, status):
        self.queue[idx].status = status
        item = self.queue[idx]
        if item.treeiter is None:
            return
        GLib.idle_add(self.liststore.set, item.treeiter, 4, status)
        if status == "Downloading...":
            GLib.idle_add(self._show_mini_popup, idx)
        if status in ("Completed", "Failed") and self._mini_idx == idx:
            GLib.idle_add(self._hide_mini_popup)
        self.update_dashboard_counts()
        # Desktop notification
        try:
            if _HAS_NOTIFY and status in ("Completed", "Failed"):
                Notify.init("FastTube Downloader")
                n = Notify.Notification.new(f"{status}", self.queue[idx].title, None)
                n.show()
        except Exception:
            pass

    def _show_mini_popup(self, idx):
        try:
            item = self.queue[idx]
            if self._mini_popup is None:
                win = Gtk.Window(title="FastTube Downloading")
                win.set_keep_above(True)
                win.set_decorated(False)
                win.set_default_size(300, 80)
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                box.set_border_width(10)
                title_lbl = Gtk.Label(label=item.title)
                title_lbl.set_ellipsize(3)  # Pango.EllipsizeMode.END
                status_lbl = Gtk.Label(label=self._compose_progress_summary(item))
                status_lbl.set_halign(Gtk.Align.START)
                status_lbl.set_ellipsize(3)
                bar = Gtk.ProgressBar()
                if item.progress:
                    bar.set_fraction(item.progress/100.0)
                    bar.set_text(f"{int(item.progress)}%")
                    bar.set_show_text(True)
                box.pack_start(title_lbl, False, False, 0)
                box.pack_start(status_lbl, False, False, 0)
                box.pack_start(bar, True, True, 0)
                win.add(box)
                css = Gtk.CssProvider()
                css.load_from_data(b".mini-popup { background: #1e1e1e; color: #eee; border-radius: 8px; }")
                box.get_style_context().add_class("mini-popup")
                Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_USER)
                self._mini_popup = win
                self._mini_title_lbl = title_lbl
                self._mini_status_lbl = status_lbl
                self._mini_progress_bar = bar
            else:
                # Update existing
                if self._mini_title_lbl is not None:
                    self._mini_title_lbl.set_text(item.title)
                if self._mini_status_lbl is not None:
                    self._mini_status_lbl.set_text(self._compose_progress_summary(item))
            self._mini_idx = idx
            self._mini_popup.show_all()
            try:
                self._mini_popup.present()
                # Fade-in animation
                self._mini_popup.set_opacity(0.0)
                def _fade(step=0):
                    try:
                        if self._mini_popup is None:
                            return False
                        new_op = min(1.0, step/10.0)
                        self._mini_popup.set_opacity(new_op)
                        return False if new_op >= 1.0 else True
                    except Exception:
                        return False
                for i in range(1,11):
                    GLib.timeout_add(25*i, lambda s=i: _fade(s))
            except Exception:
                pass
        except Exception:
            pass
    def _pulse_progress_rows(self):
        # Placeholder for future row pulsing; can expand without affecting state
        return True

    def _hide_mini_popup(self):
        if self._mini_popup is not None:
            try:
                self._mini_popup.hide()
            except Exception:
                pass
            self._mini_idx = None
            # Keep the window for reuse but clear label refs to avoid stale pointers
            self._mini_title_lbl = None
            self._mini_status_lbl = None
            self._mini_progress_bar = None

    # ================= Big IDM-style downloads window =================
    def _ensure_big_popup(self):
        if not self.config.get("show_big_popup", True):
            return
        if getattr(self, '_big_popup', None):
            return
        win = Gtk.Window(title="FastTube Downloads")
        win.set_default_size(580, 360)
        win.set_keep_above(True)
        win.set_decorated(True)
        win.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        win.set_skip_taskbar_hint(True)
        win.set_skip_pager_hint(True)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_border_width(10)
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        controls.set_hexpand(True)
        controls.get_style_context().add_class("big-controls")
        self._big_header_label = Gtk.Label(label="")
        self._big_header_label.set_halign(Gtk.Align.START)
        pause_all_btn = Gtk.Button(label="Pause All")
        pause_all_btn.connect("clicked", self._pause_all)
        resume_all_btn = Gtk.Button(label="Start All")
        resume_all_btn.connect("clicked", self._resume_all)
        clear_btn = Gtk.Button(label="Clear Finished")
        clear_btn.connect("clicked", self._clear_finished_rows)
        controls.pack_start(self._big_header_label, True, True, 0)
        controls.pack_start(pause_all_btn, False, False, 0)
        controls.pack_start(resume_all_btn, False, False, 0)
        controls.pack_start(clear_btn, False, False, 0)
        vbox.pack_start(controls, False, False, 0)
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        listbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        sc.add(listbox)
        vbox.pack_start(sc, True, True, 0)
        win.add(vbox)
        css = Gtk.CssProvider()
        css.load_from_data(b".big-popup { background:#10151a; color:#e9eef5; } .rowbox{ background:#181d22; border-radius:8px; padding:10px;} .rowtitle{ font-weight:700; font-size:13px;} .rowstatus{ color:#a8b3be; font-size:11px; } .big-controls { background:#0e1318; padding:6px 8px; border-radius:6px; } .big-controls button { background:#1f2630; color:#d5dde6; border:1px solid #2d3641; border-radius:6px; padding:4px 10px; } .big-controls button:hover { background:#2a333f; }")
        vbox.get_style_context().add_class("big-popup")
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        self._big_popup = win
        self._big_list = listbox
        self._update_big_counts()

    def _add_or_update_big_row(self, item):
        self._ensure_big_popup()
        row = self._big_rows.get(item)
        if not row:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.get_style_context().add_class("rowbox")
            title = Gtk.Label(label=item.title or item.url)
            title.set_halign(Gtk.Align.START)
            title.get_style_context().add_class("rowtitle")
            status = Gtk.Label(label=self._compose_progress_summary(item))
            status.set_halign(Gtk.Align.START)
            status.get_style_context().add_class("rowstatus")
            hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            bar = Gtk.ProgressBar()
            bar.set_show_text(True)
            pb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            btn_pause = Gtk.Button(label="Pause")
            btn_resume = Gtk.Button(label="Start")
            btn_pause.connect("clicked", lambda _b, it=item: self._pause_item(it))
            btn_resume.connect("clicked", lambda _b, it=item: self._resume_item(it))
            pb.pack_start(btn_pause, False, False, 0)
            pb.pack_start(btn_resume, False, False, 0)
            hb.pack_start(bar, True, True, 0)
            hb.pack_end(pb, False, False, 0)
            box.pack_start(title, False, False, 0)
            box.pack_start(status, False, False, 0)
            box.pack_start(hb, False, False, 0)
            self._big_list.pack_start(box, False, False, 0)
            self._big_rows[item] = {
                'box': box,
                'title': title,
                'status': status,
                'bar': bar,
                'pause': btn_pause,
                'resume': btn_resume
            }
            self._big_popup.show_all()
        else:
            box = row['box']
            title = row['title']
            status = row['status']
            bar = row['bar']
            btn_pause = row['pause']
            btn_resume = row['resume']
        # Update
        row = self._big_rows[item]
        row['title'].set_text(item.title or item.url)
        row['status'].set_text(self._compose_progress_summary(item))
        row['bar'].set_fraction(max(0.0, min(1.0, (item.progress or 0)/100.0)))
        row['bar'].set_text(f"{int(item.progress or 0)}%")
        # Enable/disable controls based on state
        running = bool(item.process and item.process.poll() is None)
        row['pause'].set_sensitive(running)
        row['resume'].set_sensitive(not running)
        self._update_big_counts()

    def _remove_big_row(self, item):
        row = getattr(self, '_big_rows', {}).get(item)
        if not row:
            return
        try:
            self._big_list.remove(row['box'])
        except Exception:
            pass
        self._big_rows.pop(item, None)
        # Hide big popup if no more rows
        if self._big_rows == {} and getattr(self, '_big_popup', None):
            try:
                self._big_popup.hide()
            except Exception:
                pass
        self._update_big_counts()

    def _update_big_counts(self):
        if not getattr(self, '_big_header_label', None):
            return
        queued = sum(1 for it in self.queue if it.status == 'Queued')
        active = sum(1 for it in self.queue if it.status == 'Downloading...')
        paused = sum(1 for it in self.queue if it.status == 'Paused')
        text = f"Active: {active} | Paused: {paused} | Queue: {queued}"
        try:
            self._big_header_label.set_text(text)
        except Exception:
            pass

    def _pause_all(self, *_args):
        for item in list(self.queue):
            self._pause_item(item)
        self._update_big_counts()

    def _resume_all(self, *_args):
        for item in list(self.queue):
            if item.status == "Paused":
                self._resume_item(item)
        self._update_big_counts()

    def _clear_finished_rows(self, *_args):
        for item in list(getattr(self, '_big_rows', {}).keys()):
            if item.status in ("Completed", "Failed"):
                self._remove_big_row(item)
        self._update_big_counts()

    def _pause_item(self, item):
        if item.status in ("Completed", "Failed"):
            return
        if getattr(item, 'kind', 'media') == 'generic' and self.config.get('aria2_rpc_enabled', False) and item.gid:
            try:
                self._aria2_rpc_call('aria2.pause', [item.gid])
                self._set_status(item, "Paused")
                return
            except Exception:
                pass
        if item.process and item.process.poll() is None:
            try:
                item.process.terminate()
            except Exception:
                pass
        self._set_status(item, "Paused")

    def _resume_item(self, item):
        if item.status == "Paused":
            if getattr(item, 'kind', 'media') == 'generic' and self.config.get('aria2_rpc_enabled', False) and item.gid:
                try:
                    self._aria2_rpc_call('aria2.unpause', [item.gid])
                    self._set_status(item, "Downloading...")
                    return
                except Exception:
                    pass
            self._set_status(item, "Queued")
            if not self.is_downloading:
                self.is_downloading = True
                threading.Thread(target=self._spooler, daemon=True).start()

    def clear_queue(self, widget):
        self.liststore.clear()
        self.queue.clear()
        for item in list(getattr(self, '_big_rows', {}).keys()):
            self._remove_big_row(item)
        self._update_big_counts()
        self.update_dashboard_counts()

    def show_message(self, msg):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, msg)
        dialog.run()
        dialog.destroy()

    def quit_app(self, widget=None):
        if self.is_downloading:
            for item in self.queue:
                if item.process:
                    try:
                        item.process.terminate()
                    except Exception:
                        pass
        Gtk.main_quit()

    def _init_tray_icon(self):
        self.app_indicator = None
        self.status_icon = None
        
        icon_path = os.path.join(_BASE_DIR, 'icon128.png')
        if not os.path.exists(icon_path):
             # Fallback icon
             icon_path = "system-run" 

        menu = Gtk.Menu()
        item_show = Gtk.MenuItem(label="Show FastTube")
        item_show.connect("activate", lambda w: (self.show_all(), self.present()))
        menu.append(item_show)
        
        item_quit = Gtk.MenuItem(label="Quit")
        item_quit.connect("activate", self.quit_app)
        menu.append(item_quit)
        menu.show_all()

        if AppIndicator3:
            try:
                self.app_indicator = AppIndicator3.Indicator.new(
                    "fasttube-downloader",
                    os.path.abspath(icon_path) if os.path.exists(icon_path) else "fasttube-downloader",
                    AppIndicator3.IndicatorCategory.APPLICATION_STATUS
                )
                self.app_indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
                self.app_indicator.set_menu(menu)
                return
            except Exception as e:
                print(f"AppIndicator init failed: {e}")

        # Fallback to Gtk.StatusIcon
        try:
            self.status_icon = Gtk.StatusIcon()
            if os.path.exists(icon_path):
                self.status_icon.set_from_file(icon_path)
            else:
                self.status_icon.set_from_icon_name("fasttube-downloader")
            self.status_icon.set_tooltip_text("FastTube Downloader")
            self.status_icon.connect("popup-menu", lambda icon, button, time: menu.popup(None, None, None, icon, button, time))
            self.status_icon.connect("activate", lambda w: (self.show_all(), self.present()))
        except Exception:
            pass

    def on_delete_event(self, widget, event):
        if self.config.get("minimize_to_tray", True):
             self.hide()
             return True
        return False

    def _send_desktop_notification(self, title: str, body: str):
        """Send desktop notification using libnotify if available"""
        if not _HAS_NOTIFY:
            return
        try:
            Notify.init("FastTube Downloader")
            notification = Notify.Notification.new(title, body, "fasttube-downloader")
            notification.show()
        except Exception:
            pass

def run_app():
    # Optional flag to force a new instance (no single-instance handshake)
    force_new = any(arg in ('--new-instance','-N') for arg in sys.argv[1:])
    if not force_new:
        # Single-instance: if a control server is already running, ask it to show window and exit
        try:
            import socket as _s
            s = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(('127.0.0.1', 47653))
            try:
                s.sendall((json.dumps({"action":"show"})+'\n').encode('utf-8'))
            except Exception:
                pass
            s.close()
            return
        except Exception:
            pass
    win = MainWindow()
    # If config was missing we ran setup and exited early; only enter main loop if UI constructed
    if isinstance(win, MainWindow) and getattr(win, 'config', None):
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()

if __name__ == "__main__":
    run_app()