# -*- coding: utf-8 -*-
from Plugins.Extensions.ElieSatPanelGrid.menus.Helpers import (
    get_local_ip,
    check_internet,
    get_image_name,
    get_python_version,
    get_storage_info,
    get_ram_info,
)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Plugins.Extensions.ElieSatPanelGrid.__init__ import Version
import os
import subprocess

try:
    from Components.Harddisk import harddiskmanager
except ImportError:
    harddiskmanager = None

class Extra2(Screen):
    skin = """
    <screen name="Blank" position="0,0" size="1920,1080" backgroundColor="transparent" flags="wfNoBorder" title="Scripts">
        <ePixmap position="0,0" zPosition="-1" size="1920,1080"
            pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/background/panel_bg.jpg"/>
        <eLabel position="0,0" size="1920,130" zPosition="10" backgroundColor="#000000" />
        <eLabel text="● Extra2 Plugin – Storage Manager"
            position="350,0" size="1400,50" zPosition="11"
            font="Bold;32" halign="left" valign="center" noWrap="1"
            foregroundColor="yellow" backgroundColor="#000000" transparent="0" />
        <eLabel position="0,1075" size="480,5" zPosition="2" backgroundColor="red" />
        <widget name="red" position="0,1000" size="480,75" zPosition="2"
            font="Bold;32" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="0" />
        <eLabel position="480,1075" size="480,5" zPosition="2" backgroundColor="green" />
        <widget name="green" position="480,1000" size="480,75" zPosition="2"
            font="Bold;32" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="0" />
        <eLabel position="960,1075" size="480,5" zPosition="2" backgroundColor="yellow" />
        <widget name="yellow" position="960,1000" size="480,75" zPosition="2"
            font="Bold;32" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="0" />
        <eLabel position="1440,1075" size="480,5" zPosition="2" backgroundColor="blue" />
        <widget name="blue" position="1440,1000" size="480,75" zPosition="2"
            font="Bold;32" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="0" />
        <eLabel position="0,130" size="80,870" zPosition="10" backgroundColor="#000000" />
        <eLabel position="1840,130" size="80,870" zPosition="10" backgroundColor="#000000" />
        <widget source="global.CurrentTime" render="Label"
            position="1350,180" size="500,35" zPosition="12"
            font="Bold;32" halign="center" valign="center"
            foregroundColor="yellow" backgroundColor="#000000" transparent="1">
            <convert type="ClockToText">Format %A %d %B</convert>
        </widget>
        <widget source="global.CurrentTime" render="Label"
            position="1350,220" size="500,35" zPosition="12"
            font="Bold;32" halign="center" valign="center"
            foregroundColor="yellow" backgroundColor="#000000" transparent="1">
            <convert type="ClockToText">Format %H:%M:%S</convert>
        </widget>
        <widget name="image_name" position="1470,420" size="500,35" zPosition="12"
            font="Bold;32" halign="left" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="1" />
        <widget name="python_ver" position="1470,460" size="500,35" zPosition="12"
            font="Bold;32" halign="left" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="1" />
        <widget name="local_ip" position="1470,500" size="500,35" zPosition="12"
            font="Bold;32" halign="left" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="1" />
        <widget name="StorageInfo" position="1470,540" size="500,35" zPosition="12"
            font="Bold;32" halign="left" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="1" />
        <widget name="RAMInfo" position="1470,580" size="500,35" zPosition="12"
            font="Bold;32" halign="left" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="1" />
        <widget name="net_status" position="1470,620" size="500,35" zPosition="12"
            font="Bold;32" halign="left" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="1" />
        <widget name="left_bar" position="20,160" size="60,760" zPosition="20"
            font="Regular;26" halign="center" valign="top" foregroundColor="yellow" transparent="1" noWrap="1" />
        <widget name="right_bar" position="1850,160" size="60,760" zPosition="20"
            font="Regular;26" halign="center" valign="top" foregroundColor="yellow" transparent="1" noWrap="1" />
       
       <widget name="device_list" position="100,300" size="1300,400" zPosition="12"
            font="Regular;32" halign="left" valign="top" foregroundColor="yellow" itemHeight="66" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanel/assets/icon/selection.png" backgroundColor="#000000" transparent="1" />

        <widget name="status" position="100,720" size="1600,35" zPosition="12"
            font="Regular;28" halign="left" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="1" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle(_("Extra2 Storage Manager"))

        # System info
        self["image_name"] = Label("Image: " + get_image_name())
        self["local_ip"] = Label("IP: " + get_local_ip())
        self["StorageInfo"] = Label(get_storage_info())
        self["RAMInfo"] = Label(get_ram_info())
        self["python_ver"] = Label("Python: " + get_python_version())
        self["net_status"] = Label("Net: " + check_internet())

        self["device_list"] = MenuList([])
        self["status"] = Label("Ready.")
        self.device_mounts = {}

        # Buttons
        self["red"] = Label(_("Refresh List"))
        self["green"] = Label(_("Initialize"))
        self["yellow"] = Label(_("Create Swapfile"))
        self["blue"] = Label(_("Fix Inodes"))

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "ok": self.okButtonAction,
                "cancel": self.close,
                "red": self.refreshDevices,
                "green": self.confirmInitialize,
                "yellow": self.createSwapfile,
                "blue": self.fixInodes,
                "up": lambda: self["device_list"].up(),
                "down": lambda: self["device_list"].down(),
            },
            -1,
        )

        self.refreshDevices()

    # ---------------- Device List ----------------
    def refreshDevices(self):
        self["status"].setText("🔍 Scanning devices...")
        devices = self.getAttachedDevices()
        display_list = []

        for dev_path, free_str in devices:
            mount = self.device_mounts.get(dev_path, "Not Mounted")
            display_list.append(f"{dev_path} ({free_str})")
            display_list.append(f"   Mount: {mount}")

        if not display_list:
            display_list.append("❌ No storage devices found.")

        self["device_list"].setList(display_list)
        self["device_list"].moveToIndex(0)
        self["status"].setText(f"✅ Found {len(devices)} device(s).")

    def getAttachedDevices(self):
        devices = []
        self.device_mounts = {}

        if harddiskmanager:
            hddlist = harddiskmanager.HDDList() or []
            for dev_path, hdd in hddlist:
                free = hdd.free()
                free_str = f"{free/1024:.2f} GB free" if free > 1024 else f"{free} MB free"

                mount = self.getMountPoint(dev_path)
                self.device_mounts[dev_path] = mount

                devices.append((dev_path, free_str))
        else:
            # Fallback: list /dev/sd* partitions
            for dev in os.listdir("/dev/"):
                if dev.startswith("sd"):
                    dev_path = f"/dev/{dev}"
                    mount = self.getMountPoint(dev_path)
                    self.device_mounts[dev_path] = mount
                    devices.append((dev_path, "Unknown size"))

        return devices

    def getMountPoint(self, device):
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    if line.startswith(device):
                        return line.split()[1]
        except Exception:
            pass
        return "Not Mounted"

    # ---------------- Buttons ----------------
    def okButtonAction(self):
        self.session.open(MessageBox, _("Select a device and press a color button."), MessageBox.TYPE_INFO, timeout=3)

    def getSelectedDevice(self):
        current = self["device_list"].getCurrent()
        if not current or "No storage" in current:
            self.session.open(MessageBox, _("Please select a valid device first."), MessageBox.TYPE_INFO, timeout=3)
            return None
        return current.split()[0]  # Return actual device path

    def confirmInitialize(self):
        device = self.getSelectedDevice()
        if not device:
            return
        msg = _("⚠ WARNING: All data on %s will be erased! Proceed?") % device
        self.session.openWithCallback(lambda confirmed: self.runAllJobs(device) if confirmed else None,
                                      MessageBox, msg, MessageBox.TYPE_YESNO)

    def createSwapfile(self):
        device = self.getSelectedDevice()
        if not device:
            return
        mountpoint = "/media/hdd"
        swapfile_path = f"{mountpoint}/swapfile"
        os.system(f"mkdir -p {mountpoint}")
        os.system(f"mount {device} {mountpoint} > /dev/null 2>&1")
        self["status"].setText(_("💾 Creating 1GB swapfile..."))
        os.system(f"dd if=/dev/zero of={swapfile_path} bs=1M count=1024 > /dev/null 2>&1")
        os.system(f"chmod 600 {swapfile_path}")
        os.system(f"mkswap {swapfile_path} > /dev/null 2>&1")
        os.system(f"swapon {swapfile_path} > /dev/null 2>&1")
        try:
            with open("/etc/fstab", "r") as f:
                fstab = f.read()
            entry = f"{swapfile_path}\tswap\tswap\tdefaults\t0\t0"
            if entry not in fstab:
                with open("/etc/fstab", "a") as f:
                    f.write(entry + "\n")
        except:
            pass
        self["status"].setText(_("✅ Swapfile created at %s") % swapfile_path)

    def fixInodes(self):
        device = self.getSelectedDevice()
        if not device:
            return
        mountpoint = "/media/hdd"
        os.system(f"umount {device} > /dev/null 2>&1")
        self["status"].setText(_("🔧 Fixing filesystem..."))
        os.system(f"e2fsck -f -y -v -C 0 {device} > /dev/null 2>&1")
        os.system(f"resize2fs -p {device} > /dev/null 2>&1")
        os.system(f"mount {device} {mountpoint} > /dev/null 2>&1")
        self["status"].setText(_("✅ Filesystem fixed and mounted at %s") % mountpoint)

    def runAllJobs(self, device):
        mountpoint = "/media/hdd"
        os.system(f"umount {device} > /dev/null 2>&1")
        self["status"].setText(_("🛠 Initializing %s...") % device)
        os.system(f"mkfs.ext4 -F {device} > /dev/null 2>&1")
        os.system(f"mkdir -p {mountpoint}")
        os.system(f"mount {device} {mountpoint} > /dev/null 2>&1")
        self.createSwapfile()
        self.fixInodes()
        self["status"].setText(_("✅ Done! Device initialized, swapfile created, and filesystem fixed."))


