# -*- coding: utf-8 -*-
# ============================================================
# ElieSat Infobox Plugin - FullHD 1920x1080
# Reordered sections: Time & Network -> Geolocation -> System Info
# ============================================================

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
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

def get_network_info():
    interfaces = ["eth0", "eth1", "wlan0", "ra0"]
    for iface in interfaces:
        base = "/sys/class/net/%s" % iface
        if not os.path.exists(base):
            continue
        mac = safe_read(base + "/address").upper()
        if mac == "00:00:00:00:00:00":
            continue
        state = safe_read(base + "/operstate")
        connected = "Connected" if state == "up" else "Disconnected"
        speed_file = base + "/speed"
        if os.path.exists(speed_file):
            sp = safe_read(speed_file)
            speed = "%s Mb/s" % sp if sp.isdigit() else "Unknown"
        else:
            speed = "Wireless"
        return iface, connected, mac, speed
    return "N/A", "Disconnected", "Unavailable", "Unknown"

def human_speed(bytes_per_sec):
    if bytes_per_sec > 1024*1024:
        return "%.1f MB/s" % (bytes_per_sec/(1024*1024))
    elif bytes_per_sec > 1024:
        return "%.1f KB/s" % (bytes_per_sec/1024)
    else:
        return "%d B/s" % bytes_per_sec

# ============================================================
# MAIN INFOBOX SCREEN
# ============================================================
class Infobox(Screen):
    skin = f"""
<screen name="infobox" position="center,center" size="1920,1080">
    <ePixmap position="0,0" size="1920,1080"
        pixmap="{BG}" zPosition="-1" />
    <eLabel text="● Welcome to ElieSatPanel – Enjoy the best plugins, addons and tools for your E2 box."
        position="350,20" size="1400,60"
        font="Bold;32"
        foregroundColor="#E6BE3A"
        transparent="1" />
    <widget name="list"
        position="100,120"
        size="1720,760"
        font="Regular;30"
        foregroundColor="#E6BE3A"
        transparent="1" />
    <!-- Bottom titles -->
    <eLabel position="0,1020" size="480,40"
        text="System"
        font="Bold;30"
        halign="center"
        foregroundColor="#E6BE3A"
        transparent="1"/>
    <eLabel position="480,1020" size="480,40"
        text="Hardware"
        font="Bold;30"
        halign="center"
        foregroundColor="#E6BE3A"
        transparent="1"/>
    <eLabel position="960,1020" size="480,40"
        text="Resources"
        font="Bold;30"
        halign="center"
        foregroundColor="#E6BE3A"
        transparent="1"/>
    <eLabel position="1440,1020" size="480,40"
        text="OSCam"
        font="Bold;30"
        halign="center"
        foregroundColor="#E6BE3A"
        transparent="1"/>
    <!-- Bottom colored bars -->
    <eLabel position="0,1075" size="480,5" zPosition="10" backgroundColor="red" transparent="0" />
    <eLabel position="480,1075" size="480,5" zPosition="10" backgroundColor="green" transparent="0" />
    <eLabel position="960,1075" size="480,5" zPosition="10" backgroundColor="yellow" transparent="0" />
    <eLabel position="1440,1075" size="480,5" zPosition="10" backgroundColor="blue" transparent="0" />
</screen>
"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self["list"] = ScrollLabel("")

        # Previous RX/TX
        self.prev_rx = 0
        self.prev_tx = 0
        self.prev_time = time.time()

        # ActionMap for scrolling, exit, colors
        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "ColorActions"],
            {
                "cancel": self.close,
                "up": self["list"].pageUp,
                "down": self["list"].pageDown,
                "red": self.showSystem,
                "green": self.showHardware,
                "yellow": self.showResources,
                "blue": self.showOscam
            }
        )

        # Timer for live update
        self.timer = eTimer()
        self.timer.callback.append(self.update_info)
        self.timer.start(1000, True)

        self.update_info()

    def update_info(self):
        lst = []

        # ---------------- TIME & NETWORK ----------------
        lst.append("○ Time & Network")
        lst.append("-" * 35)
        lst.append("• Date & Time : %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        tz = safe_read("/etc/timezone") if os.path.exists("/etc/timezone") else run_cmd("date +'%Z %z'")
        lst.append("• Time Zone   : %s" % tz)
        local_ip = run_cmd("ip addr show | awk '/inet / && !/127/ {split($2,a,\"/\");print a[1];exit}'")
        lst.append("• Local IP    : %s" % local_ip)
        try:
            pub_ip = urlopen("https://api.ipify.org", timeout=2).read().decode().strip()
        except:
            pub_ip = "Unavailable"
        lst.append("• Public IP   : %s" % pub_ip)
        ping = "Connected" if run_cmd("ping -c2 -w3 8.8.8.8 >/dev/null && echo ok") == "ok" else "Disconnected"
        lst.append("• Internet    : %s" % ping)
        lst.append("")

        # ---------------- GEOLOCATION ----------------
        lst.append("○ Geolocation")
        lst.append("-" * 35)
        if pub_ip != "Unavailable":
            try:
                info = json.loads(urlopen(f"https://ipinfo.io/{pub_ip}/json", timeout=2).read().decode())
                country = info.get("country", "Unknown")
                region = info.get("region", "Unknown")
                city = info.get("city", "Unknown")
                loc = info.get("loc", "0,0")
                lat, lon = loc.split(",")
                isp = info.get("org", "Unknown")
            except:
                country = region = city = lat = lon = isp = "Unknown"
            lst.append("• Continent : %s" % self.getContinent(country))
            lst.append("• Country   : %s" % country)
            lst.append("• State     : %s" % region)
            lst.append("• City      : %s" % city)
            lst.append("• Latitude  : %s" % lat)
            lst.append("• Longitude : %s" % lon)
            lst.append("• ISP       : %s" % isp)
        lst.append("")

        # ---------------- SYSTEM INFO ----------------
        lst.append("○ System Info")
        lst.append("-" * 35)
        iface, link, mac, speed = get_network_info()
        lst.append("• MAC Address : %s" % mac)
        lst.append("• Link Speed  : %s" % speed)
        rx_file = f"/sys/class/net/{iface}/statistics/rx_bytes"
        tx_file = f"/sys/class/net/{iface}/statistics/tx_bytes"
        try:
            rx = int(safe_read(rx_file))
            tx = int(safe_read(tx_file))
        except:
            rx = tx = 0
        now = time.time()
        dt = max(now - self.prev_time, 1)
        rx_speed = (rx - self.prev_rx)/dt
        tx_speed = (tx - self.prev_tx)/dt
        self.prev_rx = rx
        self.prev_tx = tx
        self.prev_time = now
        lst.append("• RX Speed    : %s" % human_speed(rx_speed))
        lst.append("• TX Speed    : %s" % human_speed(tx_speed))
        lst.append("")

        self["list"].setText("\n".join(lst))

    def getContinent(self, cc):
        mapping = {
            "Asia": ["LB", "AE", "SA", "QA", "KW", "JO", "IQ"],
            "Europe": ["FR", "DE", "IT", "ES", "NL", "GB"],
            "Africa": ["DZ", "EG", "MA", "TN"],
            "North America": ["US", "CA", "MX"]
        }
        for k in mapping:
            if cc in mapping[k]:
                return k
        return "Unknown"

    def showSystem(self): self.session.open(InfoScreen, "System")
    def showHardware(self): self.session.open(InfoScreen, "Hardware")
    def showResources(self): self.session.open(InfoScreen, "Resources")
    def showOscam(self): self.session.open(OscamReadersScreen)

# ============================================================
# INFO SCREEN
# ============================================================
class InfoScreen(Screen):
    skin = f"""
