# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Tools.LoadPixmap import LoadPixmap
from enigma import eTimer, getDesktop
import os
import re
import tarfile
import shutil
import requests

PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid"

# ---------------- FHD SKIN ----------------
SKIN_FHD_XML = """
<screen name="SplashScreenFHD" position="575,280" size="768,512" flags="wfNoBorder">
    <widget name="bg_icon" position="center,center" size="768,512" backgroundColor="#000000"/>
    <widget name="splash_text" position="35,10" size="700,50" halign="center" valign="center"
        font="Bold;40" foregroundColor="#FFFFFF" transparent="1"/>
    <widget name="icon" position="center,center" size="768,512" transparent="1"/>
    <widget name="version_label" position="428,center+70" size="300,50"
        font="Bold;30" halign="center" valign="center" foregroundColor="#FFFFFF"/>
    <widget name="wait_text" position="234,420" size="420,50"
        font="Bold;30" halign="left" valign="center" foregroundColor="#FFFFFF"/>
    <widget name="progress_bar" position="174,470" size="420,25"
        zPosition="2" backgroundColor="#555555" foregroundColor="#FFFFFF"/>
</screen>
"""

# ---------------- HD SKIN ----------------
SKIN_HD_XML = """
<screen name="SplashScreenHD" position="center,center" size="640,360" flags="wfNoBorder">
<widget name="bg_icon" position="0,0" size="640,360" backgroundColor="#000000"/>
<widget name="splash_text" position="20,10" size="600,40" halign="center" valign="center" font="Bold;28" foregroundColor="#FFFFFF" transparent="1"/>
<widget name="icon" position="center,center" size="640,360" transparent="1"/>
<widget name="version_label" position="340,240" size="260,40" font="Bold;22" halign="center" valign="center" foregroundColor="#FFFFFF"/>
<widget name="wait_text" position="120,300" size="400,35" font="Bold;22" halign="left" valign="center" foregroundColor="#FFFFFF"/>
<widget name="progress_bar" position="120,330" size="400,18" zPosition="2" backgroundColor="#555555" foregroundColor="#FFFFFF"/>
</screen>
"""

# ---------------- SKIN DETECTION ----------------
def detect_skin_type():
    try:
        return "FHD" if getDesktop(0).size().width() >= 1920 else "HD"
    except:
        return "HD"


