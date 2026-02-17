from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Pixmap import Pixmap
from Components.Label import Label
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
    <widget name="bg_icon" position="center,center" size="768,512" backgroundColor="#000000" transparent="0" zPosition="0"/>
    <widget name="bg_welcome" position="center,center-330" size="768,45" backgroundColor="#000000" transparent="0" zPosition="4"/>
    <widget name="welcome" position="center,center-330" size="768,45" font="Bold;40" halign="center" valign="center" foregroundColor="white" transparent="1" zPosition="5"/>
    <widget name="icon" position="center,center" size="768,512" transparent="1" zPosition="1"/>
    <widget name="version_label" position="428,center+70" size="300,50" font="Bold;30" halign="center" valign="center" foregroundColor="white" transparent="1" zPosition="5"/>
    <widget name="wait_text" position="184,460" size="300,50" font="Bold;40" halign="right" valign="center" foregroundColor="white" transparent="1" zPosition="6"/>
    <widget name="wait_dots" position="486,460" size="50,50" font="Bold;40" halign="left" valign="center" foregroundColor="white" transparent="1" zPosition="6"/>
</screen>
"""

# ---------------- HD SKIN ----------------
SKIN_HD_XML = """
<screen name="SplashScreenHD" position="320,180" size="640,360" flags="wfNoBorder">
    <widget name="bg_icon" position="center,center" size="640,360" backgroundColor="#000000" transparent="0" zPosition="0"/>
    <widget name="bg_welcome" position="center,center-220" size="640,40" backgroundColor="#000000" transparent="0" zPosition="4"/>
    <widget name="welcome" position="center,center-220" size="640,40" font="Bold;30" halign="center" valign="center" foregroundColor="white" transparent="1" zPosition="5"/>
    <widget name="icon" position="center,center" size="640,360" transparent="1" zPosition="1"/>
    <widget name="version_label" position="360,center+50" size="200,40" font="Bold;24" halign="center" valign="center" foregroundColor="white" transparent="1" zPosition="5"/>
    <widget name="wait_text" position="120,320" size="300,40" font="Bold;30" halign="right" valign="center" foregroundColor="white" transparent="1" zPosition="6"/>
    <widget name="wait_dots" position="430,320" size="40,40" font="Bold;30" halign="left" valign="center" foregroundColor="white" transparent="1" zPosition="6"/>
</screen>
"""

# ---------------- DETECT SKIN TYPE ----------------
def detect_skin_type():
    try:
        width = getDesktop(0).size().width()
        return "FHD" if width >= 1920 else "HD"
    except Exception:
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

        print("[ElieSatPanelGrid] USING SKIN:", self.skin_type)

        self["icon"] = Pixmap()
        self["welcome"] = Label("○ Powering Your E2 Experience ○")
        self["version_label"] = Label(f"Version: {self.read_version()}")
        self["wait_text"] = Label("Uploading menus")
        self["wait_dots"] = Label("")

        self.dot_count = 0
        self.onLayoutFinish.append(self.load_icon)

        # animation
        self.anim_timer = eTimer()
        self.anim_timer.callback.append(self.animate_dots)
        self.anim_timer.start(500, False)

        # github start
        self.check_timer = eTimer()
        self.check_timer.callback.append(self.start_github_process)
        self.check_timer.start(100, True)

    # ---------- LOAD ICON ----------
    def load_icon(self):

        # YOUR REQUESTED PATHS
        if self.skin_type == "HD":
            icon_path = os.path.join(
                PLUGIN_PATH,
                "assets/background/splash_icon_hd.png"
            )
        else:
            icon_path = os.path.join(
                PLUGIN_PATH,
                "assets/background/splash_icon.png"
            )

        print("[ElieSatPanelGrid] Loading icon:", icon_path)

        if not os.path.exists(icon_path):
            print("[ElieSatPanelGrid] Icon missing")
            return

        pixmap = LoadPixmap(icon_path)
        if pixmap:
            self["icon"].instance.setPixmap(pixmap)
        else:
            print("[ElieSatPanelGrid] Pixmap load failed")

    # ---------- READ VERSION ----------
    def read_version(self):
        try:
            with open(os.path.join(PLUGIN_PATH, "__init__.py"), "r") as f:
                m = re.search(r"Version\s*=\s*['\"](.+?)['\"]", f.read())
                return m.group(1) if m else "Unknown"
        except:
            return "Unknown"

    # ---------- DOTS ----------
    def animate_dots(self):
        self.dot_count = (self.dot_count + 1) % 4
        self["wait_dots"].setText("." * self.dot_count)

    # ---------- GITHUB CHECK ----------
    def start_github_process(self):
        self.check_timer.stop()
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

    # ---------- DOWNLOAD ----------
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

