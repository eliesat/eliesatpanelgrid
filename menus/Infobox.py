# -*- coding: utf-8 -*-

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from enigma import eTimer
import os, re, base64, time, subprocess, json

# Python2/3 urllib compatibility
try:
    from urllib.request import urlopen
except:
    from urllib2 import urlopen

# ---------------- CONFIG ----------------
OSCAM_URL = "http://127.0.0.1:8888/reader.html"
USER = "admin"
PASS = "password"
CONFIG = "/etc/tuxbox/config/oscam.server"

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

# ---------------- MAIN PLUGIN ----------------
class Infobox(Screen):
    skin = """
    <screen name="infobox" position="center,center" size="900,600" title="Infobox">
        <widget name="list" position="50,60" size="800,480" scrollbarMode="showOnDemand"/>
        <widget name="footer" position="50,550" size="800,30" font="Regular;22"/>
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self["list"] = MenuList([])
        self["footer"] = Label("RED=System  GREEN=Hardware  YELLOW=Resources  BLUE=OSCam Readers  EXIT=Close")

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

        # Show shell script info on open
        self.showShellInfo()

    # ---------------- SHOW SHELL-LIKE INFO ----------------
    def showShellInfo(self):
        lst = ["=== System Info / Network / Geolocation ===","-"*60]

        # Date and Time
        dt = time.strftime("%Y-%m-%d  %H:%M:%S")
        lst.append(f"Date & Time: {dt}")

        # Timezone
        tz_file = "/etc/timezone"
        tz = safe_read(tz_file) if os.path.exists(tz_file) else run_cmd("date +'%Z %z'")
        lst.append(f"Timezone   : {tz}")

        # Local IP
        local_ip = run_cmd("ip addr show | awk '/inet / && !/127.0.0.1/ {split($2,a,\"/\"); print a[1]; exit}'")
        lst.append(f"Local IP   : {local_ip}")

        # MAC Address
        mac = run_cmd("ip link show | awk '/link/ {print $2; exit}'")
        lst.append(f"MAC Address: {mac}")

        # Public IP
        try:
            pub_ip = urlopen("https://api.ipify.org", timeout=5).read().decode().strip()
        except:
            pub_ip = "Unavailable"
        lst.append(f"Public IP  : {pub_ip}")

        # Internet Connectivity
        ping_status = "Connected" if run_cmd("ping -c2 -w3 8.8.8.8 >/dev/null && echo ok") == "ok" else "Disconnected"
        lst.append(f"Internet   : {ping_status}")

        # Geolocation / ISP
        if pub_ip != "Unavailable":
            try:
                info_json = urlopen(f"https://ipinfo.io/{pub_ip}/json", timeout=5).read().decode()
                info = json.loads(info_json)
                country = info.get("country","Unknown")
                region  = info.get("region","Unknown")
                city    = info.get("city","Unknown")
                loc     = info.get("loc","0,0")
                lat, lon = loc.split(",") if "," in loc else ("Unknown","Unknown")
                isp     = info.get("org","Unknown")
            except:
                country=region=city=lat=lon=isp="Unknown"

            # Map country to continent
            continent = self.getContinent(country)
            lst.extend([
                f"Continent : {continent}",
                f"Country   : {country}",
                f"State     : {region}",
                f"City      : {city}",
                f"Latitude  : {lat}",
                f"Longitude : {lon}",
                f"ISP       : {isp}"
            ])

        self["list"].setList(lst)

    # ---------------- BUTTON ACTIONS ----------------
    def showSystem(self):
        self.session.open(InfoScreen, "System")

    def showHardware(self):
        self.session.open(InfoScreen, "Hardware")

    def showResources(self):
        self.session.open(InfoScreen, "Resources")

    def showOscam(self):
        self.session.open(OscamReadersScreen)

    # ---------------- CONTINENT MAPPING ----------------
    def getContinent(self, cc):
        mapping = {
            "North America": ["US","CA","MX"],
            "South America": ["BR","AR","CL","CO","PE","VE"],
            "Europe": ["GB","FR","DE","IT","ES","RU","SE","NO","NL","CH","AT","BE","DK","FI","IE","PT","GR"],
            "Asia": ["SA","AE","QA","KW","BH","OM","JO","IQ","SY","LB","YE"],
            "Africa": ["DZ","EG","LY","MA","SD","TN","MR","SO","DJ","KM","EH"],
            "Oceania": ["AU","NZ","FJ","PG"]
        }
        for cont, countries in mapping.items():
            if cc in countries:
                return cont
        return "Unknown"

# ---------------- INFO SCREEN ----------------
class InfoScreen(Screen):
    skin = """
    <screen name="InfoScreen" position="center,center" size="900,600">
        <widget name="title" position="20,10" size="860,40" font="Regular;28"/>
        <widget name="text" position="20,60" size="860,520" font="Regular;20"/>
    </screen>
    """

    def __init__(self, session, section):
        Screen.__init__(self, session)
        self.section = section
        self["title"] = Label(section)
        self["text"] = Label(self.getInfo(section))

        self["actions"] = ActionMap(
            ["OkCancelActions"],
            {"cancel": self.close}
        )

    def getInfo(self, section):
        if section == "System":
            img_name = run_cmd("grep '^distro=' /etc/image-version | cut -d= -f2") or run_cmd("grep '^NAME=' /etc/os-release | cut -d= -f2 | tr -d '\"'")
            img_ver  = run_cmd("grep '^version=' /etc/image-version | cut -d= -f2") or run_cmd("grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '\"'")
            py_ver   = run_cmd("python3 -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")'") or "Unavailable"
            pkg_mgr  = run_cmd("command -v apt && echo apt || command -v opkg && echo opkg") or "Unknown"
            arch     = run_cmd("uname -m")
            kernel   = run_cmd("uname -r")
            return f"Image Name    : {img_name}\nImage Version : {img_ver}\nPython Ver    : {py_ver}\nPackage Mgr   : {pkg_mgr}\nArchitecture  : {arch}\nKernel        : {kernel}"

        elif section == "Hardware":
            box_model = safe_read("/proc/stb/info/model") or safe_read("/proc/device-tree/model")
            uptime = run_cmd("uptime -p")
            cpu_temp = run_cmd("cat /proc/stb/fp/temp_sensor 2>/dev/null | awk '{printf \"%.1fC\", $1/1000}'") or run_cmd("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{printf \"%.1fC\", $1/1000}'") or "Unknown"
            cpu_load = run_cmd("awk '{print $1}' /proc/loadavg")
            return f"Box Model     : {box_model}\nUptime        : {uptime}\nCPU Temp      : {cpu_temp}\nCPU Load      : {cpu_load}"

        elif section == "Resources":
            ram = run_cmd("free -h | awk '/Mem:/ {print $3 \" / \" $2}'")
            flash = run_cmd("df -h / | awk 'NR==2 {print $3 \" / \" $2}'")
            return f"RAM Usage     : {ram}\nFlash Usage   : {flash}"

        return "No data available"

# ---------------- OSCAM READERS ----------------
class OscamReadersScreen(Screen):
    skin = """
    <screen name="OscamReadersScreen" position="center,center" size="1200,650">
        <widget name="list" position="20,60" size="1160,540" scrollbarMode="showOnDemand"/>
        <widget name="footer" position="20,610" size="1160,30" font="Regular;22"/>
    </screen>
    """
    def __init__(self, session):
        Screen.__init__(self, session)
        self["list"] = MenuList([])
        self["footer"] = Label("YELLOW = Reload   EXIT = Back")
        self["actions"] = ActionMap(["OkCancelActions","ColorActions"], {"yellow": self.reload,"cancel": self.close})
        self.timer = eTimer()
        self.timer.callback.append(self.reload)
        self.timer.start(10000, False)
        self.reload()

    def reload(self):
        readers = self.parseServer()
        html = self.fetchWebif(OSCAM_URL)
        lst = ["Reader        Host            Port   Proto     Status","-"*60]
        for r in readers:
            status = self.getStatus(html,r)
            lst.append("%-12s %-15s %-6s %-9s %s" % (r["label"],r["host"],r["port"],r["proto"],status))
        self["list"].setList(lst)

    def parseServer(self):
        data=[]
        if not os.path.exists(CONFIG): return data
        label=host=port=proto="-"; enabled=True
        for line in open(CONFIG):
            line=line.strip()
            if line.startswith("[reader]"):
                if label!="-": data.append({"label":label,"host":host,"port":port,"proto":proto,"enabled":enabled})
                label=host=port=proto="-"; enabled=True
            elif line.startswith("label"): label=line.split("=",1)[1].strip()
            elif line.startswith("protocol"): proto=line.split("=",1)[1].strip()
            elif line.startswith("device"):
                parts=line.split("=",1)[1].strip().split(",")
                host=parts[0]; port=parts[1] if len(parts)>1 else "-"
            elif line.startswith("enable"): enabled = line.split("=")[1].strip()!="0"
        if label!="-": data.append({"label":label,"host":host,"port":port,"proto":proto,"enabled":enabled})
        return data

    def fetchWebif(self,url):
        try:
            auth = base64.b64encode(("%s:%s"%(USER,PASS)).encode("utf-8")).decode("utf-8")
            req = Request(url)
            req.add_header("Authorization","Basic %s"%auth)
            return urlopen(req,timeout=5).read().decode("utf-8","ignore")
        except: return ""

    def getStatus(self,html,r):
        if not r["enabled"]: return "DISABLED"
        if not html: return "UNKNOWN"
        block = re.search(r["label"]+".*?</tr>",html,re.I|re.S)
        if not block: return "UNKNOWN"
        b=block.group(0).lower()
        if "connected" in b: return "ACTIVE"
        if "online" in b: return "IDLE"
        if "offline" in b: return "OFFLINE"
        return "UNKNOWN"

