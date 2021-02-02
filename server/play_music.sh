#!/bin/sh
# Play sample music using the ALSA loopback interface
# To be used with the RTP server
# Loops the song automatically

mpg321 ./samples/sample_music_44.1kHz.mp3 -a hw:1,0,0 -l 0
