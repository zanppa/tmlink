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
which searches all interfaces for TMLink servers, and if found lists them, 
and then allows launching applications etc. on the server.

This is very very preliminary for testing purposes only.

Tested on Devuan Excalibur.


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

