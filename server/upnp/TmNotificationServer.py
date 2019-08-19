# TmNotificationServer - Allows client to receive UPnP notifications
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
#	[x] Fix the descriptor
#	[ ] Implement the callbacks

from pyupnp.event import EventProperty
from pyupnp.services import Service, register_action,\
    ServiceActionArgument, ServiceStateVariable


class TmNotificationServer(Service):
    version = (1, 0)
    serviceType = "urn:schemas-upnp-org:service:TmNotificationServer:1"
    serviceId = "urn:upnp-org:serviceId:TmNotificationServer"

    actions = {
        'GetNotification': [
            ServiceActionArgument('ProfileID',                'in',  'A_ARG_TYPE_ProfileID'),
            ServiceActionArgument('NotiID',                   'in',  'A_ARG_TYPE_NotiID'),
            ServiceActionArgument('Notification',             'out', 'A_ARG_TYPE_Notification'),
        ],
        'GetSupportedApplications': [
            ServiceActionArgument('ProfileID',                'in',  'A_ARG_TYPE_ProfileID'),
            ServiceActionArgument('AppIDs',                   'out', 'A_ARG_TYPE_String'),
        ],
        'SetAllowedApplications': [
            ServiceActionArgument('ProfileID',                'in',  'A_ARG_TYPE_ProfileID'),
            ServiceActionArgument('AppIDs',                   'in',  'A_ARG_TYPE_String'),
        ],
        'InvokeNotiAction': [
            ServiceActionArgument('ProfileID',                'in',  'A_ARG_TYPE_ProfileID'),
            ServiceActionArgument('NotiID',                   'in',  'A_ARG_TYPE_NotiID'),
            ServiceActionArgument('ActionID',                 'in',  'A_ARG_TYPE_ActionID'),
        ],
    }
    stateVariables = [
        # Variables
        ServiceStateVariable('ActiveNotiEvent',                 'string',
                             sendEvents=True),
        ServiceStateVariable('NotiAppListUpdate',               'string',
                             sendEvents=True),

        # Arguments
        ServiceStateVariable('A_ARG_TYPE_Notification',         'string'),
        ServiceStateVariable('A_ARG_TYPE_AppID',                'string'),
        ServiceStateVariable('A_ARG_TYPE_ProfileID',            'ui4'),
        ServiceStateVariable('A_ARG_TYPE_ActionID',             'string'),
        ServiceStateVariable('A_ARG_TYPE_NotiID',               'string'),
        ServiceStateVariable('A_ARG_TYPE_String',               'string'),
        ServiceStateVariable('A_ARG_TYPE_URI',                  'URI'),
        ServiceStateVariable('A_ARG_TYPE_INT',                  'ui4'),
        ServiceStateVariable('A_ARG_TYPE_Bool',                 'string', [
            'false',
            'true'
        ]),
    ]

    active_noti_event = EventProperty('ActiveNotiEvent')
    noti_app_list_update = EventProperty('NotiAppListUpdate')

    @register_action('GetNotification')
    def getNotification(self, profileID, notiID):
        raise NotImplementedError()

    @register_action('GetSupportedApplications')
    def getSupportedApplications(self, profileID):
        raise NotImplementedError()

    @register_action('SetAllowedApplications')
    def setAllowedApplications(self, profileID, appIDs):
        raise NotImplementedError()

    @register_action('InvokeNotiAction')
    def setAllowedApplications(self, profileID, notiID, actionID):
        # actionID 0x00 shall clear any active notification
        raise NotImplementedError()
