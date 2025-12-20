# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import sys
import os

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from enigma import eLabel, gFont, RT_HALIGN_LEFT, RT_HALIGN_CENTER
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from enigma import getDesktop
from Plugins.Extensions.ElieSatPanelGrid.__init__ import Version
from Plugins.Extensions.ElieSatPanelGrid.menus.Helpers import (
    get_local_ip, check_internet, get_image_name,
    get_python_version, get_storage_info, get_ram_info
)
from Plugins.Extensions.ElieSatPanelGrid.menus.Helpers import is_device_unlocked

# Dummy translation function
def _(text):
    return text

# Unified file opener for Python 2 and 3
def open_file(filename, mode='r'):
    """
    Opens a file with UTF-8 encoding if Python 3, otherwise default encoding.
    Ignores encoding errors to prevent crashes on malformed files.
    """
    if sys.version_info[0] >= 3:
        return open(filename, mode, encoding='utf-8', errors='ignore')
    return open(filename, mode)


class Piconstudio(Screen):
    width, height = getDesktop(0).size().width(), getDesktop(0).size().height()

    skin_file = (
        "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/skin/piconstudio_fhd.xml"
        if width >= 1920
        else "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/skin/piconstudio_hd.xml"
    )

    try:
        with open(skin_file, "r") as f:
            skin = f.read()
    except Exception as e:
        print("[ElieSatPanel] Failed to load skin:", e)

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle("Panel Manager")

        self.selected_plugins = []

        self.checked_icon = LoadPixmap(
            resolveFilename(SCOPE_PLUGINS, "Extensions/ElieSatPanelGrid/assets/icon/checked.png")
        )
        self.unchecked_icon = LoadPixmap(
            resolveFilename(SCOPE_PLUGINS, "Extensions/ElieSatPanelGrid/assets/icon/unchecked.png")
        )

        # ActionMap
        self["shortcuts"] = ActionMap(
            ["ShortcutActions", "WizardActions"],
            {
                "ok": self.toggleSelection,  # OK button toggles selection
                "cancel": self.exit,
                "back": self.exit,
                "red": self.exit,
                "green": self.installSelected,
                "yellow": lambda: None,  # Yellow button does nothing
            },
            -1
        )

        self["key_red"] = Label(_("Path"))
        self["key_green"] = Label(_("Install"))
        self["key_yellow"] = Label(_("Channels"))
        self["key_blue"] = Label(_("Frequencies"))

        # Menu list
        self.list = []
        self["menu"] = List(self.list)

        # Label for selected count (under the list)
        self["selection_count"] = Label(_("Selected: 0"))

        self.load_plugins_list()
        self.mList()

        # ---------------- UI Components ----------------
        self["image_name"] = Label(f"Image: {get_image_name()}")
        self["local_ip"] = Label(f"IP: {get_local_ip()}")
        self["StorageInfo"] = Label(get_storage_info())
        self["RAMInfo"] = Label(get_ram_info())
        self["python_ver"] = Label(f"Python: {get_python_version()}")
        self["net_status"] = Label(f"Net: {check_internet()}")
        self["left_bar"] = Label("\n".join(list("Version " + Version)))
        self["right_bar"] = Label("\n".join(list("By ElieSat")))

    def load_plugins_list(self):
        self.all_plugins = [
            _("All"),
            _("30.0W - Hispasat 30W 5/6"),
            _("14.0W - Express AM8"),
            _("7.0W - Nilesat 201/301 & Eutelsat 8 West B"),
            _("5.0W - Eutelsat 5 West B"),
            _("4.0W - AMOS 3 & Dror 1"),
            _("0.8W - Thor 5/6/7 & Intelsat 10 02"),
            _("1.9E - BulgariaSat 1"),
            _("9.0E - Eutelsat 9B"),
            _("13.0E - Hot Bird 13F/13G"),
            _("16.0E - Eutelsat 16A"),
            _("19.2E - Astra 1KR/1M/1N/1P"),
            _("23.5E - Astra 3B/3C"),
            _("26.0E - Badr 7/8 & Es'hail 2"),
            _("28.2E - Astra 2E/2F/2G"),
            _("36.0E - Eutelsat 36D / Express AMU1"),
            _("39.0E - Hellas Sat 3 / Eutelsat 39B"),
            _("42.0E - Turksat 3A/4A/5A/6B"),
            _("46.0E - Azerspace 1"),
            _("52.0E - TurkmenÄlem / MonacoSat"),
            _("52.5E - Al Yah 1"),
            _("53.0E - Express AM6"),
            _("62.0E - Intelsat 902"),
        ]

    def mList(self):
        self.list = []
        for plugin_name in self.all_plugins:
            icon = self.checked_icon if plugin_name in self.selected_plugins else self.unchecked_icon
            self.list.append((plugin_name, plugin_name, icon))

        self["menu"].setList(self.list)
        self.update_selection_count()

    def toggleSelection(self):
        current = self["menu"].getCurrent()
        if not current:
            return

        index = self["menu"].getIndex()
        plugin_name = current[0]

        if plugin_name in self.selected_plugins:
            self.selected_plugins.remove(plugin_name)
            new_icon = self.unchecked_icon
        else:
            self.selected_plugins.append(plugin_name)
            new_icon = self.checked_icon

        self.list[index] = (plugin_name, plugin_name, new_icon)
        self["menu"].updateList(self.list)
        self.update_selection_count()

    def update_selection_count(self):
        self["selection_count"].setText(_("Selected: %d") % len(self.selected_plugins))

    def installSelected(self):
        if not self.selected_plugins:
            self.showError(_("No plugins selected"))
            return

        self.install_scripts = []
        for plugin in self.selected_plugins:
            script = self.get_script(plugin)
            if not script:
                self.showError(_("Script not found for %s") % plugin)
                return
            self.install_scripts.append(script)

        self.session.openWithCallback(
            self.confirmInstallSelected,
            MessageBox,
            _("Install %d selected plugins?") % len(self.selected_plugins),
            MessageBox.TYPE_YESNO,
        )

    def confirmInstallSelected(self, answer):
        if not answer:
            return

        try:
            with open("/tmp/install_script.sh", "w") as f:
                f.write("#!/bin/sh\n")
                f.write("\n".join(self.install_scripts) + "\n")

            self.session.open(
                Console,
                title=_("Installing selected plugins"),
                cmdlist=[
                    "chmod +x /tmp/install_script.sh",
                    "/bin/sh /tmp/install_script.sh",
                ],
                closeOnSuccess=True,
            )

            self.selected_plugins = []
            self.mList()
        except Exception as e:
            self.showError(str(e))

    def keyOK(self):
        current = self["menu"].getCurrent()
        if current:
            self.installPlugin(current[0])

    def installPlugin(self, plugin_name):
        script = self.get_script(plugin_name)
        if not script:
            self.showError(_("Script not found"))
            return

        self.session.openWithCallback(
            lambda answer: self.executeInstall(answer, plugin_name),
            MessageBox,
            _("Install %s?") % plugin_name,
            MessageBox.TYPE_YESNO,
        )

    def executeInstall(self, answer, plugin_name):
        if not answer:
            return

        try:
            with open("/tmp/install_script.sh", "w") as f:
                f.write("#!/bin/sh\n" + self.get_script(plugin_name) + "\n")

            self.session.open(
                Console,
                title=_("Installing %s") % plugin_name,
                cmdlist=[
                    "chmod +x /tmp/install_script.sh",
                    "/bin/sh /tmp/install_script.sh",
                ],
                closeOnSuccess=True,
            )
        except Exception as e:
            self.showError(str(e))

    def get_script(self, plugin_name):
        scripts = {
    _("All"): "/usr/script/demo/all.sh",

    _("30.0W - Hispasat 30W 5/6"): "/usr/script/demo/30w_hispasat.sh",
    _("14.0W - Express AM8"): "/usr/script/demo/14w_express_am8.sh",
    _("7.0W - Nilesat 201/301 & Eutelsat 8 West B"): "/usr/script/demo/7w_nilesat.sh",
    _("5.0W - Eutelsat 5 West B"): "/usr/script/demo/5w_eutelsat.sh",
    _("4.0W - AMOS 3 & Dror 1"): "/usr/script/demo/4w_amos.sh",
    _("0.8W - Thor 5/6/7 & Intelsat 10 02"): "/usr/script/demo/0_8w_thor.sh",

    _("1.9E - BulgariaSat 1"): "/usr/script/demo/1_9e_bulgariasat.sh",
    _("9.0E - Eutelsat 9B"): "/usr/script/demo/9e_eutelsat.sh",
    _("13.0E - Hot Bird 13F/13G"): "/usr/script/demo/13e_hotbird.sh",
    _("16.0E - Eutelsat 16A"): "/usr/script/demo/16e_eutelsat.sh",
    _("19.2E - Astra 1KR/1M/1N/1P"): "/usr/script/demo/19_2e_astra1.sh",
    _("23.5E - Astra 3B/3C"): "/usr/script/demo/23_5e_astra3.sh",
    _("26.0E - Badr 7/8 & Es'hail 2"): "/usr/script/demo/26e_badr.sh",
    _("28.2E - Astra 2E/2F/2G"): "/usr/script/demo/28_2e_astra2.sh",
    _("36.0E - Eutelsat 36D / Express AMU1"): "/usr/script/demo/36e_eutelsat.sh",
    _("39.0E - Hellas Sat 3 / Eutelsat 39B"): "/usr/script/demo/39e_hellas.sh",
    _("42.0E - Turksat 3A/4A/5A/6B"): "/usr/script/demo/42e_turksat.sh",
    _("46.0E - Azerspace 1"): "/usr/script/demo/46e_azerspace.sh",
    _("52.0E - TurkmenÄlem / MonacoSat"): "/usr/script/demo/52e_turkmenalem.sh",
    _("52.5E - Al Yah 1"): "/usr/script/demo/52_5e_alyah.sh",
    _("53.0E - Express AM6"): "/usr/script/demo/53e_express_am6.sh",
    _("62.0E - Intelsat 902"): "/usr/script/demo/62e_intelsat.sh",
}

        return scripts.get(plugin_name)

    def showError(self, message):
        self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)

    def exit(self):
        self.close()

