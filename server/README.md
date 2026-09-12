# TMLink server
This is a prototype implmentation of the TMLink server.

I've tested this on Raspberry PI Zero W. Some things are written 
with python3 while some others still require python 2.7...

## Preparations
First, you need to enable the gadget mode on the PI. Add `dtoverlay=dwc2` to `/boot/config.txt`.

You may need to compile a custom kernel to use the NCM gadget. If you do not wish to do that, 
you can also change things to use the RNDIS gadget.

Install and configure a DHCP server. See `configs/dhcp/` for more info.

Optional: Install and configure http server if you want to serve icons (which may be supported by 
some UPnP implementations, I don't use those yet). See `configs/http/` for more info.

## Running
First you need to configure the ethernet gadget: `sudo sh create_gadget.sh´.

The RTP server uses GStreamer Python bindings by default. Its default source is the monitor of the
system's default PulseAudio/PipeWire sink, so all audio sent to the normal speakers is transmitted.
Start the server normally with `sh launch_servers.sh`. If the bindings are unavailable, the optional
debug fallback can be enabled with:
`sh launch_servers.sh` after adding `--gst-launch-fallback` to its `ApplicationServer.py` command.

To transmit only audio explicitly routed to a separate sink, start the application server with
`--audio-source=sink`. This creates a sink named `tmlink_rtp_sink`; select it as the output device
in an application, or route an existing stream to it with tools such as `pavucontrol` or
`pactl move-sink-input`. Only audio sent to that sink is transmitted. Note that to create the 
sink, `pactl` is used which means you must have it installed.

The legacy ALSA loopback source remains available with `--audio-source=alsa`. In that mode,
`--device` selects the capture device (the old default is `hw:1,1,0`), and the loopback can be
created with `sudo sh create_snd_loopback.sh`.

Then, you can just launch the servers: `sh launch_servers.sh`. The ApplicationServer goes to background 
and the UPnP server stays on foreground.

Now this should work with the client after plugging the gadget in.

## Stopping
The UPnP server can be stopped by pressing `CTRL+D` or writing `stop` to the prompt. The ApplicationServer 
must be killed separately with `kill`.

## License
Copyright (C) 2019 Lauri Peltonen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.


## Disclaimer
This program is for INFORMATION PURPOSES ONLY. You use this at your own risk, author takes 
no responsibility for any loss or damage caused by using this program or any information 
presented.
