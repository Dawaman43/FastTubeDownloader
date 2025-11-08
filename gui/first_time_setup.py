import os
import json
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

CONFIG_DIR = os.path.expanduser("~/.config/FastTubeDownloader")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
NATIVE_HOST_DIR = os.path.expanduser("~/.config/google-chrome/NativeMessagingHosts")
NATIVE_HOST_FILE = os.path.join(NATIVE_HOST_DIR, "com.fasttube.downloader.json")
SCRIPT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_PATH = os.path.join(SCRIPT_PATH, "native_host", "bridge.py")
EXTENSION_ID = "gifdkhjpnkiaekcagnehmolkpndfohke"

class FirstTimeSetup(Gtk.Window):
    def __init__(self):
        super().__init__(title="FastTube Downloader Setup")
        self.set_border_width(10)
        self.set_default_size(400, 200)

        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        self.add(grid)

        self.folder_entry = Gtk.Entry()
        self.folder_entry.set_placeholder_text("~/Downloads")
        self.folder_entry.set_text("~/Downloads")
        browse_btn = Gtk.Button(label="Browse")
        browse_btn.connect("clicked", self.on_browse)
        grid.attach(Gtk.Label(label="Folder:"), 0, 0, 1, 1)
        grid.attach(self.folder_entry, 1, 0, 1, 1)
        grid.attach(browse_btn, 2, 0, 1, 1)

        self.format_combo = Gtk.ComboBoxText()
        self.format_combo.append_text("Best Video + Audio")
        self.format_combo.append_text("Audio Only")
        self.format_combo.append_text("Best (default)")
        self.format_combo.set_active(2)
        grid.attach(Gtk.Label(label="Format:"), 0, 1, 1, 1)
        grid.attach(self.format_combo, 1, 1, 2, 1)

        self.quality_entry = Gtk.Entry()
        self.quality_entry.set_placeholder_text("Optional resolution e.g., 1080")
        grid.attach(Gtk.Label(label="Resolution:"), 0, 2, 1, 1)
        grid.attach(self.quality_entry, 1, 2, 2, 1)

        self.subs_check = Gtk.CheckButton(label="Download subtitles (SRT) if available")
        grid.attach(self.subs_check, 0, 3, 3, 1)

        save_btn = Gtk.Button(label="Save & Configure")
        save_btn.connect("clicked", self.on_save)
        grid.attach(save_btn, 0, 4, 3, 1)

    def on_browse(self, widget):
        dialog = Gtk.FileChooserDialog(title="Select Folder", parent=self,
                                       action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           "Select", Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            self.folder_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def on_save(self, widget):
        folder = os.path.expanduser(self.folder_entry.get_text())
        fmt = self.format_combo.get_active_text()
        quality = self.quality_entry.get_text()
        subs = self.subs_check.get_active()

        if not folder:
            self.show_message("Please select a download folder!")
            return

        os.makedirs(CONFIG_DIR, exist_ok=True)
        config_data = {
            "download_folder": folder,
            "default_format": fmt,
            "preferred_quality": quality,
            "subs": subs
        }

        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)

        # Create Native Messaging host (dev path)
        os.makedirs(NATIVE_HOST_DIR, exist_ok=True)
        host_data = {
            "name": "com.fasttube.downloader",
            "description": "Native host for FastTube Downloader",
            "path": APP_PATH,
            "type": "stdio",
            "allowed_origins": [f"chrome-extension://{EXTENSION_ID}/"]
        }
        with open(NATIVE_HOST_FILE, "w") as f:
            json.dump(host_data, f, indent=4)

        os.chmod(APP_PATH, 0o755)
        self.show_message("Setup complete! Relaunch the app.")
        Gtk.main_quit()

    def show_message(self, msg):
        dialog = Gtk.MessageDialog(parent=self, flags=0,
                                   message_type=Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=msg)
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    if not os.path.exists(CONFIG_FILE):
        win = FirstTimeSetup()
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()
    else:
        print("Config exists, skipping setup.")