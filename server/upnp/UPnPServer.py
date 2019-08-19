# UPnP server for TM-Link
# Copyright (C) 2019 Lauri Peltonen

import sys

import argparse

import logging
from threading import Thread
from twisted.internet import reactor
from twisted.logger import globalLogPublisher
from twisted.logger._levels import LogLevel

from pyupnp.ssdp import SSDP
from pyupnp.upnp import UPnP
from pyupnp.logr import Logr

from TmServerDevice import TmServerDevice

class CommandThread(Thread):
    def __init__(self, device, upnp, ssdp):
        """

        :type device: Device
        :type upnp: UPnP
        :type ssdp: SSDP
        """
        Thread.__init__(self)
        self.device = device
        self.upnp = upnp
        self.ssdp = ssdp

        self.running = True

    def run(self):
        while self.running:
            try:
                command = 'command_' + raw_input('')

                if hasattr(self, command):
                    getattr(self, command)()
            except EOFError:
                self.command_stop()

    def command_stop(self):
        # Send 'byebye' NOTIFY
        self.ssdp.clients.sendall_NOTIFY(None, 'ssdp:byebye', True)

        # Stop everything
        self.upnp.stop()
        self.ssdp.stop()
        reactor.stop()
        self.running = False


# Hack for exceptions, from https://stackoverflow.com/questions/9295359/stopping-twisted-from-swallowing-exceptions
def analyze(event):
    if event.get("log_level") == LogLevel.critical:
        print("Stopping for: ", event)
        reactor.stop()


class UPnPServer:
    def __init__(self, host):
        Logr.configure(logging.DEBUG)

        self.host = host

        self.device = TmServerDevice(host)

        self.upnp = UPnP(self.device)
        self.ssdp = SSDP(self.device, [host], host)


    def run(self):
        globalLogPublisher.addObserver(analyze)

        self.upnp.listen(interface=self.host)
        self.ssdp.listen()

        self.device.setBaseUrl(self.host)

        r = CommandThread(self.device, self.upnp, self.ssdp)
        r.start()

        reactor.run()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--interface', help='interface (address) to listen on', default='192.168.10.1')
    args = parser.parse_args()

    interface = args.interface

    print('Launching UPnP server. Write stop or press CTRL+D (EOF) to quit')
    upnpServer = UPnPServer(interface)
    upnpServer.run()


if __name__ == '__main__':
    main()

