# TmClientProfile - Client profile
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

from pyupnp.event import EventProperty
from pyupnp.services import Service, register_action,\
    ServiceActionArgument, ServiceStateVariable


class TmClientProfile(Service):
    version = (1, 0)
    serviceType = "urn:schemas-upnp-org:service:TmClientProfile:1"
    serviceId = "urn:upnp-org:serviceId:TmClientProfile"

    actions = {
        'GetMaxNumProfiles': [
            ServiceActionArgument('NumProfilesAllowed',                 'out',  'MaxNumProfiles'),
        ],
        'SetClientProfile': [
            ServiceActionArgument('ProfileID',              'in',   'A_ARG_TYPE_ProfileID'),
            ServiceActionArgument('ClientProfile',          'in',   'A_ARG_TYPE_ClientProfile'),
            ServiceActionArgument('ResultProfile',          'out',  'A_ARG_TYPE_ClientProfile'),
        ],
        'GetClientProfile': [
            ServiceActionArgument('ProfileID',              'in',   'A_ARG_TYPE_ProfileID'),
            ServiceActionArgument('ClientProfile',          'out',  'A_ARG_TYPE_ClientProfile'),
        ],
    }
    stateVariables = [
        # Variables
        ServiceStateVariable('UnusedProfileIDs',              'string',
                             sendEvents=True),
        # Arguments
        ServiceStateVariable('A_ARG_TYPE_ClientProfile',        'string'),
        ServiceStateVariable('A_ARG_TYPE_ProfileID',            'ui4'),
        ServiceStateVariable('A_ARG_TYPE_String',               'string'),
        ServiceStateVariable('A_ARG_TYPE_INT',                  'integer'),
        ServiceStateVariable('A_ARG_TYPE_Bool',                 'string', [
            'false',
            'true'
        ]),
        ServiceStateVariable('MaxNumProfiles',   'ui2'),
    ]

    unused_profile_ids = EventProperty('UnusedProfileIDs')


    # Internal variables
    maxNumProfiles = 1

    @register_action('GetMaxNumProfiles')
    def getMaxNumProfiles(self):
        return self.maxNumProfiles

    @register_action('SetClientProfile')
    def setClientProfile(self, profileID, clientProfile):
	# TODO: Update the profile XML with the provided profile, return the new union
        if profileID < 0 or profileID >= self.maxNumProfiles:
            raise upnpError(830, 'Invalid Profile ID')
        # raise upnpError(825, 'Invalid Profile') # If profile did not match schema
        raise upnpError(701, 'Operation Rejected') # TODO: Change when function is implemented

    @register_action('GetClientProfile')
    def getClientProfile(self, profileID):
	# TODO: Return XML formatted profile
        if profileID < 0 or profileID >= self.maxNumProfiles:
            raise upnpError(830, 'Invalid Profile ID')
        raise upnpError(701, 'Operation Rejected') # TODO: Change when function is implemented


    # TODO: External handling (D-BUS?) for client connections and
    # assigning profile IDs etc
