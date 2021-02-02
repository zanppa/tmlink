#/usr/bin/env python

# Application - Class to handle applications
# Copyright (C) 2019 Lauri Peltonen


#import itertools  # To get unique ID
import argparse

# Process handling
import subprocess # To launch the apps
import os
import signal

# XML
import lxml.etree as ElementTree
from lxml.etree import Element, SubElement

# D-BUS for interprocess communication
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

# YAML for configuration files
#import yaml

# List of remoting protocols
ApplicationProtocols = [
    'VNC',    # VNC => Video
    'RTP',    # Real time protocol => Audio
    'BTA2DP', # Bluetooth advanced audio distribution profile
    'BTHFP',  # Bluetooth hands free profile
    'DAP',    # Device attestation protocol
    'CDB',    # Common data bus
    'WFD',    # Wi-Fi display
    'NONE']   # No remote-access protocol


# Protocol formats are selected for following protocols:
# VNC = Not used
# RTP = Comma separated list of RTP payloads, default 99
#       See e.g. https://en.wikipedia.org/wiki/RTP_audio_video_profile
#                https://www.iana.org/assignments/rtp-parameters/rtp-parameters.xhtml
# BTA2DP = Not used
# BTHFP = Not used
# DAP = 1.0
# CDB = 1.1
# WFD = Not used
# None = Not used



# Minimal required implementation
class Application:
    nextAppID = 1

    def __init__(self, host = None):
        self.appID = Application.nextAppID
        Application.nextAppID += 1

        self.autoLaunch = False	# True = Launch automatically on startup
        self.noTerminate = False # True = Do not allow terminate, just send to background
        self.noListing = False # True = Do not list this in the app listing (e.g. background servers)

        self.proc = None

        # XML Output string
        self.xmlTree = None
        self.xmlString = ''

        self.name = 'Test Application'

        self.host = host

        # Remoting info, i.e. protocols
        self.protocolID = 'VNC'
        self.format = None
        self.direction = None # in, out or both, None does not print this

        self.certificateURL = None

        # Application info
        self.hasAppInfo = True
        self.appCategory = '0x00000000'
        self.appTrustLevel = '0x0000'

        # If there is display
        self.hasDisplay = True
        self.displayCategory = '0x00000000'
        self.displayTrustLevel = '0x0000'

        # If this is audio app
        self.hasAudio = False
        self.audioType = 'application'
        self.audioCategory = '0x00000000'
        self.audioTrustLevel = '0x0000'

        self.resourceStatus = 'free' # free, busy or NA, is the app available. If None, not printed
        #self.signature = 'xx'       # Not implemented in 1.0

        self.uri = ''	# Uri to access the application

        self.status = 'Notrunning'  # Notrunning, Foreground, Background

	#self.createXML()


    def createXML(self):
        self.xmlTree = Element('app')
        SubElement(self.xmlTree, 'appID').text = '0x{:0X}'.format(self.appID)
        SubElement(self.xmlTree, 'name').text = self.name

        chRemoting = Element('remotingInfo')
        SubElement(chRemoting, 'protocolID').text = self.protocolID
        if self.format:
            SubElement(chRemoting, 'format').text = self.format
        if self.direction:
            SubElement(chRemoting, 'direction').text = self.direction
        self.xmlTree.append(chRemoting)

        if self.hasAppInfo:
            chAppInfo = Element('appInfo')
            SubElement(chAppInfo, 'appCategory').text = self.appCategory
            SubElement(chAppInfo, 'trustLevel').text = self.appTrustLevel
            self.xmlTree.append(chAppInfo)

        if self.hasDisplay:
            chDisplay = Element('displayInfo')
            SubElement(chDisplay, 'contentCategory').text = self.displayCategory
            SubElement(chDisplay, 'trustLevel').text = self.displayTrustLevel
            self.xmlTree.append(chDisplay)

        if self.hasAudio:
            chAudio = Element('audioInfo')
            SubElement(chAudio, 'audioType').text = self.audioType
            SubElement(chAudio, 'contentCategory').text = self.audioCategory
            self.xmlTree.append(chAudio)

        if self.resourceStatus:
            SubElement(self.xmlTree, 'resourceStatus').text = self.resourceStatus

