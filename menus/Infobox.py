# -*- coding: utf-8 -*-
# ============================================================
# ElieSat Infobox Plugin - FullHD 1920x1080
# ============================================================

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from enigma import eTimer

import os, re, base64, time, subprocess, json

# Python2/3 urllib compatibility
try:
    from urllib.request import urlopen, Request
except:
    from urllib2 import urlopen, Request

# ---------------- CONFIG ----------------
OSCAM_URL = "http://127.0.0.1:8888/reader.html"
USER = "admin"
PASS = "password"
CONFIG = "/etc/tuxbox/config/oscam.server"
BG = "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/background/panel_bg.jpg"

# ---------------- UTILS ----------------

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
    except:
        return "Unavailable"


def safe_read(file):
    try:
        with open(file) as f:
            return f.read().strip()
    except:
        return "Unknown"

# ============================================================
# MAIN INFOBOX SCREEN
# ============================================================
class Infobox(Screen):

    skin = f"""
    <screen name="infobox" position="center,center" size="1920,1080" title="Infobox">
        <ePixmap position="0,0" size="1920,1080" pixmap="{BG}" zPosition="-1" />
        <eLabel text="● Welcome to ElieSatPanel – Enjoy the best plugins, addons and tools for your E2 box." position="350,20" size="1400,60" zPosition="5" font="Bold;32" halign="left" valign="center" foregroundColor="#E6BE3A" transparent="1" />
        <widget name="list" position="100,120" size="1720,760" font="Regular;30" itemHeight="50" scrollbarMode="showOnDemand" foregroundColor="#E6BE3A" backgroundColor="transparent" foregroundColorSelected="#E6BE3A" backgroundColorSelected="#9A7B00" transparent="1" />
        <widget name="footer" position="0,0" size="0,0" transparent="1" />
        <eLabel position="0,1020" size="480,40" font="Bold;30" halign="center" valign="center" text="System" foregroundColor="#E6BE3A" transparent="1" />
        <eLabel position="480,1020" size="480,40" font="Bold;30" halign="center" valign="center" text="Hardware" foregroundColor="#E6BE3A" transparent="1" />
        <eLabel position="960,1020" size="480,40" font="Bold;30" halign="center" valign="center" text="Resources" foregroundColor="#E6BE3A" transparent="1" />
        <eLabel position="1440,1020" size="480,40" font="Bold;30" halign="center" valign="center" text="OSCam" foregroundColor="#E6BE3A" transparent="1" />
        <eLabel position="0,1075" size="480,4" backgroundColor="#FF0000" />
        <eLabel position="480,1075" size="480,4" backgroundColor="#00FF00" />
        <eLabel position="960,1075" size="480,4" backgroundColor="#FFFF00" />
        <eLabel position="1440,1075" size="480,4" backgroundColor="#0000FF" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self["list"] = MenuList([])
        self["footer"] = Label("")
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions"],
            {
                "cancel": self.close,
                "red": self.showSystem,
                "green": self.showHardware,
                "yellow": self.showResources,
                "blue": self.showOscam
            }
        )
        self.showShellInfo()

    def showShellInfo(self):

        lst = []
        lst.append("=== System Info / Network / Geolocation ===")
        lst.append("-" * 60)
        lst.append("Date & Time : %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        tz = safe_read("/etc/timezone") if os.path.exists("/etc/timezone") else run_cmd("date +'%Z %z'")
        lst.append("Timezone    : %s" % tz)
        local_ip = run_cmd("ip addr show | awk '/inet / && !/127/ {split($2,a,\"/\");print a[1];exit}'")
        lst.append("Local IP    : %s" % local_ip)
        mac = run_cmd("ip link show | awk '/link/ {print $2;exit}'")
        lst.append("MAC Address : %s" % mac)

        try:
            pub_ip = urlopen("https://api.ipify.org", timeout=5).read().decode().strip()
        except:
            pub_ip = "Unavailable"

        lst.append("Public IP   : %s" % pub_ip)
        ping = "Connected" if run_cmd("ping -c2 -w3 8.8.8.8 >/dev/null && echo ok") == "ok" else "Disconnected"
        lst.append("Internet    : %s" % ping)

        if pub_ip != "Unavailable":
            try:
                info = json.loads(urlopen("https://ipinfo.io/%s/json" % pub_ip, timeout=5).read().decode())
                country = info.get("country", "Unknown")
                region = info.get("region", "Unknown")
                city = info.get("city", "Unknown")
                loc = info.get("loc", "0,0")
                lat, lon = loc.split(",")
                isp = info.get("org", "Unknown")
            except:
                country = region = city = lat = lon = isp = "Unknown"

            lst.append("Continent  : %s" % self.getContinent(country))
            lst.append("Country    : %s" % country)
            lst.append("State      : %s" % region)
            lst.append("City       : %s" % city)
            lst.append("Latitude   : %s" % lat)
            lst.append("Longitude  : %s" % lon)
            lst.append("ISP        : %s" % isp)

        self["list"].setList(lst)

    def showSystem(self): self.session.open(InfoScreen, "System")
    def showHardware(self): self.session.open(InfoScreen, "Hardware")
    def showResources(self): self.session.open(InfoScreen, "Resources")
    def showOscam(self): self.session.open(OscamReadersScreen)

    def getContinent(self, cc):
        mapping = {
            "North America": ["US","CA","MX"],
            "South America": ["BR","AR","CL"],
            "Europe": ["GB","FR","DE","IT","ES","NL"],
            "Asia": ["SA","AE","QA","KW","JO","IQ","LB"],
            "Africa": ["DZ","EG","MA","TN"],
            "Oceania": ["AU","NZ"]
        }
        for k in mapping:
            if cc in mapping[k]:
                return k
        return "Unknown"

# ============================================================
# INFO SCREEN
# ============================================================

class InfoScreen(Screen):
    skin = f"""
    <screen name=\"InfoScreen\" position=\"center,center\" size=\"1920,1080\">

        <ePixmap position=\"0,0\" size=\"1920,1080\"
            pixmap=\"{BG}\" zPosition=\"-1\" />

        <widget name=\"title\"
            position=\"60,40\"
            size=\"1800,80\"
            font=\"Regular;48\"
            halign=\"center\"/>

        <widget name=\"text\"
            position=\"100,150\"
            size=\"1720,800\"
            font=\"Regular;34\"/>

    </screen>
    """

    def __init__(self, session, section):
        Screen.__init__(self, session)

        self["title"] = Label(section)
        self["text"] = Label(self.getInfo(section))

        self["actions"] = ActionMap(["OkCancelActions"], {"cancel": self.close})

    def getInfo(self, section):

        if section == "System":
            img = run_cmd("grep '^distro=' /etc/image-version | cut -d= -f2")
            ver = run_cmd("grep '^version=' /etc/image-version | cut -d= -f2")
            py = run_cmd("python3 -V | awk '{print $2}'")
            arch = run_cmd("uname -m")
            ker = run_cmd("uname -r")

            return (
                "Image Name    : %s\n"
                "Image Version : %s\n"
                "Python        : %s\n"
                "Architecture  : %s\n"
                "Kernel        : %s"
            ) % (img, ver, py, arch, ker)

        if section == "Hardware":
            model = safe_read("/proc/stb/info/model")
            uptime = run_cmd("uptime -p")
            temp = run_cmd("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{printf \"%.1fC\",$1/1000}'")
            load = run_cmd("awk '{print $1}' /proc/loadavg")

            return (
                "Model     : %s\n"
                "Uptime    : %s\n"
                "CPU Temp  : %s\n"
                "CPU Load  : %s"
            ) % (model, uptime, temp, load)

        if section == "Resources":
            ram = run_cmd("free -h | awk '/Mem:/ {print $3\" / \"$2}'")
            flash = run_cmd("df -h / | awk 'NR==2 {print $3\" / \"$2}'")

            return (
                "RAM Usage   : %s\n"
                "Flash Usage : %s"
            ) % (ram, flash)

        return "No Data"

# ============================================================
# OSCAM READERS SCREEN
# ============================================================

class OscamReadersScreen(Screen):
    skin = f"""
    <screen name=\"OscamReadersScreen\" position=\"center,center\" size=\"1920,1080\">

        <ePixmap position=\"0,0\" size=\"1920,1080\"
            pixmap=\"{BG}\" zPosition=\"-1\" />

        <widget name=\"list\"
            position=\"80,120\"
            size=\"1760,820\"
            font=\"Regular;34\"
            itemHeight=\"45\"
            scrollbarMode=\"showOnDemand\"/>

        <widget name=\"footer\"
            position=\"80,960\"
            size=\"1760,60\"
            font=\"Regular;32\"
            halign=\"center\"/>

    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)

        self["list"] = MenuList([])
        self["footer"] = Label("YELLOW=Reload   EXIT=Back")

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions"],
            {"yellow": self.reload, "cancel": self.close}
        )

        self.timer = eTimer()
        self.timer.callback.append(self.reload)
        self.timer.start(10000, False)

        self.reload()

    def reload(self):
        readers = self.parseServer()
        html = self.fetchWebif(OSCAM_URL)

        lst = ["Reader        Host            Port   Proto     Status", "-" * 70]

        for r in readers:
            status = self.getStatus(html, r)
            lst.append("%-12s %-15s %-6s %-9s %s" %
                       (r["label"], r["host"], r["port"], r["proto"], status))

        self["list"].setList(lst)

    def parseServer(self):
        data = []
        if not os.path.exists(CONFIG):
            return data

        label = host = port = proto = "-"
        enabled = True

        for line in open(CONFIG):
            line = line.strip()

            if line.startswith("[reader]"):
                if label != "-":
                    data.append({"label": label, "host": host, "port": port, "proto": proto, "enabled": enabled})
                label = host = port = proto = "-"
                enabled = True

            elif line.startswith("label"):
                label = line.split("=", 1)[1].strip()

            elif line.startswith("protocol"):
                proto = line.split("=", 1)[1].strip()

            elif line.startswith("device"):
                parts = line.split("=", 1)[1].split(",")
                host = parts[0]
                port = parts[1] if len(parts) > 1 else "-"

            elif line.startswith("enable"):
                enabled = line.split("=")[1].strip() != "0"

        if label != "-":
            data.append({"label": label, "host": host, "port": port, "proto": proto, "enabled": enabled})

        return data

    def fetchWebif(self, url):
        try:
            auth = base64.b64encode(("%s:%s" % (USER, PASS)).encode()).decode()
            req = Request(url)
            req.add_header("Authorization", "Basic %s" % auth)
            return urlopen(req, timeout=5).read().decode("utf-8", "ignore")
        except:
            return ""

    def getStatus(self, html, r):
        if not r["enabled"]:
            return "DISABLED"

        if not html:
            return "UNKNOWN"

        block = re.search(r["label"] + ".*?</tr>", html, re.I | re.S)
        if not block:
            return "UNKNOWN"

        b = block.group(0).lower()

        if "connected" in b:
            return "ACTIVE"
        if "online" in b:
            return "IDLE"
        if "offline" in b:
            return "OFFLINE"

        return "UNKNOWN"
