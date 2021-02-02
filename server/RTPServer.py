#!/bin/env python

# RTPServer - A tool to start RTP server after client
# sends a 1-byte message to the TRP port.

# Copyright (C) 2019 Lauri Peltonen

import argparse
import socket
import select

import subprocess

import sys


PAYLOADS = {
    99: 'audio/x-raw, layout=(string)interleaved, media=(string)audio, clock-rate=(int)48000, encoding-name=(string)L16, encoding-params=(string)2, channels=(int)2, payload=(int)99',
    }

RESAMPLE = {
    99: 'audio/x-raw, rate=48000',
    }

#RTP_COMMAND = 'gst-launch-1.0 -v alsasrc device=hw:1,1,0 ! decodebin ! audioresample ! \'audio/x-raw, rate=48000' ! audioconvert ! 'audio/x-raw, layout=(string)interleaved, media=(string)audio, clock-rate=(int)48000, encoding-name=(string)L16, encoding-params=(string)2, channels=(int)2, payload=(int)0\' ! rtpL16pay  ! udpsink host={} port={}'
# Client command: gst-launch-1.0 -v updsrc port={} caps=\"application/x-rtp, media=(string)audio, format=(string)S32LE, layout=(string)interleaved, clock-rate=(int)48000, channels=(int)2, payload=(int)0\" ! rtpL16depay ! playsink'

class RTPServer():
    """Server that handles launching the RTP stream on client address"""

    def __init__(self, interface, port=0, device='hw:1,1,0'):
        self.interface = interface
        self.port = port
        self.socket = None
        self.proc = None
        self.device = device

    def launch(self):
        """Launch the listening server, return the stream address"""

        # Open the port for listening for client
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.interface, self.port))
        self.socket.setblocking(0)
        self.sockName = self.socket.getsockname()
        self.address = self.sockName[0]
        self.port = self.sockName[1]

        self.clientAddress = None
        self.clientPort = None

        return 'rtp://{}:{}'.format(self.address, self.port)


    def run(self, uri, type=99, timeout=10, stream_port=0, verbose=False):
        """Wait for packet to indicate destination address and port and start stream"""

        if not type in RESAMPLE or not type in PAYLOADS:
            print('Unknown payload (stream) type: {}'.format(type))
            return -1

        print uri
        if self.socket and not self.clientAddress:
            readable, writable, exceptional = select.select([self.socket], [], [], timeout)

            if self.socket in readable:
                if verbose:
                    print 'Byte received from client'

                # Data received, read the byte and discard
                data, addr = self.socket.recvfrom(1)

                self.clientAddress = addr[0]
                self.clientPort = addr[1]
                print addr, self.clientAddress, self.clientPort

                # Close the socket
                self.socket.close()

                #RTP_COMMAND = 'gst-launch-1.0 -v alsasrc device=hw:1,1,0 ! decodebin ! audioresample ! \'audio/x-raw, rate=48000' ! audioconvert ! 'audio/x-raw, layout=(string)interleaved, media=(string)audio, clock-rate=(int)48000, encoding-name=(string)L16, encoding-params=(string)2, channels=(int)2, payload=(int)0\' ! rtpL16pay  ! udpsink host={} port={}'
                cmd = ['gst-launch-1.0']
                if verbose:
                    cmd.append('-v')
                cmd.extend(['alsasrc', 'device={}'.format(self.device), '!', 'decodebin', '!', 'audioresample', '!', RESAMPLE[type], '!', 'audioconvert', '!', PAYLOADS[type], '!', 'rtpL16pay', 'pt=99', '!', 'udpsink', 'host={}'.format(self.clientAddress), 'port={}'.format(self.clientPort)])
                if stream_port != 0:
                    cmd.append('bind-port={}'.format(stream_port))

                # Launch the streaming server
                # TODO: Should not use shell, instead use some smarter way to handle the arguments?
                # self.proc = subprocess.Popen(RTP_COMMAND.format(self.clientAddress, self.clientPort), preexec_fn=os.setsid, shell=True)
                #self.proc = subprocess.Popen(['gst-launch-1.0', '-v', 'filesrc', 'location=./test.mp3', '!', 'decodebin', '!', 'audioresample', '!', RESAMPLE[payloadType], '!', 'audioconvert', '!', PAYLOADS[payloadType], '!', 'rtpL16pay', 'pt={}'.format(payloadType), '!', 'udpsink', 'host={}'.format(self.clientAddress), 'port={}'.format(clientPort)])
                return subprocess.call(cmd)	# Blocking call

        print('Timeout waiting for connection')
        return -1



def main():
    supportedPayloads = PAYLOADS.keys()

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--interface', help='Interface (address) to use', default='192.168.10.1')
    parser.add_argument('-p', '--port', help='Port to listen on', default=5000, type=int)
    parser.add_argument('-P', '--stream-port', help='Port from which to stream out', default=0, type=int)
    parser.add_argument('-T', '--timeout', help='Timeout waiting for connection (s)', default=60, type=int)
    parser.add_argument('-d', '--device', help='ALSA sound device to use', default='hw:1,1,0')
    parser.add_argument('-t', '--type', help='Stream (RTP payload) type', default=99, type=int, choices=supportedPayloads)
    parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    args = parser.parse_args()

    interface = args.interface
    port = args.port
    stream_port = args.stream_port
    timeout=args.timeout
    device = args.device
    type=args.type
    verbose=args.verbose

    rtpServer = RTPServer(interface, port, device)
    uri = rtpServer.launch()
    rtpServer.run(uri, type, timeout, stream_port, verbose)


if __name__ == '__main__':
    main()


