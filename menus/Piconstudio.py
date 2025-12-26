# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import os
import sys
import time
import re

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Label import Label
from Components.ProgressBar import ProgressBar

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from enigma import getDesktop, eConsoleAppContainer, eTimer

from Plugins.Extensions.ElieSatPanelGrid.__init__ import Version
from Plugins.Extensions.ElieSatPanelGrid.menus.Helpers import (
    get_local_ip, check_internet, get_image_name,
    get_python_version, get_storage_info, get_ram_info
)


def _(txt):
    return txt


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

        # ================= UI =================
        self["menu"] = List([])
        self["selection_count"] = Label(_("Selected: 0"))

        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Install"))

        self["image_name"] = Label("Image: " + get_image_name())
        self["local_ip"] = Label("IP: " + get_local_ip())
        self["StorageInfo"] = Label(get_storage_info())
        self["RAMInfo"] = Label(get_ram_info())
        self["python_ver"] = Label("Python: " + get_python_version())
        self["net_status"] = Label("Net: " + check_internet())

        self["left_bar"] = Label("\n".join(list("Version " + Version)))
        self["right_bar"] = Label("\n".join(list("By ElieSat")))

        # ---- INSTALL UI ----
        self["item_name"] = Label("")        # Line 1: status
        self["download_info"] = Label("")    # Line 3: script output
        self["download_info"].show()

        self["progress"] = ProgressBar()     # Line 2: progress bar
        self["progress"].setRange((0, 100))
        self["progress"].setValue(0)
        self["progress"].hide()

        # ================= ACTIONS =================
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

        # ================= DATA =================
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

        self.list = []
        self.selected_plugins = []
        self.download_queue = []

        self.container = None
        self.current_pkg = None

        # ===== PROGRESS =====
        self.total_packages = 0
        self.current_index = 0
        self.install_fake_progress = 0
        self.progressTimer = eTimer()
        self.progressTimer.callback.append(self._onInstallProgress)
        self.pauseTimer = None

        # ===== RESULT TRACKING =====
        self.total_selected = 0
        self.success_installs = 0

        self.buildList()

    # ================= FILE =================
    def status_path(self):
        path = "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/data/picons"
        return path if os.path.isfile(path) else None

    # ================= LIST =================
    def buildList(self):
        self.list = []
        self.selected_plugins = []

        path = self.status_path()
        if not path:
            self.showError(_("Picons file not found"))
            return

        name = desc = ""

        for line in open_file(path):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.lower().startswith("package:"):
                name = line.split(":", 1)[1].strip()
            elif line.lower().startswith("version:"):
                desc = line.split(":", 1)[1].strip()
            elif "=" in line and name:
                self.list.append((name, desc, self.unchecked_icon))
                name = desc = ""

        self.list.sort(key=lambda x: x[0].lower())
        self["menu"].setList(self.list)
        self.updateCounter()

    # ================= SELECT =================
    def toggleSelection(self):
        cur = self["menu"].getCurrent()
        if not cur:
            return

        index = self["menu"].getIndex()
        name, desc, icon = cur

        if name in self.selected_plugins:
            self.selected_plugins.remove(name)
            icon = self.unchecked_icon
        else:
            self.selected_plugins.append(name)
            icon = self.checked_icon

        self.list[index] = (name, desc, icon)
        self["menu"].updateList(self.list)
        self.updateCounter()

    def updateCounter(self):
        self["selection_count"].setText(
            _("Selected: %d") % len(self.selected_plugins)
        )

    # ================= INSTALL =================
    def installSelected(self):
        if not self.selected_plugins:
            self.showError(_("Nothing selected"))
            return

        self.download_queue = list(self.selected_plugins)
        self.total_packages = len(self.download_queue)
        self.total_selected = self.total_packages
        self.success_installs = 0
        self.current_index = 0
        self.selected_plugins = []

        self.startNext()

    def startNext(self):
        if self.current_index >= self.total_packages:
            failed = self.total_selected - self.success_installs
            self["item_name"].setText(
                _("Done: %d/%d installed, %d failed")
                % (self.success_installs, self.total_selected, failed)
            )
            self["download_info"].setText("")
            self["progress"].setValue(100)
            self["progress"].show()
            self.buildList()
            return

        self.current_pkg = self.download_queue[self.current_index]
        self.current_index += 1

        url = None
        for line in open_file(self.status_path()):
            if line.startswith(self.current_pkg + "="):
                url = line.split("'")[1]
                break

        if not url:
            self.startNext()
            return

        self.download_url = url
        self.download_file = "/tmp/%s.sh" % self.current_pkg
        self.install_fake_progress = 0

        self["item_name"].setText(_("Preparing %s ...") % self.current_pkg)
        self["download_info"].setText("")
        self["progress"].setValue(int(((self.current_index - 1) / self.total_packages) * 100))
        self["progress"].show()

        self._downloadScript()

    # ================= DOWNLOAD =================
    def _downloadScript(self):
        cmd = "wget --progress=dot:giga -O %s --no-check-certificate %s" % (
            self.download_file, self.download_url
        )
        self.container = eConsoleAppContainer()
        self.container.dataAvail.append(self._onDownloadData)
        self.container.appClosed.append(self._onDownloadFinished)
        self.container.execute(cmd)

    def _onDownloadData(self, data):
        try:
            text = data.decode("utf-8", "ignore").strip().replace("\n", " ")
            m = re.findall(r'(\d+)%', text)
            if m:
                percent = int(m[-1])
                overall = int(
                    ((self.current_index - 1) / self.total_packages +
                     (percent / 100.0) * (0.5 / self.total_packages)) * 100
                )
                self["progress"].setValue(overall)
                self["item_name"].setText(
                    _("Downloading %s ... %d%%") % (self.current_pkg, percent)
                )
                self["download_info"].setText(text[-50:])  # last 50 chars
        except:
            pass

    def _onDownloadFinished(self, ret):
        self["item_name"].setText(
            _("Downloading %s ... 100%%") % self.current_pkg
        )
        self["download_info"].setText("Download finished")
        self.pauseTimer = eTimer()
        self.pauseTimer.callback.append(self._startInstall)
        self.pauseTimer.start(500, True)

    # ================= INSTALL =================
    def _startInstall(self):
        os.system("chmod 755 %s" % self.download_file)
        self.install_fake_progress = 0
        self["item_name"].setText(
            _("Installing %s ... 0%%") % self.current_pkg
        )
        self["download_info"].setText("")
        self.progressTimer.start(1000, False)

        self.container = eConsoleAppContainer()
        self.container.dataAvail.append(self._onInstallData)
        self.container.appClosed.append(self._onScriptFinished)
        self.container.execute("sh %s" % self.download_file)

    # Capture real-time script output during installation
    def _onInstallData(self, data):
        try:
            text = data.decode("utf-8", "ignore").strip().replace("\n", " ")
            self["download_info"].setText(text[-50:])  # last 50 chars
        except:
            pass

    def _onInstallProgress(self):
        if self.install_fake_progress < 90:
            self.install_fake_progress += 2
        elif self.install_fake_progress < 98:
            self.install_fake_progress += 0.5

        overall = int(
            ((self.current_index - 1) / self.total_packages +
             (0.5 + (self.install_fake_progress / 100.0) * 0.5) / self.total_packages) * 100
        )

        self["progress"].setValue(overall)
        self["item_name"].setText(
            _("Installing %s ... %d%%") % (self.current_pkg, int(self.install_fake_progress))
        )

    def _onScriptFinished(self, ret):
        if self.progressTimer.isActive():
            self.progressTimer.stop()

        if ret == 0:
            self.success_installs += 1

        # append final message to download_info
        self["download_info"].setText("Script finished")

        self.pauseTimer = eTimer()
        self.pauseTimer.callback.append(self.startNext)
        self.pauseTimer.start(700, True)

    # ================= ERROR =================
    def showError(self, txt):
        self.session.open(MessageBox, txt, MessageBox.TYPE_ERROR)

