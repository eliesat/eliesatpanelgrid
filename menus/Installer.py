#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
import tarfile
import urllib.request
from datetime import datetime
import time
import threading
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

PLUGIN_URL = "https://github.com/eliesat/eliesatpanelgrid/archive/main.tar.gz"
SCRIPTS_URL = "https://github.com/eliesat/scripts/archive/main.tar.gz"

FURY_SCRIPT_URL = "https://gitlab.com/eliesat/skins/-/raw/main/all/fury-fhd/fury-fhdq.sh"

PLUGIN_TMP = "/tmp/eliesatpanelgrid-main.tar.gz"
SCRIPTS_TMP = "/tmp/scripts-main.tar.gz"
FURY_TMP = "/tmp/fury-fhdq.sh"

PLUGIN_DIR = "/usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid"
SCRIPTS_PATH = "/usr/script/Eliesat-Eliesatpanel.sh"
FURY_SKIN_DIR = "/usr/share/enigma2/Fury-FHD"
ENIGMA_SETTINGS = "/etc/enigma2/settings"

OUTPUT_LOG = "/tmp/panel.txt"


# --------------------------------------------------
# UTILITIES
# --------------------------------------------------

def log(msg, newline=True):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    if newline:
        print(line)
    else:
        print(f"\r{line}", end="", flush=True)

    with open(OUTPUT_LOG, "a") as f:
        f.write(line + "\n")

    sys.stdout.flush()


def run(cmd, silent=False):
    if silent:
        return subprocess.call(cmd, shell=True,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    return subprocess.call(cmd, shell=True)


def check_connection():
    try:
        urllib.request.urlopen("https://github.com", timeout=5)
        return True
    except:
        return False


def get_image():
    image_text = "unknown"
    if os.path.exists("/etc/image-version"):
        with open("/etc/image-version") as f:
            for line in f:
                if "creator" in line.lower():
                    image_text = line.split("=")[-1].strip()
                    break
    elif os.path.exists("/etc/issue"):
        with open("/etc/issue") as f:
            image_text = f.readline().strip()

    # Clean up literal escape sequences like \n \l
    image_text = image_text.replace("\\n", "").replace("\\l", "").strip()
    return image_text


def detect_package_manager():
    if os.path.exists("/etc/opkg/opkg.conf"):
        return "opkg"
    elif os.path.exists("/etc/apt/apt.conf"):
        return "apt"
    return None


def install_package(pkg, manager):
    if manager == "opkg":
        run("opkg update", silent=True)
        run(f"opkg install {pkg}", silent=True)
    elif manager == "apt":
        run("apt-get update", silent=True)
        run(f"apt-get install -y {pkg}", silent=True)


def download(url, dest):
    urllib.request.urlretrieve(url, dest)


def extract_tar(tar_path, dest="/tmp"):
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=dest, numeric_owner=False)


# --------------------------------------------------
# FURY INSTALL LOGIC
# --------------------------------------------------

def install_and_force_fury(silent=False):
    """
    Install Fury-FHD if missing and force it as primary skin.
    If silent=True, do not print messages (used when Fury is already installed).
    """
    try:
        fury_missing = not os.path.isdir(FURY_SKIN_DIR)

        if fury_missing:
            if not silent:
                log("OpenPLi detected with Python < 3.10")
                log("Some features may not work correctly")
                log("Downloading and installing Fury-FHD please wait...")
            download(FURY_SCRIPT_URL, FURY_TMP)
            if os.path.exists(FURY_TMP):
                run(f"chmod +x {FURY_TMP}", silent=True)
                run(f"/bin/sh {FURY_TMP}", silent=True)
                os.remove(FURY_TMP)

        # Always force primary skin
        if os.path.exists(ENIGMA_SETTINGS):
            with open(ENIGMA_SETTINGS, "r") as f:
                lines = f.readlines()

            with open(ENIGMA_SETTINGS, "w") as f:
                for line in lines:
                    if not line.startswith("config.skin.primary_skin="):
                        f.write(line)
                f.write("config.skin.primary_skin=Fury-FHD/skin.xml\n")

        if fury_missing and not silent:
            log("Fury-FHD successfully installed and set as primary.")

    except Exception as e:
        log(f"ERROR during Fury setup: {e}")


# --------------------------------------------------
# ANIMATION
# --------------------------------------------------

def animated_message(stop_event):
    message = "> Downloading and installing ElieSatPanelGrid please wait"
    dots = ["   ", ".  ", ".. ", "..."]
    i = 0
    while not stop_event.is_set():
        print(f"\r{message}{dots[i % len(dots)]}", end="", flush=True)
        i += 1
        time.sleep(0.5)
    print()


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if os.path.exists(OUTPUT_LOG):
    os.remove(OUTPUT_LOG)

log("--------------------------------------------------")
log("Installing ElieSatPanelGrid be patient...")
log("--------------------------------------------------")

if not check_connection():
    log("ERROR: Server unreachable.")
    sys.exit(1)

image = get_image()
python_version = sys.version.split()[0]

log(f"Image  : {image}")
log(f"Python : {python_version}")

# Block DreamOS / closed images
if "dream" in image.lower() or shutil.which("dpkg"):
    log("ERROR: DreamOS / closed image is NOT supported")
    sys.exit(1)

# Block Python 2
if sys.version_info.major == 2:
    log("ERROR: Python 2 is NOT supported")
    sys.exit(1)

# OpenPLi + Python < 3.10 → Fury handling
if "openpli" in image.lower() and sys.version_info.major == 3 and sys.version_info.minor < 10:
    if os.path.isdir(FURY_SKIN_DIR):
        # Fury already installed → force silently
        install_and_force_fury(silent=True)
    else:
        # Fury missing → install normally (with messages)
        install_and_force_fury(silent=False)

pkg_manager = detect_package_manager()

# Start animation
stop_animation = threading.Event()
thread = threading.Thread(target=animated_message, args=(stop_animation,))
thread.start()

# Install dependencies
if pkg_manager:
    install_package("python3-requests", pkg_manager)
    install_package("python3-six", pkg_manager)

# Remove old plugin
if os.path.exists(PLUGIN_DIR):
    shutil.rmtree(PLUGIN_DIR)

# Install plugin
download(PLUGIN_URL, PLUGIN_TMP)
extract_tar(PLUGIN_TMP)

src = "/tmp/eliesatpanelgrid-main"
if os.path.exists(src):
    shutil.move(src, PLUGIN_DIR)

# Install scripts if missing
if not os.path.exists(SCRIPTS_PATH):
    download(SCRIPTS_URL, SCRIPTS_TMP)
    extract_tar(SCRIPTS_TMP)
    run("cp -r /tmp/scripts-main/usr/* /usr/", silent=True)

# Stop animation
stop_animation.set()
thread.join()

# Cleanup
for f in [PLUGIN_TMP, SCRIPTS_TMP]:
    if os.path.exists(f):
        os.remove(f)

log("--------------------------------------------------")
log("--------------------------------------------------")
log("ElieSatPanelGrid installed successfully.")
log("--------------------------------------------------")

# Countdown
for i in range(10, 0, -1):
    log(f"Restarting Enigma2 in {i} seconds...", newline=False)
    time.sleep(1)
print()

# Restart
if pkg_manager == "apt":
    run("systemctl restart enigma2", silent=True)
else:
    run("killall -9 enigma2", silent=True)

log("Done")

