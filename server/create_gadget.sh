#!/bin/sh
# Create the USB gadget and configure the USB networks interface
# This creates NCM type network interface
# This script must be run as root

modprobe libcomposite
sh ./gadget_ncm.sh
sh usb0_interface.sh
