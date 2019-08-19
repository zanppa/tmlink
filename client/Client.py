#!/bin/env python3
# TM-Link example client
# Very basic just to see if things work

import sys
import upnpclient
import xml.etree.ElementTree as ET

# Parsing the response url
from urllib.parse import urlparse

# Launching clients
import subprocess



timeout = 5
print('Searching devices for {} seconds...'.format(timeout))
devices = upnpclient.discover(timeout)
print('Search done')

tmlinkServer = []
for device in devices:
	if device.device_type == 'urn:schemas-upnp-org:device:TmServerDevice:1':
		tmlinkServer.append(device)
		print('Found server at {}'.format(device.location))


print()
selectedServer = None
if len(tmlinkServer) == 0:
	print('No servers found')
	sys.exit(0)

elif len(tmlinkServer) == 1:
	selectedServer = 0
	print('Using server {}'.format(tmlinkServer[0].location))

else:
	print('Select server to use')
	for n, server in enumerate(tmlinkServer):
		print('{:02d}: {}'.format(n, server))

	while selectedServer == None:
		try:
			server_input = int(input('>'))
		except:
			print('Erroneous selection, give number')
			continue

		if server_input < 0 or server_input >= len(tmlinkServer):
			print('Give number between 0 and {}'.format(len(tmlinkServer)))
			continue

		selectedServer = server_input


server = tmlinkServer[selectedServer]

# Sanity checks for the server
if not 'TmApplicationServer1' in server.service_map:
	print('Application server not found')
	sys.exit(-1)

hasError = False
if not 'GetApplicationList' in server.service_map['TmApplicationServer1'].action_map:
	print('GetApplicationList not implemented in server')
	hasError = True
if not 'LaunchApplication' in server.service_map['TmApplicationServer1'].action_map:
	print('LaunchApplication not implemented in server')
	hasError = True
if not 'TerminateApplication' in server.service_map['TmApplicationServer1'].action_map:
	print('TerminateApplication not implemented in server')
	hasError = True
if not 'GetApplicationStatus' in server.service_map['TmApplicationServer1'].action_map:
	print('GetApplicationStatus not implemented in server')
	hasError = True

if hasError:
	print('Errors in server implementation')
	sys.exit(-1)

# Query application list
appListXML = server.service_map['TmApplicationServer1'].GetApplicationList(AppListingFilter='', ProfileID=0)['AppListing']
appList = ET.fromstring(appListXML)

# Parse list of applications from XML
applications = []
apps = appList.findall('app')
for app in apps:
	newApp = {}
	newApp['id'] = app.find('appID').text
	newApp['name'] = app.find('name').text
	newApp['providerName'] = app.find('providerName')
	newApp['description'] = app.find('description')
	newApp['protocol'] = app.find('./remotingInfo/protocolID').text

	if newApp['protocol'] == 'RTP':
		newApp['format'] = app.find('./remotingInfo/format').text
		dir = app.find('./remotingInfo/direction')
		if dir:
			newApp['direction'] = dir.text

	applications.append(newApp)


vnc_clients = {}
rtp_clients = {}

while True:
	# Print applications and select action
	print('Applications:')
	for n, app in enumerate(applications):
		print('{:02d} : {}'.format(n, app['name']))

	print()
	print('Select action')
	print('     0 : Launch application')
	print('     1 : Terminate application')
	print('     2 : Query application status')
	print(' other : Quit')
	try:
		action = int(input('>'))
	except:
		break

	if action < 0 or action > 2:
		break


	print('Application ID')
	ID = int(input('>'))
	if ID < 0 or ID >= len(applications):
		print('ERROR: Application ID out of range')
		continue

	if action == 0:
		# Launch application
		ret =server.service_map['TmApplicationServer1'].LaunchApplication(AppID='{}'.format(applications[ID]['id']), ProfileID=0)
		uri = ret['AppURI']
		uri_part = urlparse(uri)

		# Check the protocol
		if uri_part.scheme.lower() == 'vnc':
			if (not uri in vnc_clients) or (vnc_clients[uri].poll() is not None):
				# TODO: Bring the client forwards when the viewer already exists
				# New URI or the existing client has terminated
				cmd =['vncviewer', '{}::{}'.format(uri_part.hostname, uri_part.port)]
				print('Launching: {}'.format(' '.join(x for x in cmd)))
				proc = subprocess.Popen(cmd)
				vnc_clients[uri] = proc

		elif uri_part.scheme.lower() == 'rtp':
			if (not uri in rtp_clients) or rtp_clients[uri].poll() is None:
				# New URI or the existing client has terminated
				cmd = ['python3', 'RTPClient.py', '{}'.format(uri_part.hostname), '{}'.format(uri_part.port)]
				print('Launching: {}'.format(' '.join(x for x in cmd)))
				proc = subprocess.Popen(cmd)
				rtp_clients[uri] = proc

		else:
			print('Unknown protocol in URI: {}'.format(uri))

	elif action == 1:
		# Terminate application
		print(server.service_map['TmApplicationServer1'].TerminateApplication(AppID='{}'.format(applications[ID]['id']), ProfileID=0))

	elif action == 2:
		print('Not implemented')

	else:
		print('ERROR: Unknown command. Quit.')
		break

	print
