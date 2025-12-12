# -*- coding: utf-8 -*-
import os
import re
from enigma import eTimer
from enigma import getDesktop
from Plugins.Extensions.ElieSatPanelGrid.menus.Helpers import (
    get_local_ip,
    check_internet,
    get_image_name,
    get_python_version,
    get_storage_info,
    get_ram_info,
)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import ConfigText, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Plugins.Extensions.ElieSatPanelGrid.__init__ import Version


class Iptvadder(Screen, ConfigListScreen):
    # ---------------- Load correct skin ----------------
    width, height = getDesktop(0).size().width(), getDesktop(0).size().height()
    skin_file = (
        "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/skin/iptvadder_fhd.xml"
        if width >= 1920
        else "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/skin/iptvadder_hd.xml"
    )
    try:
        with open(skin_file, "r") as f:
            skin = f.read()
    except Exception as e:
        print(f"[ElieSatPanel] Failed to load skin: {e}")
        skin = "<screen></screen>"

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle(_("Subscription Editor"))

        # Editable fields
        self.url = ConfigText(default="http://jep2024.online")
        self.port = ConfigText(default="2083")
        self.username = ConfigText(default="user")
        self.password = ConfigText(default="pass")

        clist = [
            getConfigListEntry("URL:", self.url),
            getConfigListEntry("Port:", self.port),
            getConfigListEntry("Username:", self.username),
            getConfigListEntry("Password:", self.password),
        ]
        ConfigListScreen.__init__(self, clist, session=session)
        self["config"].l.setList(clist)

        # Side bar
        self["left_bar"] = Label("\n".join(list("Version " + Version)))
        self["right_bar"] = Label("\n".join(list("By ElieSat")))

        # System info
        self["image_name"] = Label("Image: " + get_image_name())
        self["local_ip"] = Label("IP: " + get_local_ip())
        self["StorageInfo"] = Label(get_storage_info())
        self["RAMInfo"] = Label(get_ram_info())
        self["python_ver"] = Label("Python: " + get_python_version())
        self["net_status"] = Label("Net: " + check_internet())

        # Buttons
        self["red"] = Label(_("Check Path"))
        self["green"] = Label(_("Restore"))
        self["yellow"] = Label(_("Send and Backup"))
        self["blue"] = Label(_("Clear Playlists"))

        # Playlists and Red button label
        self["playlists"] = Label(self.get_playlists_dirs())
        self["panel_path"] = Label("")

        # Prepare panel_dir & isubscription.txt
        self.panel_dir = self.find_panel_dir()

        # ---------------- Load previous values if file exists ----------------
        if self.panel_dir:
            subfile = os.path.join(self.panel_dir, "isubscription.txt")
            if os.path.exists(subfile):
                with open(subfile, "r") as f:
                    line = f.read().strip()
                if line:  # Only overwrite defaults if file has content
                    m = re.match(
                        r'(http[s]?://[^:/]+)(?::(\d+))?/get\.php\?username=([^&]+)&password=([^&]+)',
                        line,
                    )
                    if m:
                        self.url.setValue(m.group(1))
                        self.port.setValue(m.group(2) or "")  # <-- keep empty if missing
                        self.username.setValue(m.group(3))
                        self.password.setValue(m.group(4))

        # Actions
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions"],
            {
                "red": self.show_isubscription_path,
                "green": self.restore_reader,
                "yellow": self.send_backup,
                "blue": self.clear_playlists,
                "cancel": self.close,
            },
            -1,
        )

    # ---------------- Helpers ----------------
    def find_panel_dir(self):
        search_roots = ["/media/hdd", "/media/mmc"]
        usb_dirs = [os.path.join("/media", d) for d in os.listdir("/media") if d.startswith("usb")]
        search_roots.extend(usb_dirs)

        for root in search_roots:
            path = os.path.join(root, "ElieSatPanel", "panel_dir.cfg")
            if os.path.exists(path):
                folder = os.path.dirname(path)
                subfile = os.path.join(folder, "isubscription.txt")
                if not os.path.exists(subfile):
                    open(subfile, "w").close()
                return folder
        return None

    def get_playlists_dirs(self):
        dirs = []
        for root, _, files in os.walk("/etc/enigma2"):
            if "playlists.txt" in files:
                dirs.append(root)
        if not dirs:
            return "Playlists dir:\n<not found>"
        return "Playlists dirs:\n" + "\n".join(dirs[:10])

    def get_all_playlists_files(self):
        files = []
        for root, _, fs in os.walk("/etc/enigma2"):
            if "playlists.txt" in fs:
                files.append(os.path.join(root, "playlists.txt"))
        return files

    # ---------------- Buttons ----------------
    def show_isubscription_path(self):
        if self.panel_dir:
            subfile = os.path.join(self.panel_dir, "isubscription.txt")
            if os.path.exists(subfile):
                with open(subfile, "r") as f:
                    content = f.read().strip()
                text = f"isubscription.txt path:\n{subfile}\nContent:\n{content or '<empty>'}"
            else:
                text = "isubscription.txt not found"
        else:
            text = "panel_dir.cfg not found"
        self["panel_path"].setText(text)

        self.clear_timer = eTimer()
        self.clear_timer.timeout.get().append(self.clear_panel_path)
        self.clear_timer.start(5000, True)

    def clear_panel_path(self):
        self["panel_path"].setText("")

    def restore_reader(self):
        if not self.panel_dir:
            self["panel_path"].setText("No panel folder found")
            return
        subfile = os.path.join(self.panel_dir, "isubscription.txt")
        if not os.path.exists(subfile):
            self["panel_path"].setText("isubscription.txt not found")
            return
        with open(subfile, "r") as f:
            content = f.read().strip()
        message = f"Backup content:\n{content}\n\nDo you want to restore?"
        self["panel_path"].setText(message)

        def yes_restore():
            playlist_files = self.get_all_playlists_files()
            for file_path in playlist_files:
                with open(file_path, "w") as f:
                    f.write(content)
            self["panel_path"].setText("Playlists restored from backup")
            self.clear_timer = eTimer()
            self.clear_timer.timeout.get().append(self.clear_panel_path)
            self.clear_timer.start(5000, True)

        self.session.openWithCallback(
            lambda ret: yes_restore() if ret else self.clear_panel_path(),
            MessageBox,
            "Do you want to restore?",
            MessageBox.TYPE_YESNO,
        )

    def send_backup(self):
        """Yellow: Save current config to file + playlists"""
        if not self.panel_dir:
            self["panel_path"].setText("No panel folder found")
            return

        # Build URL properly, skip ':' if port is empty
        if self.port.value.strip():
            subscription_line = f"{self.url.value}:{self.port.value}/get.php?username={self.username.value}&password={self.password.value}&type=m3u_plus&output=ts"
        else:
            subscription_line = f"{self.url.value}/get.php?username={self.username.value}&password={self.password.value}&type=m3u_plus&output=ts"

        # Write backup file
        subfile = os.path.join(self.panel_dir, "isubscription.txt")
        with open(subfile, "w") as f:
            f.write(subscription_line)

        # Write playlists
        playlist_files = self.get_all_playlists_files()
        errors = []
        for file_path in playlist_files:
            try:
                with open(file_path, "w") as f:
                    f.write(subscription_line)
            except Exception as e:
                errors.append(f"{file_path}: {e}")

        if errors:
            self["panel_path"].setText("Some errors occurred:\n" + "\n".join(errors))
        else:
            self["panel_path"].setText(f"Saved:\n{subscription_line}")

        self.clear_timer = eTimer()
        self.clear_timer.timeout.get().append(self.clear_panel_path)
        self.clear_timer.start(5000, True)

    def clear_playlists(self):
        playlist_files = self.get_all_playlists_files()
        for file_path in playlist_files:
            open(file_path, "w").close()
        if self.panel_dir:
            subfile = os.path.join(self.panel_dir, "isubscription.txt")
            open(subfile, "w").close()
        self["panel_path"].setText("Playlists and backup cleared")
        self.clear_timer = eTimer()
        self.clear_timer.timeout.get().append(self.clear_panel_path)
        self.clear_timer.start(5000, True)

    def show_credentials(self):
        self.session.open(
            MessageBox,
            f"Username: {self.username.value}\nPassword: {self.password.value}",
            MessageBox.TYPE_INFO,
            timeout=5,
        )

