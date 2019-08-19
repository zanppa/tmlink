#!/bin/sh

ifconfig usb0 up
ifconfig usb0 192.168.10.1 netmask 255.255.255.0
systemctl restart isc-dhcp-server
