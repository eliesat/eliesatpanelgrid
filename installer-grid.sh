#!/bin/bash

clear >/dev/null 2>&1

# Configuration
###########################################
plugin=eliesatpanelgrid-main.tar.gz
version='3.74'
changelog='1.12.12.2025'
url=https://github.com/eliesat/eliesatpanelgrid/archive/main.tar.gz
package=/tmp/$plugin
rm -rf $package >/dev/null 2>&1

# Check script URL connectivity
###########################################
if wget -q --method=HEAD https://github.com/eliesat/eliesatpanelgrid; then
    connection=ok
else
    echo "> Server is down, try again later..."
    exit 1
fi

# Functions
###########################################
print_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}
print_message "> Start of process ..."
echo "-----------------------------------------------"
echo
sleep 2

cleanup() {
    rm -rf /var/cache/opkg/* /var/lib/opkg/lists/* /run/opkg.lock >/dev/null 2>&1
}

# Check image and python version
###########################################

if [ -f /etc/image-version ]; then
    image_version=$(grep -iF "creator" /etc/image-version | cut -d"=" -f2 | xargs)
elif [ -f /etc/issue ]; then
    image_version=$(head -n1 /etc/issue | awk '{print $1}')
else
    image_version='image not found'
fi

# Get Python version
python_version=$(python -c "import platform; print(platform.python_version())")

print_message "> Image  : $image_version"
sleep 2
print_message "> Python : $python_version"
sleep 2

# Extract Python major & minor
python_major=$(echo "$python_version" | cut -d'.' -f1)
python_minor=$(echo "$python_version" | cut -d'.' -f2)

# ------------------------------------------------
# CASE 1: Closed-source images / DreamOS → EXIT
# ------------------------------------------------
if echo "$image_version" | grep -Eqi "vti|blackhole|dreamos|dreambox" || \
   command -v dpkg >/dev/null 2>&1; then

    if command -v dpkg >/dev/null 2>&1; then
        print_message "> You are using a DreamOS image and it is NOT supported"
    else
        print_message "> Your image is NOT supported"
    fi

    sleep 2
    exit 1
fi

# ------------------------------------------------
# CASE 2: Python 2 → EXIT
# ------------------------------------------------
if [ "$python_major" = "2" ]; then
    print_message "> Your image Python is NOT supported (Python 2 detected)"
    sleep 2
    exit 1
fi

# ------------------------------------------------
# CASE 3: OpenPLi + Python < 3.10 → WARNING
# ------------------------------------------------
if echo "$image_version" | grep -qi "openpli" && \
   [ "$python_major" = "3" ] && [ "$python_minor" -lt 10 ]; then
    print_message "> OpenPLi detected with Python < 3.10"
    sleep 2
    print_message "> Some features may not work correctly"
    sleep 2

#!/bin/sh

SKIN_DIR="/usr/share/enigma2/Fury-FHD"
TMP_SCRIPT="/tmp/fury-fhdq.sh"

# Check if Fury-FHD skin already exists
if [ -d "$SKIN_DIR" ]; then
    echo ""
else

print_message "> Downloading and installing a new skin please wait..."
    sleep 2

# Download the script if the skin does not exist
wget -q --no-check-certificate "https://gitlab.com/eliesat/skins/-/raw/main/all/fury-fhd/fury-fhdq.sh" -O "$TMP_SCRIPT"

# Optional: Review the script before running
# less "$TMP_SCRIPT"

# Make it executable
chmod +x "$TMP_SCRIPT"

# Execute the script safely
/bin/sh "$TMP_SCRIPT"

# Clean up temporary script
rm -f "$TMP_SCRIPT"
fi
# Set primary skin
skin="config.skin.primary_skin=Fury-FHD/skin.xml"

# Remove any previous primary_skin lines
sed -i '/^config\.skin\.primary_skin=/d' /etc/enigma2/settings

# Add the new skin setting
echo "$skin" >> /etc/enigma2/settings

fi

# ------------------------------------------------
# CASE 4: Everything else → OK
# ------------------------------------------------

# Remove unnecessary files and folders
###########################################
[ -d "/CONTROL" ] && rm -r /CONTROL >/dev/null 2>&1
rm -rf /control /postinst /preinst /prerm /postrm /tmp/*.ipk /tmp/*.tar.gz >/dev/null 2>&1

# Download and install ElieSatPanel
###########################################
print_message "> Downloading and installing eliesatpanel ..."
wget -qO $package --no-check-certificate $url
tar -xzf $package -C /tmp
extract=$?
rm -rf $package >/dev/null 2>&1

if [ $extract -eq 0 ]; then
    rm -rf /usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid >/dev/null 2>&1
    mkdir -p /usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid
    mv /tmp/eliesatpanelgrid-main/* /usr/lib/enigma2/python/Plugins/Extensions/ElieSatPanelGrid/ >/dev/null 2>&1
    rm -rf /tmp/eliesatpanelgrid-main >/dev/null 2>&1
fi

# Download and install scripts
###########################################
if [ ! -f /usr/script/Eliesat-Eliesatpanel.sh ] ; then
    plugin=scripts
    version='scripts'
    url=https://github.com/eliesat/scripts/archive/main.tar.gz
    package=/tmp/$plugin.tar.gz
    rm -rf $package >/dev/null 2>&1

    wget -qO $package --no-check-certificate $url
    tar -xzf $package -C /tmp
    extract=$?
    rm -rf $package >/dev/null 2>&1

    if [ $extract -eq 0 ]; then
        mkdir -p /usr/script >/dev/null 2>&1
        cp -r /tmp/scripts-main/usr/* /usr/ >/dev/null 2>&1
        rm -rf /tmp/scripts-main >/dev/null 2>&1

        print_message "> Eliesat scripts are installed successfully and up to date ..."
        sleep 3
    fi
fi

print_message "> End of process ..."
sleep 3
echo
print_message "> Please Wait, Enigma2 restarting ..."
echo "-----------------------------------------------------------"
sleep 3

# Restart Enigma2 service
############################################
if [ "$OSTYPE" == "DreamOS" ]; then
    sleep 2
    systemctl restart enigma2
else
    sleep 2
    killall -9 enigma2
fi
