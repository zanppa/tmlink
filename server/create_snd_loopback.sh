#!/bin/sh
# Create the ALSA loopback device to be used with RTP server
# This script must be run as root

modprobe snd-aloop
