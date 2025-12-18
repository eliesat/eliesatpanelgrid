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
    is_device_unlocked,
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
        "All": "Satellites",
        "30.0W": "Hispasat 30W 5/6",
        "14.0W": "Express AM8",
        "7.0W": "Nilesat 201/301 & Eutelsat 8 West B",
        "5.0W": "Eutelsat 5 West B",
        "4.0W": "AMOS 3 & Dror 1",
        "0.8W": "Thor 5/6/7  & intelsat 10 02",
        "1.9E": "BulgariaSat 1",
        "9.0E": "Eutelsat 9B",
        "13.0E": "Hot Bird 13F/13G",
        "16.0E": "Eutelsat 16A",
        "19.2E": "Astra 1KR/1M/1N/1P",
        "23.5E": "Astra 3B/3C",
        "26.0E": "Badr 7/8 & Es'hail 2",
        "28.2E": "Astra 2E/2F/2G",
        "36.0E": "Eutelsat 36D / Express AMU1",
        "39.0E": "Hellas Sat 3 / Eutelsat 39B",
        "42.0E": "Turksat 3A/4A/5A/6B",
        "46.0E": "Azerspace 1",
        "52.0E": "TurkmenÄlem / MonacoSat",
        "52.5E": "al Yah 1",
        "53.0E": "Express AM6",
        "62.0E": "Intelsat 902",
    }

    def __init__(self, session):
        Screen.__init__(self, session)

        # -----------------------------
        # SECURITY CHECK
        # -----------------------------
        if not (
            is_device_unlocked()
            and os.path.exists("/etc/eliesat_unlocked.cfg")
            and os.path.exists("/etc/eliesat_main_mac.cfg")
        ):
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
        # SATELLITE MENU (WEST → EAST + Specials)
        # -----------------------------
        west_sats = []
        east_sats = []
        special_sats = []

        for k, v in Piconstudio.satellites.items():
            try:
                if k.endswith("W"):
                    west_sats.append((float(k[:-1]), k, v))
                elif k.endswith("E"):
                    east_sats.append((float(k[:-1]), k, v))
                else:
                    special_sats.append((k, v))
            except ValueError:
                special_sats.append((k, v))

        # Sort West descending (highest → lowest)
        west_sorted = sorted(west_sats, key=lambda x: -x[0])

        # Sort East ascending (lowest → highest)
        east_sorted = sorted(east_sats, key=lambda x: x[0])

        # Build final menu list
        # Put 'All - Satellites' always on top
        all_entry = []
        other_specials = []

        for k, v in special_sats:
            if k == "All":
                all_entry.append(f"{k} - {v}")
            else:
                other_specials.append(f"{k} - {v}")

        sat_list = (
            all_entry
            + [f"{k} - {v}" for _, k, v in west_sorted + east_sorted]
            + other_specials
        )

        # Assign MenuList

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
            -1,
        )

    # -----------------------------
    # BUTTON METHODS
    # -----------------------------
    def dummy(self):
        self.session.open(
            MessageBox,
            _("This button is not linked yet."),
            MessageBox.TYPE_INFO,
            timeout=3,
        )

    def show_selected_sat(self):
        sel = self["sat_menu"].getCurrent()
        if sel:
            self.session.open(
                MessageBox,
                _("Selected satellite:\n%s") % sel,
                MessageBox.TYPE_INFO,
            )

    def update_sat_label(self):
        sel = self["sat_menu"].getCurrent()
        if sel:
            self["image_name"].setText(f"Selected: {sel}")

