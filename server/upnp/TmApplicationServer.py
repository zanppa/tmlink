# TmApplicationServer - Handles launching and listing applications
# and so forth
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




# TODO:
#	[ ] Implement UPnP action handlers
#	[ ] Implement state variables
#	[ ] Implement interface to register applications
#	[ ] Implement interface to launch / terminate applications

#from twisted.internet import reactor
#from txdbus import error, client

import dbus

from pyupnp.logr import Logr

from pyupnp.event import EventProperty
from pyupnp.services import Service, register_action,\
    ServiceActionArgument, ServiceStateVariable
from pyupnp.upnp import upnpError

class TmApplicationServer(Service):
    version = (1, 0)
    serviceType = "urn:schemas-upnp-org:service:TmApplicationServer:1"
    serviceId = "urn:upnp-org:serviceId:TmApplicationServer"

    actions = {
        'GetApplicationList': [
            ServiceActionArgument('AppListingFilter',       'in',   'A_ARG_TYPE_String'),
            ServiceActionArgument('ProfileID',              'in',   'A_ARG_TYPE_ProfileID'),
            ServiceActionArgument('AppListing',             'out',  'A_ARG_TYPE_AppList'),
        ],
        'LaunchApplication': [
            ServiceActionArgument('AppID',                  'in',   'A_ARG_TYPE_AppID'),
            ServiceActionArgument('ProfileID',              'in',   'A_ARG_TYPE_ProfileID'),
            ServiceActionArgument('AppURI',                 'out',  'A_ARG_TYPE_URI'),
        ],
        'TerminateApplication': [
            ServiceActionArgument('AppID',                  'in',   'A_ARG_TYPE_AppID'),
            ServiceActionArgument('ProfileID',              'in',   'A_ARG_TYPE_ProfileID'),
            ServiceActionArgument('TerminationResult',      'out',  'A_ARG_TYPE_Bool'),
        ],
        'GetApplicationStatus': [
            ServiceActionArgument('AppID',                  'in',   'A_ARG_TYPE_AppID'),
            ServiceActionArgument('AppStatus',              'out',  'A_ARG_TYPE_AppStatus'),
        ],
        'GetApplicationCertificateInfo': [
            ServiceActionArgument('AppID',                  'in',   'A_ARG_TYPE_AppID'),
            ServiceActionArgument('AppCertification',       'out',  'A_ARG_TYPE_AppCertificateInfo'),
        ],
        'GetCertifiedApplicationsList': [
            ServiceActionArgument('AppCertFilter',          'in',   'A_ARG_TYPE_String'),
            ServiceActionArgument('ProfileID',              'in',   'A_ARG_TYPE_ProfileID'),
            ServiceActionArgument('CertifiedAppList',       'out',  'A_ARG_TYPE_String'),
        ],
        'GetAppCertificationStatus': [
            ServiceActionArgument('AppID',                  'in',   'A_ARG_TYPE_AppID'),
            ServiceActionArgument('AppCertFilter',          'in',   'A_ARG_TYPE_String'),
            ServiceActionArgument('ProfileID',              'in',   'A_ARG_TYPE_ProfileID'),
            ServiceActionArgument('AppCertified',           'out',  'A_ARG_TYPE_Bool'),
        ],
        'SetAllowedApplicationsList': [
            ServiceActionArgument('AllowedAppListNonRestricted', 'in',   'A_ARG_TYPE_String'),
            ServiceActionArgument('AllowedAppListRestricted', 'in',   'A_ARG_TYPE_String'),
            ServiceActionArgument('ProfileID',              'in',   'A_ARG_TYPE_ProfileID'),
        ],
    }

    stateVariables = [
        # Variables
        ServiceStateVariable('AppStatusUpdate',                 'string',
                             sendEvents=True),
        ServiceStateVariable('AppListUpdate',                   'string',
                             sendEvents=True),

        # Arguments
        ServiceStateVariable('A_ARG_TYPE_AppStatus',            'string'),
        ServiceStateVariable('A_ARG_TYPE_AppList',              'string'),
        ServiceStateVariable('A_ARG_TYPE_AppID',                'string'),
        ServiceStateVariable('A_ARG_TYPE_ProfileID',            'ui4'),
        ServiceStateVariable('A_ARG_TYPE_URI',                  'URI'),
        ServiceStateVariable('A_ARG_TYPE_String',               'string'),
        ServiceStateVariable('A_ARG_TYPE_Bool',                 'string', [
            'false',
            'true'
        ]),
        ServiceStateVariable('A_ARG_TYPE_Int',                  'ui4'),
        ServiceStateVariable('A_ARG_TYPE_AppCertificateInfo',   'string'),
    ]

    # Events that can be registered to
    app_status_update = EventProperty('AppStatusUpdate')
    app_list_update = EventProperty('AppListUpdate')
    # TODO: How to handle the changes...?


    def __init__(self):
        Service.__init__(self)

        # Initialize D-BUS connection to the application server
        self.dbus = dbus.SessionBus()
        self.session = self.dbus.get_object('org.tmlink', '/org/tmlink')
        self.iface = dbus.Interface(self.session, 'org.tmlink.ApplicationServer')

    @register_action('GetApplicationList')
    def getApplicationList(self, appListingFilter, profileID):
        return {'AppListing': self.iface.ApplicationList()}

    @register_action('LaunchApplication')
    def launchApplication(self, appID, profileID):
        return {'AppURI': self.iface.LaunchApplication(appID)}

    @register_action('TerminateApplication')
    def terminateApplication(self, appID, profileID):
        return {'TerminationResult': self.iface.TerminateApplication(appID)}

    @register_action('GetApplicationStatus')
    def getApplicationStatus(self, appID):
        return {'AppStatus': self.iface.GetApplicationStatus(appID)}

    @register_action('GetApplicationCertificateInfo')
    def getApplicationCertificateInfo(self, appID):
        raise upnpError(815, 'Device Locked') # TODO: Implement

    @register_action('GetCertifiedApplicationsList')
    def getCertifiedApplicationsList(self, appCertFilter, profileID):
        raise upnpError(815, 'Device Locked') # TODO: Implement

    @register_action('GetAppCertificationStatus')
    def getAppCertificationStatus(self, appID, appCertFilter, profileID):
        raise upnpError(815, 'Device Locked') # TODO: Implement

    @register_action('SetAllowedApplicationsList')
    def setAllowedApplicationsList(self, allowedAppListNonRestricted, allowedAppListRestricted, profileID):
        raise upnpError(815, 'Device Locked') # TODO: Implement



    ## Custom handling code here, i.e. to register applications and so forth
