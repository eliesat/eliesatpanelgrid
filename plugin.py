# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Pixmap import Pixmap
from Components.Label import Label
from Tools.LoadPixmap import LoadPixmap
from enigma import eTimer, getDesktop, eConsoleAppContainer
import os
import json
import re

try:
    import requests
except ImportError:
    import urllib.request as urllib_requests

PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid"
INSTALLER_SCRIPT = os.path.join(PLUGIN_PATH, "menus/Installer.py")

# ---------------- FHD SKIN ----------------
SKIN_FHD_XML = """
<screen name="SplashScreenFHD" position="575,280" size="768,512" flags="wfNoBorder">
    <widget name="bg_icon" position="center,center" size="768,512" backgroundColor="#000000" transparent="0"/>
    <widget name="welcome" position="center,center-330" size="768,45" font="Bold;40"
        halign="center" valign="center" foregroundColor="white" transparent="1"/>
    <widget name="icon" position="center,center" size="768,512" transparent="1"/>
    <widget name="version_label" position="428,center+70" size="300,50"
        font="Bold;30" halign="center" valign="center" foregroundColor="white"/>
    <widget name="wait_text" position="184,460" size="300,50"
        font="Bold;40" halign="right" valign="center" foregroundColor="white"/>
    <widget name="wait_dots" position="486,460" size="50,50"
        font="Bold;40" halign="left" valign="center" foregroundColor="white"/>
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
    <widget name="wait_text" position="120,320" size="300,40"
        font="Bold;30" halign="right" valign="center" foregroundColor="white"/>
    <widget name="wait_dots" position="430,320" size="40,40"
        font="Bold;30" halign="left" valign="center" foregroundColor="white"/>
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

    def __init__(self, session):
        self.skin_type = detect_skin_type()
        self.skin = SKIN_HD_XML if self.skin_type == "HD" else SKIN_FHD_XML

        Screen.__init__(self, session)

        # widgets
        self["icon"] = Pixmap()
        self["welcome"] = Label("○ Powering Your E2 Experience ○")
        self["version_label"] = Label("Version: %s" % self.read_version())
        self["wait_text"] = Label("")
        self["wait_dots"] = Label("")

        self.dot_count = 0
        self.is_updating = False

        self.onLayoutFinish.append(self.load_icon)

        # animation timer
        self.anim_timer = eTimer()
        self.anim_timer.callback.append(self.animate_dots)
        self.anim_timer.start(500, False)

        # start version check immediately
        self.version_timer = eTimer()
        self.version_timer.callback.append(self.check_version)
        self.version_timer.start(100, True)

    # ---------- LOAD ICON ----------
    def load_icon(self):
        icon = "splash_icon_hd.png" if self.skin_type == "HD" else "splash_icon.png"
        path = os.path.join(PLUGIN_PATH, "assets/background", icon)
        if os.path.exists(path):
            pixmap = LoadPixmap(path)
            if pixmap:
                self["icon"].instance.setPixmap(pixmap)

    # ---------- READ VERSION ----------
    def read_version(self):
        try:
            with open(os.path.join(PLUGIN_PATH, "__init__.py")) as f:
                m = re.search(r"Version\s*=\s*['\"](.+?)['\"]", f.read())
                return m.group(1) if m else "Unknown"
        except:
            return "Unknown"

    # ---------- DOT ANIMATION ----------
    def animate_dots(self):
        self.dot_count = (self.dot_count + 1) % 4
        self["wait_dots"].setText("." * self.dot_count)

    # ---------- VERSION CHECK ----------
    def check_version(self):
        self.version_timer.stop()
        local_version = self.read_version()
        url = "https://raw.githubusercontent.com/eliesat/eliesatpanelgrid/main/__init__.py"

        try:
            if 'requests' in globals():
                r = requests.get(url, timeout=5)
                content = r.text if r.status_code == 200 else ""
            else:
                with urllib_requests.urlopen(url) as f:
                    content = f.read().decode()

            m_version = re.search(r"Version\s*=\s*['\"](.+?)['\"]", content)
            remote_version = m_version.group(1) if m_version else None

            m_changelog = re.search(r"changelog\s*=\s*['\"](.+?)['\"]", content)
            remote_changelog = m_changelog.group(1) if m_changelog else ""

            if remote_version and remote_version != local_version:
                message_text = f"New version {remote_version} is available.\n{remote_changelog}\nDo you want to update?"
                self.session.openWithCallback(
                    self.update_answer,
                    MessageBox,
                    message_text,
                    MessageBox.TYPE_YESNO
                )
            else:
                # no update → start menu download
                self.start_github_process()

        except:
            # if request fails → start menu download
            self.start_github_process()

    # ---------- UPDATE ANSWER ----------
    def update_answer(self, answer):
        if answer:
            self.is_updating = True
            self["wait_text"].setText("Updating")
            self["wait_dots"].setText("")
            if not os.path.exists(INSTALLER_SCRIPT):
                print("[ElieSatPanelGrid] Installer.py missing")
                self.start_github_process()
                return
            try:
                self.container = eConsoleAppContainer()
                self.container.appClosed.append(self.install_finished)
                self.container.execute("/usr/bin/python3 %s" % INSTALLER_SCRIPT)
            except Exception as e:
                print("[ElieSatPanelGrid] Update error:", e)
                self.start_github_process()
        else:
            # user selected NO → start menu download
            self.start_github_process()

    # ---------- INSTALL FINISHED ----------
    def install_finished(self, retval):
        print("[ElieSatPanelGrid] Installer finished:", retval)
        os.system("killall -9 enigma2")

    # ---------- DOWNLOAD FILES ----------
    def start_github_process(self):
        self["wait_text"].setText("Uploading menus")
        os.makedirs(self.DEST_FOLDER, exist_ok=True)

        api_url = f"https://api.github.com/repos/{self.REPO_OWNER}/{self.REPO_NAME}/contents/{self.FOLDER_PATH}?ref={self.BRANCH}"
        try:
            if 'requests' in globals():
                resp = requests.get(api_url, timeout=5)
                files = resp.json() if resp.status_code == 200 else []
            else:
                with urllib_requests.urlopen(api_url) as r:
                    files = json.loads(r.read().decode())
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

        file_info = self.files_to_download[self.current_file_index]
        url = file_info.get("download_url")
        if url:
            dest = os.path.join(self.DEST_FOLDER, os.path.basename(url))
            try:
                if 'requests' in globals():
                    open(dest, "wb").write(requests.get(url, timeout=5).content)
                else:
                    with urllib_requests.urlopen(url) as u:
                        open(dest, "wb").write(u.read())
            except:
                pass

        self.current_file_index += 1
        self.download_timer.start(100, True)

    # ---------- OPEN PANEL ----------
    def open_panel(self):
        self.anim_timer.stop()
        try:
            from Plugins.Extensions.ElieSatPanelGrid.main import EliesatPanel
            self.session.open(EliesatPanel)
        except Exception as e:
            print("[ElieSatPanelGrid] Launch error:", e)
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

