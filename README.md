# TMLink
TMLink is a set of tools (clients, servers) to allow zero configuration remote access to
a gadget from a computer. It is currently only a prototype/proof-of-concept and as such needs lots of 
manual setup to get to work properly.

Raspberry PI Zero W has been used as the gadget, and laptop running Devuan Linux as the host computer.

TMLink builts upon known technologies, for example:
 * Gadget is connected to the host as a virtual network card (e.g. CDC/NCM or RNDIS)
 * DHCP is used for automatic configuration of the network interface
 * SSDP and UPnP are used for automatic service discovery and description
 * VNC is used for video transfer, allowing usage of any normal applications

TMLink is heavily inspired by Nokia's Terminal Mode and Car Connectivity Consortium's MirrorLink. 
Some parts are implemented so that they may closely resemble the [ETSI standards TS 103 544](https://www.etsi.org/standards-search#page=1&search=103%20544&title=0&etsiNumber=1&content=0&version=0&onApproval=1&published=1&historical=1&startDate=1988-01-15&endDate=2017-10-11&harmonized=0&keyword=&TB=&stdType=&frequency=&mandate=&collection=&sort=1). 

## Theory of operation
Note that not everything described here is currently implemented (properly).

The gadget to be remote-operated runs as a server and the host computer is the client.

### Connection
When the gadget is connected to a host (in USB device mode, or with Bluetooth or WLAN or similar), 
it identifies as a network interface. The gadget configures its own network interface and launches a DHCP server.

The host (client) detects the new network interface and configures it with a DHCP client.

### Service discovery
The gadget launches SSDP and UPnP servers, both listening on the new network interface.

The host runs a SSDP discovery (using multicast to 239.255.255.250:1900), which reaches the gadget which replies with the 
UPnP server address. The host then launches UPnP client, which requests UPnP descriptor from the gadget. 
This descriptor describes all actions that can be performed on the gadget (e.g. launch applications).

### Commanding the gadget
The UPnP descriptor provides list of actions that can be invoked with UPnP (HTTP/SOAP calls). These 
actions include launching applications or querying status reports. Using these calls the host can 
run a pre-defined set of actions on the gadget.

### Sharing screen
The host can request list of applications available on the gadget. It can also request the status of 
each application. If there is a VNC server already running on the gadget, the status report lists the 
address of it. If it is not running, the client can launch a suitable application on the server, return 
value of the launch call is the VNC server address.

The client can then connect to this server with the provided address. At the moment the VNC server 
requires no authorisation, but it can be implemented if necessary.

### Audio transfer
Audio can be transferred using RTP. UPnP actions can be used to request the audio input/output stream 
addresses.

As RTP uses UDP, it is necessary to somehow establish the connection. This is done so that when RTP 
stream is launched, the server listens on a port and provides the client the address and port via UPnP. 
The client then sends 1 byte UDP packet to the given address and port. Server uses this packet to 
determine the client address and port, and starts the RTP stream to that address.

The client may re-send the 1 byte packets at some intervals if it does not receive the stream.

Audio is streamed in mode 99, 16 bit stereo, 48 kHz.

## A word of warning
As this is designed to be easy to use and to operate on local connection (e.g. USB) only, there is 
absolutely no built-in security. So please make sure that you do not bind any of these to external 
network interfaces, do not bridge the local connection to external networks and do not use this on
stock Raspbian with sudo requiring no password.

Also note that this is a proof-of-concept type idea, so it might not work properly, it may corrupt 
your files or do other nasty things. It works on my box, no other guarantees. For information purposes 
only. You have been warned.

## Installation
To be written. Go through all the directories and see their READMEs.

Some parts work with python 2.7 and some parts with python 3...

### Server requirements
* [My fork of pyUPnP](https://github.com/zanppa/PyUPnP) and its requirements
* DBUS and its python bindings
* python-gobject
* VNC server, I use [TigerVNC](https://tigervnc.org/)
* Gstreamer1.0, gstreamer1.0-tools, gstreamer1.0-plugins-base and gstreamer1.0-plugins-good


### Client requirements
* [UPnPClient](https://github.com/flyte/upnpclient)
* Gstreamer1.0, gstreamer1.0-tools, gstreamer1.0-plugins-base and gstreamer1.0-plugins-good
* VNC client, I use [TigerVNC](https://tigervnc.org/)


## Server status
### Connection
[x] USB gadget configuration (static or with ConfigFS)
[ ] Bluetooth PAN network interface (and pairing, connection)
[ ] WLAN access point

### Service discovery
[x] SSDP server
[x] UPnP server with service descriptors, actions
[x] Some actions can be invoked
[ ] All actions can be invoked
[ ] Errors are reported properly
[x] Can bind the server(s) to a selected interface
[ ] Support for multiple simultaneous connections (different interfaces)

### Commanding
[x] Applications can be listed
[x] Applications can be launched
[x] Applications can be terminated
[x] Application status can be queried
[ ] Application status is correct, updated automatically (e.g. if it terminated by itself)

### Screen sharing
[x] VNC server can be launched and terminated on selected (one) interface
[x] VNC server reports its address
[x] Applications can be launched on the VNC server

### RTP
[ ] RTP stream(s) can be started
[ ] Audio is routed to these streams automatically

### Other TODO items
[X] PyUPnP: Fork in github and commit changes there
[X] SSDP: Pass the interface IP where the UPnP server is listening instead of using default
[ ] UPnP: in upnp.py e.g. render_POST method(s), allow raising exception that will return an UPnP error instead
 * [X] Create upnpException that allows defining the error code and error description
 * [X] Catch it when calling the func(**kwargs)
 * [X] return 500 internal server error (request.setResponseCode(500)) and correct SOAP/XML response
[X] UPnP: Fix the method_POST so that buildSOAP is e.g. buildSOAP(method='%sResponse'%name, kw=result, namespace=self.service.serviceType)
 * That way the namespace will indicate correct service, which seems to be required by some implementations
[ ] Add a way to return errors through D-BUS, e.g. return tuple (errorCode, value)
[ ] Implement notifications (over D-BUS, over UPnP)

## Client status
### UPnP client
[X] Can search for device
[X] Can list applications
[X] Can launch applications
 * [X] Can launch VNC client for each individual VNC URI
 * [ ] Can launch RTP client for each RTP stream URI
[X] Can terminate applications

### RTP client
[X] Send one-byte packet to server
[X] Automatically identify stream type and select decoding parameters
[X] Read UDP RTP stream and play

### VNC client
[X] Uses standard client
[ ] Terminal Mode extension in VNC client (WIP in separate repository)

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

