#!/bin/sh
# This script launches the TM-Link servers on the usb0 interface
# the usb0 IP address is configured to be static 192.168.10.1

python3 ApplicationServer.py --interface=192.168.10.1 --kill &
python upnp/UPnPServer.py --interface=192.168.10.1