#        self.xmlString = ElementTree.tostring(self.xmlTree, encoding='UTF-8', method='xml')

        return self.xmlTree

    def dump(self):
        return self.createXML()

    def dumps(self):
        self.xmlString = ElementTree.tostring(self.dump(), encoding='UTF-8', method='xml', xml_declaration=True)
        return self.xmlString

    def launch(self, command, environ=None):
        if self.proc:	# Already running
            self.foreground()
            return self.uri

        print('Launching: {}'.format(' '.join(x for x in command)))
        self.proc = subprocess.Popen(command, preexec_fn=os.setsid, env=environ)
        self.status = 'Foreground'
        return self.uri

    def terminate(self):
        if not self.proc or self.noTerminate:
            return False

        #self.proc.terminate()
        #self.proc.kill()

        # Kill the process group, i.e. also all children
        os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)

        self.proc = None
        self.status = 'Notrunning'
        return True

    def isRunning(self):
        if not self.proc:
            return False
        if self.proc.poll() == None:
            return True
        return False

    def foreground(self):
        # TODO: Use wmctrl or xdotool to bring the window to foreground (if PID is stored in data)
        # Program is now on foreground
        self.status = 'Foreground'

    def background(self):
        # TODO: Use wmctrl or xdotool to send the window to background (if PID is stored in data)
        self.status = 'Background'

    def getURI(self):
        return self.uri

    def getStatus(self):
        """Return application status in XML format"""
        self.xmlStatus = Element('appStatus')
        SubElement(self.xmlStatus, 'appID').text = '0x{:0X}'.format(self.appID)

        # TODO: Should be possible to run app multiple times under different profiles, show status of all
        stat = SubElement(self.xmlStatus, 'status')
        SubElement(stat, 'profileID').text = 0	# TODO: Correct profile ID
        SubElement(stat, 'statusType').text = self.status

        return self.xmlStatus


class VNCApplication(Application):
    vncScreen = 1

    def __init__(self, host):
        #super(VNCApplication, self).__init__(host)
        Application.__init__(self, host)

        self.protocolID = 'VNC'
        self.hasDisplay = True
        self.hasAudio = False
        self.hasAppInfo = True

        # Select next free screen number
        self.screenID = VNCApplication.vncScreen
        VNCApplication.vncScreen += 1

        # Select port
        self.port = 5900 + self.screenID

        self.uri = 'vnc://{}:{}'.format(self.host, self.port)

        self.proc = None

        #self.createXML()

    def launch(self):
        # TODO: without -interface the server listens on all interfaces
        # Add also the process to a process group, so we can terminate all the child processes
        # too, and the server closes cleanly
        return Application.launch(self, ['vncserver', '-SecurityTypes=None', '-geometry=800x600', '-interface={}'.format(self.host), '-localhost=0', '--I-KNOW-THIS-IS-INSECURE', '-rfbport={}'.format(self.port), '-fg', ':{}'.format(self.screenID)])



class RTPServerApplication(Application):
    def __init__(self, host):
        #super(RTPApplication, self).__init__()
        Application.__init__(self, host)

        self.port = 12345	# TODO: Change to correct one

        self.protocolID = 'RTP'
        self.format = '99'
        self.hasDisplay = False
        self.hasAudio = True
        self.audioType = 'application'
        self.hasAppInfo = True
        self.uri = 'rtp://{}:{}'.format(self.host, self.port)

        #self.createXML()

    def launch(self):
        return Application.launch(self, ['python', 'RTPServer.py', '--interface={}'.format(self.host), '--port={}'.format(self.port)])


class RTPClientApplication(Application):
    def __init__(self, host):
        #super(RTPApplication, self).__init__()
        Application.__init__(self, host)

        self.port = 12346	# TODO: Change to correct one

        self.protocolID = 'RTP'
        self.format = '99'
        self.hasDisplay = False
        self.hasAudio = True
        self.audioType = 'application'
        self.hasAppInfo = True
        self.uri = 'rtp://{}:{}'.format(self.host, self.port)

        self.stream_type = 'application/x-rtp, media=audio, format=S32LE, layout=interleaved, clock-rate=48000, channels=2, payload=99'

        #self.createXML()

    def launch(self):
        return Application.launch(self, ['gst-launch-1.0', 'udpsrc', 'port={}'.format(self.port), 'caps=\"{}\"'.format(self.stream_type), '!', 'rtpL16depay', '!', 'alsasink device=hw:1,1,1'])


class GenericApplication(Application):
    def __init__(self, command, uri, display=1):
        Application.__init__(self)

        self.hasDisplay = True
        self.hasAudio = False	# This does not provide audio stream

        self.command = command
        self.uri = uri
        self.display = display

    def launch(self):
        env = os.environ.copy()
        env['DISPLAY'] = ':{}'.format(self.display)  # Which display to use
        return Application.launch(self, self.command, env)