# ---------------- SPLASH SCREEN ----------------
class SplashScreen(Screen):

    REPO_OWNER = "eliesat"
    REPO_NAME = "eliesatpanelgrid"
    FOLDER_PATH = "assets/data"
    BRANCH = "main"
    DEST_FOLDER = os.path.join(PLUGIN_PATH, "assets/data")

    UPDATE_URL = "https://github.com/eliesat/eliesatpanelgrid/archive/main.tar.gz"
    PACKAGE = "/tmp/eliesatpanelgrid-main.tar.gz"

    def __init__(self, session):

        self.skin_type = detect_skin_type()
        self.skin = SKIN_HD_XML if self.skin_type == "HD" else SKIN_FHD_XML
        Screen.__init__(self, session)

        # Widgets
        self["icon"] = Pixmap()
        self["splash_text"] = Label("○ Powering Your E2 Experience ○")
        self["version_label"] = Label("Version: %s" % self.read_version())
        self["wait_text"] = Label()
        self["progress_bar"] = ProgressBar()
        self["progress_bar"].setValue(0)
        self["progress_bar"].show()

        # Layout actions
        self.onLayoutFinish.append(self.load_icon)
        self.onLayoutFinish.append(self.start_version_check)

    # ---------- START VERSION CHECK ----------
    def start_version_check(self):
        self.version_timer = eTimer()
        self.version_timer.callback.append(self.check_version)
        self.version_timer.start(200, True)

    # ---------- LOAD ICON ----------
    def load_icon(self):
        icon = "splash_icon_hd.png" if self.skin_type == "HD" else "splash_icon.png"
        path = os.path.join(PLUGIN_PATH, "assets/background", icon)
        if os.path.exists(path):
            pixmap = LoadPixmap(path)
            if pixmap:
                self["icon"].instance.setPixmap(pixmap)

    # ---------- READ LOCAL VERSION ----------
    def read_version(self):
        try:
            with open(os.path.join(PLUGIN_PATH, "__init__.py")) as f:
                m = re.search(r"[Vv]ersion\s*=\s*['\"](.+?)['\"]", f.read())
                return m.group(1) if m else "Unknown"
        except:
            return "Unknown"

    # ---------- CHECK REMOTE VERSION ----------
    def check_version(self):

        local = self.read_version()
        url = "https://raw.githubusercontent.com/%s/%s/%s/__init__.py" % (
            self.REPO_OWNER, self.REPO_NAME, self.BRANCH)

        try:

            headers = {"User-Agent": "Mozilla/5.0"}
            content = requests.get(url, headers=headers, timeout=5).text

            m = re.search(r"[Vv]ersion\s*=\s*['\"](.+?)['\"]", content)
            remote = m.group(1) if m else None

            c = re.search(r"changelog\s*=\s*['\"](.+?)['\"]", content)
            changelog = c.group(1) if c else ""

            if remote and remote != local:

                message = (
                    "New version %s is available.\n%s\nDo you want to upgrade?"
                ) % (remote, changelog)

                self.session.openWithCallback(
                    self.update_answer,
                    MessageBox,
                    message,
                    MessageBox.TYPE_YESNO
                )

            else:
                self.start_github_process()

        except Exception as e:
            print("Version check failed:", e)
            self.start_github_process()

    # ---------- UPDATE ANSWER ----------
    def update_answer(self, answer):

        if not answer:
            self.start_github_process()
            return

        self["progress_bar"].show()
        self["progress_bar"].setValue(0)

        self.display_progress = 0
        self.downloaded = 0
        self.phase = "download"
        self.install_index = 0

        self["wait_text"].setText("Upgrading the panel: 0%")

        self.download_update()

    # ---------- DOWNLOAD UPDATE ----------
    def download_update(self):

        try:
            self.req = requests.get(self.UPDATE_URL, stream=True, timeout=10)
            self.total_size = int(self.req.headers.get("content-length", 0))

            self.update_file = open(self.PACKAGE, "wb")
            self.chunk_iter = self.req.iter_content(chunk_size=32768)

            self.upgrade_timer = eTimer()
            self.upgrade_timer.callback.append(self.download_and_install_tick)
            self.upgrade_timer.start(50, True)

        except Exception as e:
            print("Update start error:", e)
            self.start_github_process()

    # ---------- DOWNLOAD + INSTALL ----------
    def download_and_install_tick(self):

        target_progress = self.display_progress

        if self.phase == "download":

            try:
                chunk = next(self.chunk_iter)
                self.update_file.write(chunk)
                self.downloaded += len(chunk)

                if self.total_size > 0:
                    target_progress = int((self.downloaded / self.total_size) * 60)

            except StopIteration:

                self.update_file.close()
                self.phase = "install"

                try:
                    self.tar = tarfile.open(self.PACKAGE, "r:gz")
                    self.members = self.tar.getmembers()
                    self.total_members = len(self.members)
                    self.install_index = 0
                except:
                    self.start_github_process()
                    return

        elif self.phase == "install":

            if self.install_index < self.total_members:

                member = self.members[self.install_index]
                self.tar.extract(member, "/tmp")
                self.install_index += 1

                target_progress = 60 + int(self.install_index / self.total_members * 40)

            else:

                self.tar.close()

                try:
                    os.remove(self.PACKAGE)

                    if os.path.exists(PLUGIN_PATH):
                        shutil.rmtree(PLUGIN_PATH)

                    shutil.move("/tmp/eliesatpanelgrid-main", PLUGIN_PATH)

                except Exception as e:
                    print("Install error:", e)

                target_progress = 100
                self.phase = "done"

        if self.display_progress < target_progress:

            self.display_progress += max(
                1, (target_progress - self.display_progress) // 3
            )

            if self.display_progress > target_progress:
                self.display_progress = target_progress

        self["progress_bar"].setValue(self.display_progress)

        if self.phase in ["download", "install"]:
            self["wait_text"].setText(
                "Upgrading the panel: %d%%" % self.display_progress
            )

        if self.phase != "done":

            self.upgrade_timer.start(50, True)

        else:

            self.upgrade_timer.stop()
            self.session.nav.stopService()
            os.system("killall -9 enigma2")

    # ---------- DOWNLOAD MENU FILES ----------
    def start_github_process(self):

        self["progress_bar"].show()
        self["progress_bar"].setValue(0)
        self["wait_text"].setText("Uploading menus: 0%")

        os.makedirs(self.DEST_FOLDER, exist_ok=True)

        api = "https://api.github.com/repos/%s/%s/contents/%s?ref=%s" % (
            self.REPO_OWNER,
            self.REPO_NAME,
            self.FOLDER_PATH,
            self.BRANCH,
        )

        try:
            files = requests.get(api).json()
        except:
            self.open_panel()
            return

        self.files_to_download = files
        self.current_file_index = 0

        self.download_timer = eTimer()
        self.download_timer.callback.append(self.download_next_file)
        self.download_timer.start(100, True)

    def download_next_file(self):

        if self.current_file_index >= len(self.files_to_download):
            self.open_panel()
            return

        info = self.files_to_download[self.current_file_index]
        url = info.get("download_url")

        if url:
            dest = os.path.join(self.DEST_FOLDER, os.path.basename(url))

            try:
                open(dest, "wb").write(requests.get(url).content)
            except:
                pass

        total = len(self.files_to_download)
        progress = int((self.current_file_index + 1) * 100 / total)

        self["progress_bar"].setValue(progress)
        self["wait_text"].setText("Uploading menus: %d%%" % progress)

        self.current_file_index += 1
        self.download_timer.start(100, True)

    # ---------- OPEN PANEL ----------
    def open_panel(self):

        try:
            from Plugins.Extensions.ElieSatPanelGrid.main import EliesatPanel
            self.session.open(EliesatPanel)
        except Exception as e:
            print("Launch error:", e)

        self.close()


# ---------------- ENTRY ----------------
def main(session, **kwargs):
    session.open(SplashScreen)


def menuHook(menuid, **kwargs):
    if menuid == "mainmenu":
        return [("ElieSatPanelGrid", main, "eliesat_panel_grid", 46)]
    return []


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="ElieSatPanelGrid",
            description="Enigma2 addons panel (auto HD/FHD skin)",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="assets/icon/panel_logo.png",
            fnc=main,
        ),
        PluginDescriptor(
            name="ElieSatPanelGrid",
            where=PluginDescriptor.WHERE_MENU,
            fnc=menuHook,
        ),
        PluginDescriptor(
            name="ElieSatPanelGrid",
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=main,
        ),
    ]
