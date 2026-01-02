#!/bin/sh
# Check and install packages
#######################################
packages="wget curl"

for package in $packages; do
    if ! opkg list-installed | grep -q "^$package"; then
        if [ -f /etc/apt/apt.conf ]; then
            apt-get update >/dev/null 2>&1
            apt install $package -y >/dev/null 2>&1
        else
            opkg update >/dev/null 2>&1
            opkg install $package >/dev/null 2>&1
        fi
    fi
done

# Check server URL connectivity and install eliesatpanel
#######################################
if wget -q --method=HEAD https://github.com/eliesat; then
    wget -q "https://www.dropbox.com/scl/fi/qkmk5xsxwpzdbnpon6hts/installer-grid.sh?rlkey=bylcyjwqvjrj8acrsku07orww&st=lf62m95a&dl=0" -O - | sh
else
    echo "> Check your internet connection and try again ..."
fi
