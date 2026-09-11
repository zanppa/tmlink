# TMLink client
A very simple test client for TMLink.

After the gadget is connected (I've used Raspberry PI Zero W) as ethernet gadget, 
or an actual Mirrorlink compatible device (Sony Xperia Z2), launch
```
sudo sh usb0_interface.sh
```
to configure the local usb0 interface up and run dhclient on it. Note: at least on 
Devuan Excalibur the usb connection, after launching mirrorlink, automatically 
launches DHCP client on it so this step is not needed!

After that, launch
```
python3 Client.py
```
which searches all interfaces for TMLink servers. The interactive interface
supports arrow-key navigation, Enter to select, Escape or `q` to go back, and
scrolling through long server and application lists.

This is very very preliminary for testing purposes only.

Tested on Devuan Excalibur.

## Python API

`Client.py` exposes a `Server` class for one discovered TMLink server. Its
`applications` collection contains `Application` objects created from the
server's application list. VNC and RTP applications use the specialized
`VNCApplication` and `RTPApplication` subclasses; unsupported protocols use
`GenericApplication`.

```python
from Client import Server

server = Server.discover(timeout=5)[0]
application = server.get_application("0x00000001")
application.launch()
print(application.status())
application.stop()
```

## RTPClient

The RTP client launcher can use either GST python bindings from `python3-gi` package
or alternatively if that fails, it tries to launch `gst-launcher-1.0` which is 
intended for debuging only. To use the former method you may need to install that 
package and create the Python venv with `python -m venv --system-site-packages venv`. 
This makes the system installed gi bindings visible in the venv.

Note that `gst-launcher-1.0` version seems to launch/fork background, so it will not 
close cleanly when the client is stopped but must be terminated separately.

## License
Copyright (C) 2019, 2026 Lauri Peltonen

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
