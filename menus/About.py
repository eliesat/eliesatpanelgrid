# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Label import Label
from Plugins.Extensions.ElieSatPanelGrid.menus.Helpers import (
    get_local_ip,
    check_internet,
    get_image_name,
    get_python_version,
    get_storage_info,
    get_ram_info,
)
from Plugins.Extensions.ElieSatPanelGrid.__init__ import Version
from enigma import getDesktop


class Abt(Screen):
    def __init__(self, session):
        # Determine screen resolution
        screen_width = getDesktop(0).size().width()
        if screen_width >= 1920:
            self.width, self.height = 1920, 1080
        else:
            self.width, self.height = 1280, 720

        # Skin
        self.skin = f"""
<screen name="About" position="0,0" size="{self.width},{self.height}" backgroundColor="transparent" flags="wfNoBorder" title="About">
    <ePixmap position="0,0" zPosition="-1" size="{self.width},{self.height}"
        pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/background/panel_bg.jpg"/>

    <!-- Top black bar -->
    <eLabel position="0,0" size="{self.width},130" zPosition="10" backgroundColor="#000000" />

    <!-- Title -->
    <eLabel text="● About ElieSatPanel"
        position="350,0" size="1400,50" zPosition="11"
        font="Bold;32" halign="left" valign="center" noWrap="1"
        foregroundColor="yellow" backgroundColor="#000000"
        transparent="0" />

    <!-- Left / Right bars -->
    <eLabel position="0,130" size="80,{self.height-210}" zPosition="10" backgroundColor="#000000" />
    <eLabel position="{self.width-80},130" size="80,{self.height-210}" zPosition="10" backgroundColor="#000000" />

    <!-- Scrollable About text -->
    <widget name="about_text"
        position="200,180" size="1200,800" zPosition="12"
        font="Bold;32" halign="left" valign="top"
        foregroundColor="yellow" backgroundColor="#000000"
        transparent="1" />

    <!-- Page indicator -->
    <widget name="page_info"
        position="{self.width-220},940" size="200,60" zPosition="12"
        font="Bold;32" halign="left" valign="center"
        foregroundColor="yellow" backgroundColor="#000000"
        transparent="1" />

    <!-- Date -->
    <widget source="global.CurrentTime" render="Label"
        position="1350,180" size="500,35" zPosition="12"
        font="Bold;32" halign="center" valign="center"
        foregroundColor="yellow" backgroundColor="#000000"
        transparent="1">
        <convert type="ClockToText">Format %A %d %B</convert>
    </widget>

    <!-- Clock -->
    <widget source="global.CurrentTime" render="Label"
        position="1350,220" size="500,35" zPosition="12"
        font="Bold;32" halign="center" valign="center"
        foregroundColor="yellow" backgroundColor="#000000"
        transparent="1">
        <convert type="ClockToText">Format %H:%M:%S</convert>
    </widget>

    <!-- System info -->
    <widget name="image_name"
        position="1470,420" size="500,35" zPosition="12"
        font="Bold;32" halign="left" valign="center"
        foregroundColor="yellow" backgroundColor="#000000"
        transparent="1" />
    <widget name="python_ver"
        position="1470,460" size="500,35" zPosition="12"
        font="Bold;32" halign="left" valign="center"
        foregroundColor="yellow" backgroundColor="#000000"
        transparent="1" />
    <widget name="local_ip"
        position="1470,500" size="500,35" zPosition="12"
        font="Bold;32" halign="left" valign="center"
        foregroundColor="yellow" backgroundColor="#000000"
        transparent="1" />
    <widget name="StorageInfo"
        position="1470,540" size="500,35" zPosition="12"
        font="Bold;32" halign="left" valign="center"
        foregroundColor="yellow" backgroundColor="#000000"
        transparent="1" />
    <widget name="RAMInfo"
        position="1470,580" size="500,35" zPosition="12"
        font="Bold;32" halign="left" valign="center"
        foregroundColor="yellow" backgroundColor="#000000"
        transparent="1" />
    <widget name="net_status"
        position="1470,620" size="500,35" zPosition="12"
        font="Bold;32" halign="left" valign="center"
        foregroundColor="yellow" backgroundColor="#000000"
        transparent="1" />

    <!-- Vertical texts -->
    <widget name="left_bar"
        position="20,160" size="60,{self.height-210}" zPosition="20"
        font="Regular;26" halign="center" valign="top"
        noWrap="1" foregroundColor="yellow" backgroundColor="#000000"
        transparent="0" />
    <widget name="right_bar"
        position="{self.width-60},160" size="60,{self.height-210}" zPosition="20"
        font="Regular;26" halign="center" valign="top"
        noWrap="1" foregroundColor="yellow" backgroundColor="#000000"
        transparent="0" />
</screen>
"""

        Screen.__init__(self, session)
        self.session = session
        self.setTitle(_("About ElieSatPanel"))

        # Scrollable text
        about_lines = [
            "● ElieSatPanel, Enjoy a smoother Enigma2 experience!",
            "Lightweight Enigma2 plugin",
            "Quick access to system info, shortcuts & tools",
            "",
            "◆ Features:",
            "  • Display system info (Image, IP, Storage, RAM, Python)",
            "  • Scrollable news, updates & GitHub info",
            "  • Version always visible",
            "  • Works on HD & FHD screens",
            "  • Customizable left/right bars",
            "",
            "◆ Version Info:",
            "  Beta (weekly updates)",
            "",
            "◆ Credits:",
            "  Developed by ElieSat",
            "  Special thanks: JePro & Eagle Servers",
            "",
            "◆ Support:",
            "  WhatsApp: +961 70 787 872",
            "  GitHub: github.com/eliesat/eliesatpanel",
            "",
            "◆ Note:",
            "  Thank you for using ElieSatPanel!",
            "  Feedback and suggestions are welcome.",
            "",
        ]

        self["about_text"] = ScrollLabel("\n".join(about_lines))

        # Page info
        self["page_info"] = Label("Page 1/1")

        # Vertical bars
        self["left_bar"] = Label("\n".join(list("Version " + Version)))
        self["right_bar"] = Label("\n".join(list("By ElieSat")))

        # System info
        self["image_name"] = Label("Image: " + get_image_name())
        self["local_ip"] = Label("IP: " + get_local_ip())
        self["StorageInfo"] = Label(get_storage_info())
        self["RAMInfo"] = Label(get_ram_info())
        self["python_ver"] = Label("Python: " + get_python_version())
        self["net_status"] = Label("Net: " + check_internet())

        # Actions
        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions"],
            {
                "cancel": self.close,
                "up": self.pageUp,
                "down": self.pageDown,
                "left": self.pageUp,
                "right": self.pageDown,
            },
            -1,
        )

    def pageUp(self):
        self["about_text"].pageUp()

    def pageDown(self):
        self["about_text"].pageDown()