<screen name="InfoScreen" position="center,center" size="1920,1080">
    <ePixmap position="0,0" size="1920,1080"
        pixmap="{BG}" zPosition="-1" />
    <widget name="title"
        position="60,40"
        size="1800,80"
        font="Regular;48"
        halign="center"/>
    <widget name="text"
        position="100,150"
        size="1720,800"
        font="Regular;34"
        foregroundColor="#E6BE3A"
        transparent="1"/>
</screen>
"""

    def __init__(self, session, section):
        Screen.__init__(self, session)
        self["title"] = Label(section)
        self["text"] = ScrollLabel(self.getInfo(section))
        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions"],
            {
                "cancel": self.close,
                "up": self["text"].pageUp,
                "down": self["text"].pageDown
            }
        )

    def getInfo(self, section):
        if section == "System":
            img = run_cmd("grep '^distro=' /etc/image-version | cut -d= -f2")
            ver = run_cmd("grep '^version=' /etc/image-version | cut -d= -f2")
            py = run_cmd("python3 -V | awk '{print $2}'")
            arch = run_cmd("uname -m")
            ker = run_cmd("uname -r")
            return ("Image Name    : %s\n"
                    "Image Version : %s\n"
                    "Python        : %s\n"
                    "Architecture  : %s\n"
                    "Kernel        : %s") % (img, ver, py, arch, ker)
        if section == "Hardware":
            model = safe_read("/proc/stb/info/model")
            uptime = run_cmd("uptime -p")
            temp = run_cmd("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{printf \"%.1fC\",$1/1000}'")
            load = run_cmd("awk '{print $1}' /proc/loadavg")
            return ("Model     : %s\n"
                    "Uptime    : %s\n"
                    "CPU Temp  : %s\n"
                    "CPU Load  : %s") % (model, uptime, temp, load)
        if section == "Resources":
            ram = run_cmd("free -h | awk '/Mem:/ {print $3\" / \"$2}'")
            flash = run_cmd("df -h / | awk 'NR==2 {print $3\" / \"$2}'")
            return ("RAM Usage   : %s\n"
                    "Flash Usage : %s") % (ram, flash)
        return "No Data"

# ============================================================
# OSCAM READERS SCREEN
# ============================================================
class OscamReadersScreen(Screen):
    skin = f"""
<screen name="OscamReadersScreen" position="center,center" size="1920,1080">
    <ePixmap position="0,0" size="1920,1080"
        pixmap="{BG}" zPosition="-1" />
    <widget name="list"
        position="80,120"
        size="1760,820"
        font="Regular;34"
        itemHeight="45"
        scrollbarMode="showOnDemand"/>
    <widget name="footer"
        position="80,960"
        size="1760,60"
        font="Regular;32"
        halign="center"/>
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
        lst = ["Reader        Host            Port   Proto     Status",
               "-" * 70]
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
                    data.append({"label": label,"host": host,"port": port,"proto": proto,"enabled": enabled})
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
            data.append({"label": label,"host": host,"port": port,"proto": proto,"enabled": enabled})
        return data

    def fetchWebif(self, url):
        try:
            auth = base64.b64encode(("%s:%s" % (USER, PASS)).encode()).decode()
            req = Request(url)
            req.add_header("Authorization", "Basic %s" % auth)
            return urlopen(req, timeout=5).read().decode("utf-8","ignore")
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
