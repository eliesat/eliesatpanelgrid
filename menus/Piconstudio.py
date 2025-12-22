# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import os
import sys

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Console import Console

from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Label import Label

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from enigma import getDesktop

from Plugins.Extensions.ElieSatPanelGrid.__init__ import Version
from Plugins.Extensions.ElieSatPanelGrid.menus.Helpers import is_device_unlocked
from Plugins.Extensions.ElieSatPanelGrid.menus.Helpers import (
    get_local_ip, check_internet, get_image_name,
    get_python_version, get_storage_info, get_ram_info
)
# Dummy translation
def _(txt):
    return txt

# Python 2 / 3 safe file open
def open_file(path, mode="r"):
    if sys.version_info[0] >= 3:
        return open(path, mode, encoding="utf-8", errors="ignore")
    return open(path, mode)

class Piconstudio(Screen):

    width = getDesktop(0).size().width()
    skin = open(
        "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/skin/%s"
        % ("piconstudio_fhd.xml" if width >= 1920 else "piconstudio_hd.xml")
    ).read()

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle(_("PiconStudio"))

        # ---- ERROR HANDLING ----
        self._pending_error = None
        self.onShown.append(self._showPendingError)

        self.selected_plugins = []

        # Load icons
        self.checked_icon = LoadPixmap(
            resolveFilename(
                SCOPE_PLUGINS,
                "Extensions/ElieSatPanelGrid/assets/icon/checked.png"
            )
        )
        self.unchecked_icon = LoadPixmap(
            resolveFilename(
                SCOPE_PLUGINS,
                "Extensions/ElieSatPanelGrid/assets/icon/unchecked.png"
            )
        )

        # UI Elements
        self["menu"] = List([])
        self["selection_count"] = Label(_("Selected: 0"))

        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Install"))
        self["key_yellow"] = Label(_("—"))
        self["key_blue"] = Label(_("—"))

        # System info
        self["image_name"] = Label("Image: " + get_image_name())
        self["local_ip"] = Label("IP: " + get_local_ip())
        self["StorageInfo"] = Label(get_storage_info())
        self["RAMInfo"] = Label(get_ram_info())
        self["python_ver"] = Label("Python: " + get_python_version())
        self["net_status"] = Label("Net: " + check_internet())

        # Vertical bars
        self["left_bar"] = Label("\n".join(list("Version " + Version)))
        self["right_bar"] = Label("\n".join(list("By ElieSat")))

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions"],
            {
                "ok": self.toggleSelection,
                "cancel": self.close,
                "red": self.close,
                "green": self.installSelected,
            },
            -1
        )

        self.list = []
        self.buildList()

    # ---------------- FILE PATH ----------------
    def status_path(self):
        # Path to your picons text file
        path = "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/data/picons"
        if os.path.exists(path):
            return path
        return None

    # ---------------- BUILD MENU ----------------
    def buildList(self):
        self.list = []
        self.selected_plugins = []

        path = self.status_path()
        if not path or not os.path.isfile(path):
            self.showError(_("Picons file not found"))
            self["menu"].setList([])
            self.updateCounter()
            return

        name = None
        desc = ""

        for line in open_file(path):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.lower().startswith("package:"):
                name = line.split(":", 1)[1].strip()
            elif line.lower().startswith("version:"):
                desc = line.split(":", 1)[1].strip()
            elif line.lower().startswith("status:") or "=" in line:
                if name:
                    # Tuple format matching skin: (title, description, icon)
                    self.list.append((name, desc, self.unchecked_icon))
                    name = None
                    desc = ""

        # Catch last block in case file does not end with status or '='
        if name:
            self.list.append((name, desc, self.unchecked_icon))

        if not self.list:
            self.showError(_("No packages found"))
            self["menu"].setList([])
            self.updateCounter()
            return

        # Sort alphabetically by package name
        self.list.sort(key=lambda x: x[0].lower())
        self["menu"].setList(self.list)
        self.updateCounter()

    # ---------------- TOGGLE SELECTION ----------------
    def toggleSelection(self):
        cur = self["menu"].getCurrent()
        if not cur:
            return

        index = self["menu"].getIndex()
        name, desc, _icon = cur

        if name in self.selected_plugins:
            self.selected_plugins.remove(name)
            icon = self.unchecked_icon
        else:
            self.selected_plugins.append(name)
            icon = self.checked_icon

        self.list[index] = (name, desc, icon)
        self["menu"].updateList(self.list)
        self.updateCounter()

    # ---------------- COUNTER ----------------
    def updateCounter(self):
        self["selection_count"].setText(
            _("Selected: %d") % len(self.selected_plugins))

    # ---------------- INSTALL ----------------
    def installSelected(self):
        if not self.selected_plugins:
            self.showError(_("Nothing selected"))
            return

        script = "/tmp/install_selected.sh"

        try:
            with open(script, "w") as f:
                f.write("#!/bin/sh\n")
                for pkg in self.selected_plugins:
                    # Find URL in picons.txt
                    url = None
                    for line in open_file(self.status_path()):
                        if line.startswith(pkg + "="):
                            url = line.split("'")[1]
                            break
                    if url:
                        f.write("wget --no-check-certificate %s -qO - | /bin/sh\n" % url)

            self.session.open(
                Console,
                _("Installing"),
                [
                    "chmod +x %s" % script,
                    "/bin/sh %s" % script
                ]
            )

            self.selected_plugins = []
            self.buildList()

        except Exception as e:
            self.showError(str(e))

    # ---------------- ERROR HANDLING ----------------
    def showError(self, txt):
        self._pending_error = txt

    def _showPendingError(self):
        if self._pending_error:
            self.session.open(
                MessageBox,
                self._pending_error,
                MessageBox.TYPE_ERROR
            )
            self._pending_error = None

