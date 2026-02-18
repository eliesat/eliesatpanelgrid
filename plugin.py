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
import json
import re

try:
    import requests
except ImportError:
    import urllib.request as urllib_requests

PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid"

# ---------------- FHD SKIN ----------------
SKIN_FHD_XML = """
<screen name="SplashScreenFHD" position="575,280" size="768,512" flags="wfNoBorder">
    <widget name="bg_icon" position="center,center" size="768,512" backgroundColor="#000000"/>
    <widget name="welcome" position="center,center-330" size="768,45" font="Bold;40"
        halign="center" valign="center" foregroundColor="white"/>
    <widget name="icon" position="center,center" size="768,512" transparent="1"/>
    <widget name="version_label" position="428,center+70" size="300,50"
        font="Bold;30" halign="center" valign="center" foregroundColor="white"/>
    <widget name="wait_text" position="234,400" size="320,50"
        font="Bold;30" halign="left" valign="center" foregroundColor="white"/>

    <widget name="update_progress_bar" position="174,460" size="420,25"
        backgroundColor="#555555" foregroundColor="#FFFFFF"/>

    <widget name="progress_bar" position="174,460" size="420,25"
        backgroundColor="#555555" foregroundColor="#FFFFFF"/>
</screen>
"""

# ---------------- HD SKIN ----------------
SKIN_HD_XML = """
<screen name="SplashScreenHD" position="320,180" size="640,360" flags="wfNoBorder">
    <widget name="bg_icon" position="center,center" size="640,360" backgroundColor="#000000"/>
    <widget name="welcome" position="center,center-220" size="640,40"
        font="Bold;30" halign="center" valign="center" foregroundColor="white"/>
    <widget name="icon" position="center,center" size="640,360" transparent="1"/>
    <widget name="version_label" position="360,center+50" size="200,40"
        font="Bold;24" halign="center" valign="center" foregroundColor="white"/>
    <widget name="wait_text" position="210,300" size="400,40"
        font="Bold;24" halign="left" valign="center" foregroundColor="white"/>

    <widget name="update_progress_bar" position="65,310" size="500,20"
        backgroundColor="#333333" foregroundColor="#00baff"/>

    <widget name="progress_bar" position="65,340" size="500,20"
        backgroundColor="#555555" foregroundColor="#FFFFFF"/>
</screen>
"""

# ---------------- DETECT SKIN ----------------
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
    EXTRACT = "/tmp/eliesatpanelgrid-main"

    def __init__(self, session):

        self.skin_type = detect_skin_type()
        self.skin = SKIN_HD_XML if self.skin_type == "HD" else SKIN_FHD_XML
        Screen.__init__(self, session)

        self["icon"] = Pixmap()
        self["welcome"] = Label("○ Powering Your E2 Experience ○")
        self["version_label"] = Label("Version: %s" % self.read_version())
        self["wait_text"] = Label("")

        self["progress_bar"] = ProgressBar()
        self["progress_bar"].setValue(0)

        self["update_progress_bar"] = ProgressBar()
        self["update_progress_bar"].setValue(0)
        self["update_progress_bar"].hide()

        self.onLayoutFinish.append(self.load_icon)

        self.version_timer = eTimer()
        self.version_timer.callback.append(self.check_version)
        self.version_timer.start(100, True)

    # ---------- ICON ----------
    def load_icon(self):
        icon = "splash_icon_hd.png" if self.skin_type == "HD" else "splash_icon.png"
        path = os.path.join(PLUGIN_PATH, "assets/background", icon)
        if os.path.exists(path):
            pixmap = LoadPixmap(path)
            if pixmap:
                self["icon"].instance.setPixmap(pixmap)

    # ---------- VERSION ----------
    def read_version(self):
        try:
            with open(os.path.join(PLUGIN_PATH, "__init__.py")) as f:
                m = re.search(r"Version\s*=\s*['\"](.+?)['\"]", f.read())
                return m.group(1) if m else "Unknown"
        except:
            return "Unknown"

    # ---------- VERSION CHECK ----------
    def check_version(self):
        self.version_timer.stop()

        local = self.read_version()
        url = f"https://raw.githubusercontent.com/{self.REPO_OWNER}/{self.REPO_NAME}/{self.BRANCH}/__init__.py"

        try:
            content = requests.get(url, timeout=5).text
            m = re.search(r"Version\s*=\s*['\"](.+?)['\"]", content)
            remote = m.group(1) if m else None

            if remote and remote != local:
                self.session.openWithCallback(
                    self.update_answer,
                    MessageBox,
                    "New version %s available.\nDo you want to update?" % remote,
                    MessageBox.TYPE_YESNO
                )
            else:
                self.start_github_process()
        except:
            self.start_github_process()

    # ---------- UPDATE ----------
    def update_answer(self, answer):

        if not answer:
            self.start_github_process()
            return

        self["progress_bar"].hide()
        self["update_progress_bar"].show()
        self["wait_text"].setText("Downloading update: 0%")

        self.download_update()

    # NON-BLOCKING DOWNLOAD
    def download_update(self):

        try:
            self.req = requests.get(self.UPDATE_URL, stream=True, timeout=10)
            self.total_size = int(self.req.headers.get("content-length", 0))
            self.downloaded = 0

            self.update_file = open(self.PACKAGE, "wb")
            self.chunk_iter = self.req.iter_content(chunk_size=65536)

            self.update_timer = eTimer()
            self.update_timer.callback.append(self.download_chunk)
            self.update_timer.start(10, True)

        except Exception as e:
            print("Update start error:", e)
            self.start_github_process()

    def download_chunk(self):

        try:
            chunk = next(self.chunk_iter)

            if chunk:
                self.update_file.write(chunk)
                self.downloaded += len(chunk)

                if self.total_size > 0:
                    progress = int(self.downloaded * 100 / self.total_size)
                    self["update_progress_bar"].setValue(progress)
                    self["wait_text"].setText(
                        "Downloading update: %d%%" % progress
                    )

            self.update_timer.start(10, True)

        except StopIteration:
            self.update_file.close()
            self.install_update()

        except Exception as e:
            print("Download error:", e)
            self.start_github_process()

    # INSTALL
    def install_update(self):

        self["wait_text"].setText("Installing update...")

        os.system("rm -rf %s >/dev/null 2>&1" % self.EXTRACT)
        res = os.system("tar -xzf %s -C /tmp >/dev/null 2>&1" % self.PACKAGE)
        os.remove(self.PACKAGE)

        if res == 0:
            os.system("rm -rf %s >/dev/null 2>&1" % PLUGIN_PATH)
            os.makedirs(PLUGIN_PATH, exist_ok=True)
            os.system("mv %s/* %s/ >/dev/null 2>&1" % (self.EXTRACT, PLUGIN_PATH))
            os.system("rm -rf %s >/dev/null 2>&1" % self.EXTRACT)

        os.system("killall -9 enigma2")

    # ---------- MENUS DOWNLOAD (ORIGINAL) ----------
    def start_github_process(self):

        self["update_progress_bar"].hide()
        self["progress_bar"].show()

        self["progress_bar"].setValue(0)
        self["wait_text"].setText("Uploading menus: 0%")

        os.makedirs(self.DEST_FOLDER, exist_ok=True)

        api = f"https://api.github.com/repos/{self.REPO_OWNER}/{self.REPO_NAME}/contents/{self.FOLDER_PATH}?ref={self.BRANCH}"

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

