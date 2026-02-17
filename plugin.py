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
    <widget name="bg_icon" position="center,center" size="768,512" backgroundColor="#000000" transparent="0" zPosition="0" />
    <widget name="bg_welcome" position="center,center-330" size="768,45" backgroundColor="#000000" transparent="0" zPosition="4" />
    <widget name="welcome" position="center,center-330" size="768,45" font="Bold;40" halign="center" valign="center" foregroundColor="white" transparent="1" zPosition="5" />
    <widget name="icon" position="center,center" size="768,512" transparent="1" zPosition="1" />
    <widget name="version_label" position="428,center+70" size="300,50" font="Bold;30" halign="center" valign="center" foregroundColor="white" transparent="1" zPosition="5" />
    <widget name="wait_text" position="184,460" size="300,50" font="Bold;40" halign="right" valign="center" foregroundColor="white" transparent="1" zPosition="6" />
    <widget name="wait_dots" position="486,460" size="50,50" font="Bold;40" halign="left" valign="center" foregroundColor="white" transparent="1" zPosition="6" />
</screen>
"""

# ---------------- HD SKIN ----------------
SKIN_HD_XML = """
<screen name="SplashScreenHD" position="480,180" size="640,360" flags="wfNoBorder">
    <widget name="bg_icon" position="center,center" size="640,360" backgroundColor="#000000" transparent="0" zPosition="0" />
    <widget name="bg_welcome" position="center,center-220" size="640,40" backgroundColor="#000000" transparent="0" zPosition="4" />
    <widget name="welcome" position="center,center-220" size="640,40" font="Bold;30" halign="center" valign="center" foregroundColor="white" transparent="1" zPosition="5" />
    <widget name="icon" position="center,center" size="640,360" transparent="1" zPosition="1" />
    <widget name="version_label" position="360,center+50" size="200,40" font="Bold;24" halign="center" valign="center" foregroundColor="white" transparent="1" zPosition="5" />
    <widget name="wait_text" position="120,320" size="200,40" font="Bold;30" halign="right" valign="center" foregroundColor="white" transparent="1" zPosition="6" />
    <widget name="wait_dots" position="340,320" size="40,40" font="Bold;30" halign="left" valign="center" foregroundColor="white" transparent="1" zPosition="6" />
</screen>
"""

# ---------------- DETECT SKIN TYPE ----------------
def detect_skin_type():
    try:
        screen_width = getDesktop(0).size().width()
        if screen_width >= 1280:
            return "FHD"
        else:
            return "HD"
    except Exception:
        return "FHD"

# ---------------- SPLASH SCREEN CLASS ----------------
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

        self["icon"] = Pixmap()
        self["welcome"] = Label("○ Powering Your E2 Experience ○")
        self["version_label"] = Label(f"Version: {self.read_version()}")
        self["wait_text"] = Label("Uploading menus")
        self["wait_dots"] = Label("")

        self.dot_count = 0
        self.downloading = False
        self.files_to_download = []
        self.current_file_index = 0

        self.onLayoutFinish.append(self.load_icon)

        # DOT ANIMATION TIMER
        self.anim_timer = eTimer()
        self.anim_timer.callback.append(self.animate_dots)
        self.anim_timer.start(500, False)

        # START GITHUB CHECK
        self.check_timer = eTimer()
        self.check_timer.callback.append(self.start_github_process)
        self.check_timer.start(100, True)

    # ---------- LOAD ICON ----------
    def load_icon(self):
        icon_file = "splash_icon.png"
        folder = "hd" if self.skin_type == "HD" else "background"
        icon_path = os.path.join(PLUGIN_PATH, f"assets/{folder}/{icon_file}")

        if os.path.exists(icon_path):
            pixmap = LoadPixmap(icon_path)
            if pixmap:
                self["icon"].instance.setPixmap(pixmap)

    # ---------- READ VERSION ----------
    def read_version(self):
        init_file = os.path.join(PLUGIN_PATH, "__init__.py")
        version = "Unknown"
        try:
            with open(init_file, "r") as f:
                content = f.read()
                match = re.search(r"Version\s*=\s*['\"](.+?)['\"]", content)
                if match:
                    version = match.group(1)
        except Exception as e:
            print("[ElieSatPanelGrid] Failed to read version:", e)
        return version

    # ---------- DOT ANIMATION ----------
    def animate_dots(self):
        self.dot_count = (self.dot_count + 1) % 4
        self["wait_dots"].setText("." * self.dot_count)

    # ---------- START GITHUB CHECK ----------
    def start_github_process(self):
        self.check_timer.stop()
        self.downloading = True
        os.makedirs(self.DEST_FOLDER, exist_ok=True)

        api_url = f"https://api.github.com/repos/{self.REPO_OWNER}/{self.REPO_NAME}/contents/{self.FOLDER_PATH}?ref={self.BRANCH}"
        print("[ElieSatPanelGrid] Checking GitHub folder availability...")

        try:
            if 'requests' in globals():
                resp = requests.get(api_url, timeout=5)
                status_code = resp.status_code
            else:
                with urllib_requests.urlopen(api_url) as response:
                    status_code = response.getcode()
                    resp = type('Resp', (), {"text": response.read().decode()})
        except Exception as e:
            print("[ElieSatPanelGrid] GitHub request failed:", e)
            status_code = 0

        if status_code != 200:
            print("[ElieSatPanelGrid] GitHub folder not available.")
            self["wait_text"].setText("Server down!")
            self.downloading = False
            self.open_panel()
            return

        print("[ElieSatPanelGrid] GitHub folder available.")
        if 'requests' in globals():
            self.files_to_download = resp.json()
        else:
            self.files_to_download = json.loads(resp.text)

        # START SEQUENTIAL DOWNLOAD
        self.current_file_index = 0
        self.download_timer = eTimer()
        self.download_timer.callback.append(self.download_next_file)
        self.download_timer.start(100, True)

    # ---------- SEQUENTIAL DOWNLOAD ----------
    def download_next_file(self):
        if self.current_file_index >= len(self.files_to_download):
            print("[ElieSatPanelGrid] All files downloaded!")
            self.downloading = False
            self.download_timer.stop()
            self.open_panel()
            return

        file_info = self.files_to_download[self.current_file_index]
        download_url = file_info.get("download_url")
        if download_url:
            file_name = os.path.basename(download_url)
            dest_path = os.path.join(self.DEST_FOLDER, file_name)
            try:
                if 'requests' in globals():
                    r = requests.get(download_url, timeout=5)
                    with open(dest_path, "wb") as f:
                        f.write(r.content)
                else:
                    with urllib_requests.urlopen(download_url) as u:
                        with open(dest_path, "wb") as f:
                            f.write(u.read())
                print(f"[ElieSatPanelGrid] Downloaded {file_name}")
            except Exception as e:
                print(f"[ElieSatPanelGrid] Failed to download {file_name}: {e}")

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

# ---------------- ENTRY FUNCTION ----------------
def main(session, **kwargs):
    session.open(SplashScreen)

def menuHook(menuid, **kwargs):
    if menuid == "mainmenu":
        return [("ElieSatPanelGrid", main, "eliesat_panel_grid", 46)]
    return []

# ---------------- PLUGIN REGISTRATION ----------------
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
            description="Enigma2 addons panel",
            where=PluginDescriptor.WHERE_MENU,
            fnc=menuHook,
        ),
        PluginDescriptor(
            name="ElieSatPanelGrid",
            description="Enigma2 addons panel",
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=main,
        ),
    ]

