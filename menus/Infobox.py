# -*- coding: utf-8 -*-

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.MenuList import MenuList
from enigma import eTimer
import os, re, base64, time, subprocess, json

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
# MAIN INFOBOX SCREEN (UNCHANGED)
# ============================================================
class Infobox(Screen):
    skin = f"""
<screen name="infobox" position="center,center" size="1920,1080">
<ePixmap position="0,0" size="1920,1080" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/background/panel_bg.jpg" zPosition="-10"/>
<eLabel position="0,0" size="1920,130" backgroundColor="#000000" zPosition="10"/>
<eLabel text="● Welcome to ElieSatPanel – Enjoy the best plugins, addons and tools for your E2 box." position="350,20" size="1400,60" font="Bold;32" halign="left" valign="center" foregroundColor="#E6BE3A" backgroundColor="#000000" transparent="0" zPosition="11"/>
<eLabel position="90,110" size="1740,780" backgroundColor="#000000" transparent="0" zPosition="-1"/>
<widget name="list" position="120,140" size="1680,720" font="Regular;30" foregroundColor="#E6BE3A" transparent="1" zPosition="5"/>
<eLabel position="0,1020" size="480,40" text="System Monitor" font="Bold;30" halign="center" foregroundColor="#E6BE3A" backgroundColor="#000000" transparent="0"/>
<eLabel position="480,1020" size="480,40" text="IPTV" font="Bold;30" halign="center" foregroundColor="#E6BE3A" backgroundColor="#000000" transparent="0"/>
<eLabel position="960,1020" size="480,40" text="NCam" font="Bold;30" halign="center" foregroundColor="#E6BE3A" backgroundColor="#000000" transparent="0"/>
<eLabel position="1440,1020" size="480,40" text="OSCam" font="Bold;30" halign="center" foregroundColor="#E6BE3A" backgroundColor="#000000" transparent="0"/>
<eLabel position="0,1075" size="480,5" backgroundColor="red" transparent="0" zPosition="10"/>
<eLabel position="480,1075" size="480,5" backgroundColor="green" transparent="0" zPosition="10"/>
<eLabel position="960,1075" size="480,5" backgroundColor="yellow" transparent="0" zPosition="10"/>
<eLabel position="1440,1075" size="480,5" backgroundColor="blue" transparent="0" zPosition="10"/>
</screen>
"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self["list"] = ScrollLabel("")

        self.prev_rx = 0
        self.prev_tx = 0
        self.prev_time = time.time()

        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "ColorActions"],
            {
                "cancel": self.close,
                "up": self["list"].pageUp,
                "down": self["list"].pageDown,
                "red": self.openSystemMonitor,
                "green": self.openIPTV,
                "yellow": self.openNCam,
                "blue": self.showOscam
            }
        )

        self.timer = eTimer()
        self.timer.callback.append(self.update_info)
        self.timer.start(1000, True)

        self.update_info()

    def update_info(self):
        lst = []

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

    # ---------------- BUTTON ACTIONS ----------------
    def openSystemMonitor(self): self.session.open(SystemMonitorScreen)
    def openIPTV(self): self.session.open(PlaceholderScreen,"IPTV")
    def openNCam(self): self.session.open(PlaceholderScreen,"NCam")
    def showOscam(self): self.session.open(OscamReadersScreen)

# ============================================================
# SYSTEM MONITOR SCREEN (NEW)
# ============================================================
# -*- coding: utf-8 -*-

class SystemMonitorScreen(Screen):
    skin = f"""
