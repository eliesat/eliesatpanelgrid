# -*- coding: utf-8 -*-

# -----------------------------
# IMPORTS
# -----------------------------
from Plugins.Extensions.ElieSatPanelGrid.menus.Helpers import (
    get_local_ip,
    check_internet,
    get_image_name,
    get_python_version,
    get_storage_info,
    get_ram_info,
    is_device_unlocked
)

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Plugins.Extensions.ElieSatPanelGrid.__init__ import Version
from enigma import getDesktop
import os

# -----------------------------
# MAIN CLASS
# -----------------------------
class Piconstudio(Screen):

    width, height = getDesktop(0).size().width(), getDesktop(0).size().height()

    skin_file = (
        "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/skin/piconstudio_fhd.xml"
        if width >= 1920
        else "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/assets/skin/piconstudio_hd.xml"
    )

    try:
        with open(skin_file, "r") as f:
            skin = f.read()
    except Exception as e:
        print(f"[ElieSatPanel] Failed to load skin: {e}")
        skin = "<screen></screen>"

    # -----------------------------
    # SATELLITE LIST
    # -----------------------------
    satellites = {
        "45.0W": "Intelsat 14",
        "43.0W": "Intelsat 11",
        "40.5W": "SES-6",
        "37.5W": "Eutelsat 37 West A",
        "34.5W": "ABS 3A / Intelsat 903",
        "30.0W": "Hispasat 30W-6/4",
        "27.5W": "Intelsat 907",
        "24.5W": "Intelsat 905",
        "22.0W": "NSS-7",
        "20.0W": "Intelsat 901",
        "18.0W": "Intelsat 901 (18W)",
        "15.0W": "Telstar 12 Vantage",
        "14.0E": "Express AM8",
        "12.5W": "Eutelsat 12 West B",
        "11.0W": "Express AM44",
        "8.0W": "Eutelsat 8 West B",
        "7.0W": "Nilesat / Eutelsat 7W",
        "5.0W": "Eutelsat 5 West B",
        "4.0W": "AMOS / Eutelsat 4W",
        "1.0W": "Thor 5/6/7",
        "0.8W": "Nilesat 101/102",
        "1.9E": "BulgariaSat 1",
        "3.0E": "Eutelsat 3B",
        "4.8E": "Astra 4A / SES-5",
        "7.0E": "Eutelsat 7A/7B",
        "9.0E": "Eutelsat 9B",
        "10.0E": "Eutelsat 10A",
        "13.0E": "Hot Bird 13B/13C/13G",
        "16.0E": "Eutelsat 16A",
        "19.2E": "Astra 1KR/L/M/N",
        "21.5E": "Eutelsat 21B",
        "23.5E": "Astra 3B",
        "26.0E": "Arabsat Badr 4/5/6/7",
        "28.2E": "Astra 2E/2F/2G",
        "30.5E": "Arabsat 5A",
        "31.5E": "Astra 5B",
        "33.0E": "Eutelsat 33E",
        "36.0E": "Eutelsat 36B / Express AMU1",
        "39.0E": "Hellas Sat 3 / Eutelsat 39B",
        "42.0E": "Turksat 3A/4A",
        "45.0E": "Azerspace 2 / Intelsat 38",
        "46.0E": "Azerspace 1 / Africasat 1A",
        "51.5E": "Belintersat 1",
        "52.0E": "TurkmenÄlem / MonacoSat",
        "52.5E": "Yahsat 1B/1D",
        "53.0E": "Express AM6",
        "54.9E": "ABS 2A",
        "56.0E": "Express AT1",
        "57.0E": "NSS 12",
        "62.0E": "Intelsat 902",
        "66.0E": "Intelsat 17",
        "68.5E": "Intelsat 20",
        "70.5E": "Eutelsat 70B",
        "75.0E": "ABS 2",
        "80.0E": "INSAT / GSAT",
        "85.0E": "Intelsat 18",
        "88.0E": "ST 2",
        "90.0E": "Yamal 401",
        "93.5E": "GSAT / Insat",
        "95.0E": "NSS 6 / SES 8",
        "100.5E": "AsiaSat 5",
        "105.5E": "AsiaSat 7",
        "108.2E": "Telkom 4",
        "110.0E": "BSAT / Japan",
        "115.0E": "ABS 7 / Apstar 7"
    }

    def __init__(self, session):
        Screen.__init__(self, session)

        # -----------------------------
        # SECURITY CHECK
        # -----------------------------
        if not (is_device_unlocked() and
                os.path.exists("/etc/eliesat_unlocked.cfg") and
                os.path.exists("/etc/eliesat_main_mac.cfg")):
            self.close()
            return

        self.session = session
        self.setTitle(_("PiconStudio"))

        # -----------------------------
        # VERTICAL TEXT
        # -----------------------------
        vertical_left = "\n".join(list("Version " + Version))
        vertical_right = "\n".join(list("By ElieSat"))
        self["left_bar"] = Label(vertical_left)
        self["right_bar"] = Label(vertical_right)

        # -----------------------------
        # SYSTEM INFO LABELS
        # -----------------------------
        self["image_name"] = Label("Image: " + get_image_name())
        self["local_ip"] = Label("IP: " + get_local_ip())
        self["StorageInfo"] = Label(get_storage_info())
        self["RAMInfo"] = Label(get_ram_info())
        self["python_ver"] = Label("Python: " + get_python_version())
        self["net_status"] = Label("Net: " + check_internet())

        # -----------------------------
        # BUTTON LABELS
        # -----------------------------
        self["red"] = Label(_("Red"))
        self["green"] = Label(_("Green"))
        self["yellow"] = Label(_("Yellow"))
        self["blue"] = Label(_("Blue"))

        # -----------------------------
        # SATELLITE MENU
        # -----------------------------
        sat_list = [f"{key} - {value}" for key, value in sorted(self.satellites.items())]
        self["sat_menu"] = MenuList(sat_list, enableWrapAround=True)
        self["sat_menu"].onSelectionChanged.append(self.update_sat_label)

        # -----------------------------
        # BUTTON ACTIONS
        # -----------------------------
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "red": self.dummy,
                "green": self.dummy,
                "yellow": self.dummy,
                "blue": self.dummy,
                "ok": self.show_selected_sat,
                "cancel": self.close,
            },
            -1
        )

    # -----------------------------
    # BUTTON METHODS
    # -----------------------------
    def dummy(self):
        self.session.open(
            MessageBox,
            _("This button is not linked yet."),
            MessageBox.TYPE_INFO,
            timeout=3
        )

    def show_selected_sat(self):
        sel = self["sat_menu"].getCurrent()
        if sel:
            self.session.open(
                MessageBox,
                _("Selected satellite:\n%s") % sel,
                MessageBox.TYPE_INFO
            )

    def update_sat_label(self):
        sel = self["sat_menu"].getCurrent()
        if sel:
            self["image_name"].setText(f"Selected: {sel}")

