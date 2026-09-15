# TMLink server
This is a prototype implmentation of the TMLink server.

I've tested this on Raspberry PI Zero W. Some things are written 
with python3 while some others still require python 2.7...

## Preparations
First, you need to enable the gadget mode on the PI. Add `dtoverlay=dwc2` to `/boot/config.txt`.

You may need to compile a custom kernel to use the NCM gadget. If you do not wish to do that, 
you can also change things to use the RNDIS gadget.

Install and configure a DHCP server. See `configs/dhcp/` for more info.

Optional: start the standalone Python HTTP server if you want to serve icons
or other static content. Put files in `http/` and run `sh launch_http.sh`.
See `configs/http/` for configuration details. The old `webfsd` configuration
is retained there as an alternative, but is no longer the recommended setup.

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

## Configured applications

The current built-in `DefaultApplicationList` remains the default when no
configuration is supplied. To create applications from a TOML file instead,
copy `config.example.toml`, edit it, and start:

```sh
python3 ApplicationServer.py --config config.toml --interface 192.168.10.1 --kill
```

Configured mode creates VNC and RTP output-server targets by default. Set a
target's `enabled = false` to disable it. Additional VNC or RTP targets can be
defined under `[targets.<name>]`. Applications select a target and provide
either a `command` array or an `executable` plus `arguments`.

Command and environment values support placeholders such as `{host}`,
`{vnc_uri}`, `{rtp_uri}`, `{port}`, `{display_number}`, `{config_dir}`,
`{sink_name}`, and `{audio_source}`. Target-specific values such as
`{rtp_sink_name}` are also available. This allows media players to use the
configured PulseAudio/PipeWire sink or RTP input device without hard-coded
values.

Python 3.11 or newer provides TOML parsing through the standard library. On
older Python versions, install the compatible `tomli` package.

Then, you can just launch the servers: `sh launch_servers.sh`. The
ApplicationServer goes to background and the UPnP server stays on foreground.
The HTTP server, when needed, is started independently with
`sh launch_http.sh`.

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