<screen name="SystemMonitor" position="center,center" size="1920,1080">
<ePixmap position="0,0" size="1920,1080" pixmap="{BG}" zPosition="-10"/>
<eLabel position="0,0" size="1920,130" backgroundColor="#000000" zPosition="10"/>
<eLabel text="● Welcome to ElieSatPanel – Enjoy the best plugins, addons and tools for your E2 box." position="350,20" size="1400,60" font="Bold;32" halign="left" valign="center" foregroundColor="#E6BE3A" backgroundColor="#000000" transparent="0" zPosition="11"/>
<eLabel position="90,110" size="1740,780" backgroundColor="#000000" transparent="0" zPosition="-1"/>
<widget name="list" position="120,140" size="1680,720" font="Regular;30" foregroundColor="#E6BE3A" transparent="1" zPosition="5"/>
<eLabel position="0,1075" size="480,5" backgroundColor="red" transparent="0" zPosition="10"/>
<eLabel position="480,1075" size="480,5" backgroundColor="green" transparent="0" zPosition="10"/>
<eLabel position="960,1075" size="480,5" backgroundColor="yellow" transparent="0" zPosition="10"/>
<eLabel position="1440,1075" size="480,5" backgroundColor="blue" transparent="0" zPosition="10"/>
</screen>
"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self["list"] = ScrollLabel(self.build_text())

        self["actions"] = ActionMap(
            ["OkCancelActions","DirectionActions"],
            {
                "cancel": self.close,
                "up": self["list"].pageUp,
                "down": self["list"].pageDown
            }
        )

    def build_text(self):
        # --- System Info ---
        img = run_cmd("grep '^distro=' /etc/image-version | cut -d= -f2")
        ver = run_cmd("grep '^version=' /etc/image-version | cut -d= -f2")
        py = run_cmd("python3 -V | awk '{print $2}'")
        arch = run_cmd("uname -m")
        ker = run_cmd("uname -r")
        
        # --- Hardware Info ---
        model = safe_read("/proc/stb/info/model")
        uptime = run_cmd("uptime -p")
        load = run_cmd("awk '{print $1}' /proc/loadavg")
        temp = run_cmd("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{printf \"%.1fC\",$1/1000}'")
        
        # --- Resources ---
        ram = run_cmd("free -h | awk '/Mem:/ {print $3\" / \"$2}'")
        flash = run_cmd("df -h / | awk 'NR==2 {print $3\" / \"$2}'")

        text = []
        text.append("○ System")
        text.append("-" * 35)
        text.append("• Image Name    : %s" % img)
        text.append("• Image Version : %s" % ver)
        text.append("• Python        : %s" % py)
        text.append("• Architecture  : %s" % arch)
        text.append("• Kernel        : %s" % ker)
        text.append("")
        text.append("○ Hardware")
        text.append("-" * 35)
        text.append("• Model     : %s" % model)
        text.append("• Uptime    : %s" % uptime)
        text.append("• CPU Temp  : %s" % temp)
        text.append("• CPU Load  : %s" % load)
        text.append("")
        text.append("○ Resources")
        text.append("-" * 35)
        text.append("• RAM Usage   : %s" % ram)
        text.append("• Flash Usage : %s" % flash)
        
        return "\n".join(text)

# ============================================================
# PLACEHOLDER SCREEN FOR IPTV / NCam
# ============================================================
class PlaceholderScreen(Screen):
    skin = f"""
<screen name="Placeholder" position="center,center" size="1920,1080">
<ePixmap position="0,0" size="1920,1080" pixmap="{BG}" zPosition="-10"/>
<eLabel text="Coming Soon..." position="0,450" size="1920,80" font="Bold;48" halign="center" foregroundColor="#E6BE3A"/>
</screen>
"""
    def __init__(self, session, title="Coming Soon"):
        Screen.__init__(self, session)
        self["actions"] = ActionMap(["OkCancelActions"], {"cancel": self.close})

