#Server DHCP configuration

## Setup (Raspbian)
```
apt-get install isc-dhcp-server
```

## Configuration
Copy (merge) the `dhcpd.conf` to `/etc/dhcp/dhcpd.conf`.

The provided config file runs the dhcp server for the interface with 
address `192.168.10.1` which is the USB interface.

The clients get IP addresses in the range `192.168.10.10`...`192.168.10.127`.

At this point nameserver is not supported, but IP addresses must be used.

