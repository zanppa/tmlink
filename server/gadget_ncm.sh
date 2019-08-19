#!/bin/sh
# Greate a NCM ethernet gadget
# This script needs to be run as root
# Original script from https://www.isticktoit.net/?p=1383

# Create the gadget
cd /sys/kernel/config/usb_gadget/
mkdir -p isticktoit
cd isticktoit
echo 0x1d6b > idVendor # Linux Foundation
echo 0x0104 > idProduct # Multifunction Composite Gadget
echo 0x0100 > bcdDevice # v1.0.0
echo 0x0200 > bcdUSB # USB2

# Add descriptions
mkdir -p strings/0x409
echo "fedcba9876543210" > strings/0x409/serialnumber
echo "Lauri Peltonen" > strings/0x409/manufacturer
echo "USB NCM ethernet Gadget" > strings/0x409/product

# Add configuration
mkdir -p configs/c.1/strings/0x409
echo "Config 1: NCM network" > configs/c.1/strings/0x409/configuration

# Options
echo 250 > configs/c.1/MaxPower

# Add functions
mkdir -p functions/ncm.usb0

# Add MAC addresses if required
# If this is commented out, random MAC address will be used
# first byte of address must be even
HOST="48:6f:73:74:50:43" # "HostPC"	# Host address
SELF="42:61:64:55:53:42" # "BadUSB"	# Device (gadget) address
#echo $HOST > functions/ncm.usb0/host_addr
#echo $SELF > functions/ncm.usb0/dev_addr

# Add function to the config
ln -s functions/ncm.usb0 configs/c.1/

# End functions

# Enable gadget on first USB Device Controller
ls /sys/class/udc | head -1 > UDC