# ============================================================
# OSCAM READERS SCREEN (FINAL — COLORS + ALIGNMENT)
# ============================================================
class OscamReadersScreen(Screen):

    skin = """
<screen name="OscamReadersScreen" position="center,center" size="1920,1080">
<ePixmap position="0,0" size="1920,1080" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/background/panel_bg.jpg" zPosition="-10"/>
<eLabel position="0,0" size="1920,130" backgroundColor="#000000" zPosition="10"/>
<eLabel text="● Welcome to ElieSatPanel – Enjoy the best plugins, addons and tools for your E2 box." position="350,20" size="1400,60" font="Bold;32" foregroundColor="#E6BE3A" backgroundColor="#000000" zPosition="11"/>
<eLabel position="90,120" size="1740,780" backgroundColor="#000000" zPosition="-1"/>
<!-- Header row -->
<eLabel text="READER                │ADDRESS                    │PORT      │PROTOCOL      │STATUS" position="100,150" size="1720,40" font="Console;30" foregroundColor="#E6BE3A" backgroundColor="#000000" zPosition="6"/>
<!-- Header separator -->
<eLabel text="────────────────────────────────────────────────────────────────────────────────────" position="100,185" size="1720,40" font="Console;30" foregroundColor="#E6BE3A" backgroundColor="#000000" zPosition="6"/>
<!-- Scrollable list -->
<widget name="list" position="100,225" size="1720,625" font="Console;30" foregroundColor="#E6BE3A" transparent="1" zPosition="5" scrollbarMode="showOnDemand"/>
<!-- Black bottom bar -->
<eLabel position="0,1015" size="1920,50" backgroundColor="#000000" zPosition="9"/>
<!-- Color bars -->
<eLabel position="0,1075" size="480,5" backgroundColor="red" zPosition="12"/>
<eLabel position="480,1075" size="480,5" backgroundColor="green" zPosition="12"/>
<eLabel position="960,1075" size="480,5" backgroundColor="yellow" zPosition="12"/>
<eLabel position="1440,1075" size="480,5" backgroundColor="blue" zPosition="12"/>
<!-- Centered title instead of Oscam.server -->
<widget name="title" position="0,950" size="1920,50" font="Bold;28" halign="center" foregroundColor="#E6BE3A" transparent="1"/>
</screen>
"""

    # --------------------------------------------------------

    def __init__(self, session):
        Screen.__init__(self, session)

        # Title label in the middle
        self["title"] = Label("OSCam Readers Status")

        # ScrollLabel for readers
        self["list"] = ScrollLabel("")

        # Actions (no Back/Reload)
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "cancel": self.close,
                "up": self["list"].pageUp,
                "down": self["list"].pageDown,
                "yellow": self.reload,  # keeps logic intact
            },
        )

        self.timer = eTimer()
        self.timer.callback.append(self.reload)
        self.timer.start(10000, False)

        self.reload()

    # ========================================================
    # STATUS COLOR ENGINE
    # ========================================================
    def colorStatus(self, status, proto):

        s = status.lower()
        if proto == "emu":
            return "\\c0000FF00CardOK\\c00E6BE3A"
        if s == "connected":
            return "\\c0000FF00connected\\c00E6BE3A"
        if s == "off":
            return "\\c00FF0000Off\\c00E6BE3A"
        return status

    # ========================================================
    # FETCH WEBIF
    # ========================================================
    def fetchWebif(self):
        try:
            auth = base64.b64encode(("%s:%s" % (USER, PASS)).encode()).decode()
            req = Request(OSCAM_URL)
            req.add_header("Authorization", "Basic %s" % auth)
            return urlopen(req, timeout=5).read().decode("utf-8", "ignore")
        except:
            return ""

    # ========================================================
    # PARSE SERVER
    # ========================================================
    def parseServer(self):

        readers = []

        if not os.path.exists(CONFIG):
            return readers

        reader = ""
        host = "-"
        port = "-"
        proto = "-"
        status = "ON"

        def push():
            if reader:
                readers.append({
                    "label": reader,
                    "host": host,
                    "port": port,
                    "proto": proto.lower(),
                    "status": status
                })

        for raw in open(CONFIG):
            line = raw.strip()
            if line.startswith("[reader]"):
                push()
                reader, host, port, proto, status = "", "-", "-", "-", "ON"
            elif line.startswith("label"):
                reader = line.split("=",1)[1].strip()
            elif line.startswith("protocol"):
                proto = line.split("=",1)[1].strip()
            elif line.startswith("device"):
                parts = line.split("=",1)[1].split(",")
                host = parts[0].strip()
                if len(parts) > 1:
                    port = parts[1].strip()
            elif line.startswith("enable"):
                if line.split("=")[1].strip() == "0":
                    status = "OFF"

        push()
        return readers

    # ========================================================
    # STATUS DETECTION
    # ========================================================
    def detectStatus(self, html, reader):

        proto = reader["proto"]

        if reader["status"] == "OFF":
            return "Unreachable", 3

        if not html:
            return "Unknown", 3

        block = re.search(r">" + re.escape(reader["label"]) + r"<.*?</tr>", html, re.I | re.S)
        if not block:
            return "Unknown", 3

        info = block.group(0).lower()
        if "cardok" in info or "connected" in info:
            state = "connected"
            priority = 1
        elif "online" in info:
            state = "Off"
            priority = 2
        elif "offline" in info or "error" in info or "disconnected" in info:
            state = "Unreachable"
            priority = 3
        else:
            state = "Unknown"
            priority = 3

        if proto in ("cccam", "newcamd", "mgcamd"):
            priority += 10

        return state, priority

    # ========================================================
    # MAIN RELOAD
    # ========================================================
    def reload(self):

        readers = self.parseServer()
        html = self.fetchWebif()

        rows = []

        W_READER = 22
        W_ADDRESS = 27
        W_PORT = 10
        W_PROTOCOL = 14

        for r in readers:
            status, prio = self.detectStatus(html, r)
            colored_status = self.colorStatus(status, r["proto"])

            line = "{:<{}}│{:<{}}│{:<{}}│{:<{}}│{}".format(
                r["label"], W_READER,
                r["host"], W_ADDRESS,
                r["port"], W_PORT,
                r["proto"], W_PROTOCOL,
                colored_status
            )
            rows.append((prio, line))

        rows.sort(key=lambda x: x[0])

        # spacer line prevents clipping under header
        lines = [""]
        lines.extend(row for _, row in rows)

        self["list"].setText("\n".join(lines))
