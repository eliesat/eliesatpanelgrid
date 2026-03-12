# -*- coding: utf-8 -*-
import os
from os import chmod, system as os_system
from os.path import exists, join

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from enigma import eConsoleAppContainer, getDesktop

from Plugins.Extensions.ElieSatPanelGrid.menus.Helpers import (
    get_local_ip,
    check_internet,
    get_image_name,
    get_python_version,
    get_storage_info,
    get_ram_info,
)
from Plugins.Extensions.ElieSatPanelGrid.__init__ import Version
from Plugins.Extensions.ElieSatPanelGrid.menus.Console import Console

scriptpath = "/usr/script/"
if not os.path.exists(scriptpath):
    os.makedirs(scriptpath, exist_ok=True)

class Scripts(Screen):
    def __init__(self, session):
        width, height = getDesktop(0).size().width(), getDesktop(0).size().height()
        skin_file = "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/skin/scripts_fhd.xml" \
            if width >= 1920 else "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/skin/scripts_hd.xml"
        with open(skin_file, "r") as f:
            self.skin = f.read()

        Screen.__init__(self, session)
        self.session = session
        self.items_per_page = 10
        self.current_page = 1
        self.total_pages = 1
        self.setTitle(_("Scripts Manager"))

        # Vertical bars
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
        self["red"] = Label(_("Remove List"))
        self["green"] = Label(_("Update List"))
        self["yellow"] = Label(_("Background run"))
        self["blue"] = Label(_("Restart Enigma2"))
        self["script_name"] = Label("")
        self["page_info"] = Label("Page 1/1")

        # Menu list
        self["list"] = MenuList([])
        self["list"].onSelectionChanged.append(self.updateSelection)

        # Actions
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions"],
            {
                "ok": self.run,
                "green": self.update,
                "yellow": self.bgrun,
                "red": self.remove,
                "blue": self.restart,
                "up": self.moveUp,
                "down": self.moveDown,
                "left": self.pageLeft,
                "right": self.pageRight,
                "cancel": self.close,
            },
            -1,
        )

        self.loadScripts()

    # --------------------------------------------------
    # Load scripts
    # --------------------------------------------------
    def loadScripts(self):
        self.scripts = []
        self.display_list = []

        if os.path.exists(scriptpath):
            self.scripts = [x for x in os.listdir(scriptpath) if x.endswith(".sh") or x.endswith(".py")]

        self.scripts.sort()

        for script in self.scripts:
            self.display_list.append("• %s" % script)

        self["list"].setList(self.display_list)
        self.updateSelection()

    # --------------------------------------------------
    # Update selection info
    # --------------------------------------------------
    def updateSelection(self):
        idx = self["list"].getCurrentIndex()
        total = len(self.scripts)

        if self.scripts and idx < len(self.scripts):
            self["script_name"].setText("• %s" % self.scripts[idx])
        else:
            self["script_name"].setText(_("No scripts found"))

        self.total_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)
        self.current_page = (idx // self.items_per_page) + 1 if total else 1
        self["page_info"].setText("Page %d/%d" % (self.current_page, self.total_pages))

    # --------------------------------------------------
    # Navigation
    # --------------------------------------------------
    def moveUp(self):
        self["list"].moveUp()
        self.updateSelection()

    def moveDown(self):
        self["list"].moveDown()
        self.updateSelection()

    def pageLeft(self):
        idx = max(0, self["list"].getCurrentIndex() - self.items_per_page)
        self["list"].setIndex(idx)
        self.updateSelection()

    def pageRight(self):
        idx = min(len(self.scripts) - 1, self["list"].getCurrentIndex() + self.items_per_page)
        self["list"].setIndex(idx)
        self.updateSelection()

    # --------------------------------------------------
    # Run script in console
    # --------------------------------------------------
    def run(self):
        idx = self["list"].getCurrentIndex()
        script = self.scripts[idx] if self.scripts else None

        if not script:
            self.session.open(MessageBox, _("No script selected!"), MessageBox.TYPE_INFO)
            return

        full_path = join(scriptpath, script)

        if not exists(full_path):
            self.session.open(MessageBox, _("Script not found!"), MessageBox.TYPE_ERROR)
            return

        if full_path.endswith(".sh"):
            chmod(full_path, 0o755)
            cmd = full_path
        else:
            cmd = "python " + full_path

        self.session.open(Console, _("Executing: %s") % script, [cmd])

    # --------------------------------------------------
    # Background run
    # --------------------------------------------------
    def bgrun(self):
        idx = self["list"].getCurrentIndex()
        script = self.scripts[idx] if self.scripts else None

        if not script:
            self.session.open(MessageBox, _("No script selected!"), MessageBox.TYPE_INFO)
            return

        full_path = join(scriptpath, script)

        if not exists(full_path):
            self.session.open(MessageBox, _("Script not found!"), MessageBox.TYPE_ERROR)
            return

        if full_path.endswith(".sh"):
            chmod(full_path, 0o755)
            cmd = "sh {}".format(full_path)
        else:
            cmd = "python {}".format(full_path)

        self.container = eConsoleAppContainer()
        self.log_file = "/tmp/scripts_yellow.log"
        open(self.log_file, "w").close()

        try:
            self.container.dataAvail.append(self.logData)
        except:
            self.container.dataAvail_conn = self.container.dataAvail.connect(self.logData)

        try:
            self.container.appClosed.append(self.finishExecution)
        except:
            self.container.appClosed_conn = self.container.appClosed.connect(self.finishExecution)

        self.container.execute(cmd)
        self.session.open(MessageBox, _("Script is running... check log after finish!"), MessageBox.TYPE_INFO, timeout=3)

    # --------------------------------------------------
    # Logging
    # --------------------------------------------------
    def logData(self, data):
        with open(self.log_file, "a") as f:
            f.write(data.decode())
            f.flush()

    def finishExecution(self, retval):
        if retval == 0:
            self.session.openWithCallback(self.openLog, MessageBox, _("Execution completed!"), MessageBox.TYPE_INFO)
        else:
            self.session.openWithCallback(self.openLog, MessageBox, _("Error while running (Code: %d)") % retval, MessageBox.TYPE_ERROR)

    def openLog(self, callback=None):
        if exists(self.log_file):
            try:
                from .File_Commander import File_Commander
                self.session.open(File_Commander, self.log_file)
            except Exception as e:
                self.session.open(MessageBox, _("Error opening log viewer: %s") % str(e), MessageBox.TYPE_ERROR)
        else:
            self.session.open(MessageBox, _("Log file not found!"), MessageBox.TYPE_WARNING)

    # --------------------------------------------------
    # Other actions
    # --------------------------------------------------
    def restart(self):
        self.session.open(Console, _("Restarting Enigma2..."), ["killall -9 enigma2"])

    def remove(self):
        self.session.openWithCallback(self.xremove, MessageBox, _('Remove all scripts?'), MessageBox.TYPE_YESNO)

    def xremove(self, answer=False):
        if answer:
            os_system('rm -rf /usr/script/*')
            self.loadScripts()
            self.session.open(MessageBox, _('Scripts successfully removed!'), MessageBox.TYPE_INFO)

    def update(self):
        self.session.open(Console, _("Installing scripts please wait..."), [
            "wget --no-check-certificate https://raw.githubusercontent.com/eliesat/scripts/main/installer.sh -qO - | /bin/sh"
        ])

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------
    def doClose(self):
        try:
            if hasattr(self, "container"):
                self.container.dataAvail.clear()
                self.container.appClosed.clear()
        except:
            pass
        Screen.doClose(self)
