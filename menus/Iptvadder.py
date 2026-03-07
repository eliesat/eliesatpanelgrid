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
from Components.config import ConfigText, ConfigSelection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Plugins.Extensions.ElieSatPanelGrid.__init__ import Version


class Iptvadder(Screen, ConfigListScreen):

    width, height = getDesktop(0).size().width(), getDesktop(0).size().height()

    skin_file = (
        "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/skin/iptvadder_fhd.xml"
        if width >= 1920
        else "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/skin/iptvadder_hd.xml"
    )

    try:
        with open(skin_file, "r") as f:
            skin = f.read()
    except:
        skin = "<screen></screen>"

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle(_("Subscription Editor"))

        # Label selection (custom is default)
        self.label = ConfigSelection(
            default="custom",
            choices=[
                ("custom", "custom"),
                ("serverx1", "serverx1"),
                ("serverx2", "serverx2"),
                ("jepro1", "server jepro1"),
                ("jepro2", "server jepro2"),
                ("ultra", "server ultra"),
                ("strong8k1", "server strong 8k1"),
                ("strong8k2", "server strong 8k2"),
            ],
        )

        # Editable fields
        self.url = ConfigText(default="http://url.com")
        self.port = ConfigText(default="80")
        self.username = ConfigText(default="user")
        self.password = ConfigText(default="pass")

        # Add listener to auto-update URL when label changes
        self.label.addNotifier(self.label_changed, initial_call=False)

        self.clist = [
            getConfigListEntry("Label:", self.label),
            getConfigListEntry("URL:", self.url),
            getConfigListEntry("Port:", self.port),
            getConfigListEntry("Username:", self.username),
            getConfigListEntry("Password:", self.password),
        ]

        ConfigListScreen.__init__(self, self.clist, session=session)
        self["config"].l.setList(self.clist)

        # Side bars
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

        self["playlists"] = Label(self.get_playlists_dirs())
        self["panel_path"] = Label("")

        self.panel_dir = self.find_panel_dir()

        # Load saved subscription if exists
        if self.panel_dir:
            subfile = os.path.join(self.panel_dir, "isubscription.txt")
            if os.path.exists(subfile):
                with open(subfile, "r") as f:
                    lines = f.read().splitlines()

                if lines:
                    # First line is label
                    saved_label = lines[0].strip()
                    if saved_label in [choice[0] for choice in self.label.choices]:
                        self.label.setValue(saved_label)

                    # Second line is subscription
                    if len(lines) > 1:
                        line = lines[1].strip()
                        m = re.match(
                            r'(http[s]?://[^:/]+)(?::(\d+))?/get\.php\?username=([^&]+)&password=([^&]+)',
                            line,
                        )
                        if m:
                            self.url.setValue(m.group(1))
                            self.port.setValue(m.group(2) or "")
                            self.username.setValue(m.group(3))
                            self.password.setValue(m.group(4))

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

    # ------------------- Auto-fill URL based on label -------------------
    def label_changed(self, config_element):
        label = config_element.value
        mapping = {
            "custom": "http://url.com",
            "serverx1": "https://vipxtv.net",
            "serverx2": "http://sjl4p.otvipserv.com",
            "jepro1": "http://live.u8k.pro",
            "jepro2": "http://a345d.info",
            "ultra": "http://ultra.gotop.me",
            "strong8k1": "http://cf.business-cdn-8k.su",
            "strong8k2": "https://sean35934.cdnsilver.me",
        }
        if label in mapping and label != "custom":
            self.url.setValue(mapping[label])

    # ------------------- Refresh config list -------------------
    def refresh_config(self):
        self.clist = [
            getConfigListEntry("Label:", self.label),
            getConfigListEntry("URL:", self.url),
            getConfigListEntry("Port:", self.port),
            getConfigListEntry("Username:", self.username),
            getConfigListEntry("Password:", self.password),
        ]
        self["config"].l.setList(self.clist)
        self["config"].setCurrentIndex(0)

    # ------------------- Find panel directory -------------------
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

    # ------------------- Playlists -------------------
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

    # ------------------- Buttons -------------------
    def show_isubscription_path(self):
        if self.panel_dir:
            subfile = os.path.join(self.panel_dir, "isubscription.txt")
            if os.path.exists(subfile):
                with open(subfile, "r") as f:
                    content = f.read().strip()
                text = "isubscription.txt path:\n%s\nContent:\n%s" % (subfile, content or "<empty>")
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
            lines = f.read().splitlines()
        if len(lines) < 2:
            self["panel_path"].setText("No subscription to restore")
            return
        subscription_line = lines[1]

        def yes_restore():
            playlist_files = self.get_all_playlists_files()
            for file_path in playlist_files:
                with open(file_path, "w") as f:
                    f.write(subscription_line)
            self["panel_path"].setText("Playlists restored from backup")

        self.session.openWithCallback(
            lambda ret: yes_restore() if ret else None,
            MessageBox,
            "Do you want to restore?",
            MessageBox.TYPE_YESNO,
        )

    def send_backup(self):
        if not self.panel_dir:
            self["panel_path"].setText("No panel folder found")
            return

        if self.port.value.strip():
            subscription_line = "%s:%s/get.php?username=%s&password=%s&type=m3u_plus&output=ts" % (
                self.url.value,
                self.port.value,
                self.username.value,
                self.password.value,
            )
        else:
            subscription_line = "%s/get.php?username=%s&password=%s&type=m3u_plus&output=ts" % (
                self.url.value,
                self.username.value,
                self.password.value,
            )

        subfile = os.path.join(self.panel_dir, "isubscription.txt")
        with open(subfile, "w") as f:
            f.write("%s\n%s" % (self.label.value, subscription_line))

        playlist_files = self.get_all_playlists_files()
        for file_path in playlist_files:
            try:
                with open(file_path, "w") as f:
                    f.write(subscription_line)
            except:
                pass

        self["panel_path"].setText("Saved:\n%s" % subscription_line)

    def clear_playlists(self):
        playlist_files = self.get_all_playlists_files()
        for file_path in playlist_files:
            open(file_path, "w").close()

        if self.panel_dir:
            subfile = os.path.join(self.panel_dir, "isubscription.txt")
            open(subfile, "w").close()

        # Reset defaults
        self.label.setValue("custom")
        self.url.setValue("http://url.com")
        self.port.setValue("80")
        self.username.setValue("user")
        self.password.setValue("pass")

        self.refresh_config()
        self["panel_path"].setText("Playlists cleared and defaults restored")

        self.clear_timer = eTimer()
        self.clear_timer.timeout.get().append(self.clear_panel_path)
        self.clear_timer.start(5000, True)