class ApplicationServer(dbus.service.Object):
    """Server that handles listing, launching, terminating etc. applications"""

    def __init__(self, host):
        self.busName = dbus.service.BusName('org.tmlink', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, self.busName, '/org/tmlink')

        self.apps = {}
        self.xmlTree = None
        self.xmlString = ''

        self.host = host


    def addApplication(self, app):
        #self.apps.append(app)
        appID = app.appID
        if not appID in self.apps:
            self.apps[appID] = app

            if app.autoLaunch:
                self.LaunchApplication('0x{:X}'.format(appID))

    def terminateAll(self):
        for appID in self.apps:
            self.apps[appID].terminate()


    def createXML(self):
        self.xmlTree = Element('appList')
        self.xmlTree.set('{http://www.w3.org/XML/1998/namespace}id', 'mlServerAppList')	# attribute becomes 'xml:id' as it should

        for id in self.apps:
            if self.apps[id].noListing == False:
                self.xmlTree.append(self.apps[id].dump())


    def dump(self):
        self.createXML()
        return self.xmlTree

    @dbus.service.method('org.tmlink.ApplicationServer', in_signature='b', out_signature='b')
    def KillServer(self, killApps):
        if killApps:
            self.terminateAll()
        glib.MainLoop.quit()
        return True


    @dbus.service.method('org.tmlink.ApplicationServer', in_signature='', out_signature='s')
    def ApplicationList(self):
        self.xmlString = ElementTree.tostring(self.dump(), encoding='UTF-8', method='xml', xml_declaration=True)
        return self.xmlString

    @dbus.service.method('org.tmlink.ApplicationServer', in_signature='s', out_signature='s')
    def LaunchApplication(self, appID):
        try:
            appID = int(appID, 16)
        except:
            # TODO: Throw or something to get server error?
            # 810 = Bad AppID
            return ''

        if appID in self.apps:
            if self.apps[appID].launch():
                self.ForegroundApplication(appID)	# Make it fg and others bg
                return self.apps[appID].uri
            else:
                return '' # Todo: throw or something for 813 = Launch Failed
        # TODO: Throw or something to get server error?
        # 810 = Bad AppID
        return ''

    @dbus.service.method('org.tmlink.ApplicationServer', in_signature='s', out_signature='b')
    def TerminateApplication(self, appID):
        appID = int(appID, 16)
        if appID in self.apps:
            if not self.apps[appID].noTerminate:
                return self.apps[appID].terminate()
            else:
                self.background(appID)
                return True

        return False

    @dbus.service.method('org.tmlink.ApplicationServer', in_signature='i', out_signature='b')
    def ForegroundApplication(self, appID):
        # Put one program on foreground and others on background
        if not appID in self.apps:
            return False

        ret = False
        for id in self.apps:
            if id == appID:
                ret = self.apps[id].foreground()
            else:
                self.apps[id].background()

        return ret

    @dbus.service.method('org.tmlink.ApplicationServer', in_signature='i', out_signature='b')
    def BackgroundApplication(self, appID):
        # Put one program on background
        if not appID in self.apps:
            return False

        # TODO: Rise some other app?

        return self.apps[appID].background()

    @dbus.service.method('org.tmlink.ApplicationServer', in_signature='s', out_signature='s')
    def GetApplicationStatus(self, appID):
        self.statusList = Element('appStatusList')

        if appID == '*':         # Wildcard, show status of all apps
            for id in self.apps:
                statusList.append(self.apps[id].getStatus())
        else: # Show status of one app only
            appID = int(appID, 16)
            if appID in self.apps:
                statusList.append(self.apps[appID].getStatus())

        return ElementTree.tostring(statusList, encoding='UTF-8', method='xml', xml_declaration=True)




class DefaultApplicationList():
    """Simple list of default applications to present"""

    def __init__(self, server, host_address):
        # Default VNC server
        self.VNCapp = VNCApplication(host_address)
        self.VNCapp.appCategory = '0xF0000001'	# Server functionality
        self.VNCapp.name = 'VNC'
        self.VNCapp.autoLaunch = True
        self.VNCapp.noTerminate = True
        self.VNCapp.noListing = True
        server.addApplication(self.VNCapp)

        # RTP server (audio out)
        self.RTPserver = RTPServerApplication(host_address)
        self.RTPserver.appCategory = '0xF0000001'	# Server functionality
        self.RTPserver.name = 'Audio out'
        self.RTPserver.audioType = 'all'
        self.RTPserver.direction = 'out'
        server.addApplication(self.RTPserver)

        # RTP sink (audio in)
        self.RTPclient = RTPClientApplication(host_address)
        self.RTPclient.appCategory = '0xF0000002'	# Client functionality
        self.RTPclient.name = 'Audio in'
        self.RTPclient.audioType = 'all'
        self.RTPclient.direction = 'in'
        server.addApplication(self.RTPclient)

        # Generic test apps
        self.genapp = GenericApplication(['gnome-text-editor'], self.VNCapp.uri, 1)
        self.genapp.name = 'Text editor'
        server.addApplication(self.genapp)

        self.genapp2 = GenericApplication(['rxvt'], self.VNCapp.uri, 1)
        self.genapp2.name = 'Terminal'
        server.addApplication(self.genapp2)

        self.genapp3 = GenericApplication(['sh', 'play_music.sh'], self.RTPserver.uri, 0)
        self.genapp3.name = 'Play music'
        server.addApplication(self.genapp3)




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--interface', help='interface (address) to listen on', default='192.168.10.1')
    parser.add_argument('-k', '--kill', help='Kill applications when application server quits', action='store_true')
    args = parser.parse_args()

    interface = args.interface
    kill = args.kill

    # This must be run before connecting to the bus (i.e. creating the server)
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    server = ApplicationServer(interface)
    appList = DefaultApplicationList(server, interface)

    # dbus_service = Session_DBus()

    try:
        GLib.MainLoop().run()
    except KeyboardInterrupt:
        print("\nThe MainLoop will close...")
        GLib.MainLoop().quit()

    if kill:
        server.terminateAll()


if __name__ == '__main__':
    main()
