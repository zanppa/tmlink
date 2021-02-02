#!/bin/sh
# Create the ALSA loopback device to be used with RTP server
# This script must be run as root

# It is assumed that the loop-back device will be card #1

modprobe snd-aloop
