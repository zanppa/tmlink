# Device - main device descripton
# Copyright (C) 2019 Lauri Peltonen

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#import logging
#from threading import Thread
#import time
#from twisted.internet import reactor
import xml.etree.ElementTree as et
from pyupnp.device import Device, DeviceIcon
from pyupnp.logr import Logr
from pyupnp.services import register_action
from pyupnp.services.connection_manager import ConnectionManagerService
from pyupnp.services.content_directory import ContentDirectoryService
from pyupnp.services.microsoft.media_receiver_registrar import MediaReceiverRegistrarService
#from ssdp import SSDP
#from pyupnp.upnp import UPnP
from pyupnp.util import make_element

from TmApplicationServer import TmApplicationServer
from TmNotificationServer import TmNotificationServer
from TmClientProfile import TmClientProfile

class TmServerDevice(Device):
    deviceType = 'urn:schemas-upnp-org:device:TmServerDevice:1'
    friendlyName = 'TmDevice-TestUnit'
    manufacturer = 'Zan'
    manufacturerURL = 'http://google.com'
    modelDecription = 'FirstModel'
    modelName = 'RaspiServer'
    #modelNumber = 1
    modelURL = 'http://google.com'
    serialNumber = '1234abcd'
    UPC = 'Universal Product Code'	# TODO: Add sensible one?


    def __init__(self, address):
        Device.__init__(self)
        #super(Device, self).__init__()

        self.uuid = '2fac1234-31f8-11b4-a222-08002b34c003'

        self.tmApplicationServer = TmApplicationServer()
	self.tmNotificationServer = TmNotificationServer()
	self.tmClientProfile = TmClientProfile()

        self.services = [
            self.tmApplicationServer,
	    self.tmNotificationServer,
	    self.tmClientProfile,
        ]

        self.icons = [
            DeviceIcon('image/png', 48, 48, 24,
                       'http://{}:8000/icon.png'.format(address))
        ]

        self.namespaces[''] = 'urn:schemas-upnp-org:device-1-0'

        #self.extras['X_Signature'] = 'TODO'      # TODO: Which version?
        #self.extras['X_presentations'] = 'TODO'  # Version 1.2 and forwards

        # Build version info
        linkVersion = et.Element('X_mirrorLinkVersion')
        major = make_element('majorVersion', '1')
        minor = make_element('minorVersion', '0')
        linkVersion.append(major)
        linkVersion.append(minor)

	# TODO: Signature

        # List additional elements
        self.extraElements = [linkVersion]


    def setBaseUrl(self, bind):
#        Logr.debug('Device location is {}'.format(self.location))
        self.extras['URLBase'] = self.getLocation(bind)

    def dump_device(self):
        """Dump the device XML tree. This adds required additional fields"""
        device = Device.dump_device(self)

        for element in self.extraElements:
            device.append(element)

        return device

