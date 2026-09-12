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

    def __init__(self, interface, port=0, device='hw:1,1,0',
                 audio_source='system', sink_name='tmlink_rtp_sink',
                 gst_launch_fallback=False):
        self.interface = interface
        self.port = port
        self.socket = None
        self.proc = None
        self.device = device
        self.audio_source = audio_source
        self.sink_name = sink_name
        self.gst_launch_fallback = gst_launch_fallback

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
            print('Unknown payload (stream) type: {}'.format(type), file=sys.stderr)
            return -1

        if self.socket and not self.clientAddress:
            readable, writable, exceptional = select.select([self.socket], [], [], timeout)

            if self.socket in readable:
                if verbose:
                    print('Byte received from client')

                # Data received, read the byte and discard
                data, addr = self.socket.recvfrom(1)

                self.clientAddress = addr[0]
                self.clientPort = addr[1]
                if verbose:
                    print('Client connection from {} to {}:{}'.format(addr, self.clientAddress, self.clientPort))

                # Close the socket
                self.socket.close()

                return self._run_pipeline(type, stream_port, verbose)

        print('RTP server error! Timeout waiting for connection', file=sys.stderr)
        return -1

    def _source_pipeline(self):
        """Return the GStreamer source and an optional PulseAudio module id."""
        if self.audio_source == 'system':
            # @DEFAULT_MONITOR@ captures audio currently sent to the default sink.
            return 'pulsesrc device=@DEFAULT_MONITOR@', None

        if self.audio_source == 'sink':
            # For a new sink use pactl to create a null-sink that will be monitored
            result = subprocess.run(
                ['pactl', 'load-module', 'module-null-sink',
                 'sink_name={}'.format(self.sink_name),
                 'sink_properties=device.description={}'.format(self.sink_name)],
                check=True, stdout=subprocess.PIPE, universal_newlines=True)
            module_id = result.stdout.strip()
            return 'pulsesrc device={}.monitor'.format(self.sink_name), module_id

        if self.audio_source == 'alsa':
            return 'alsasrc device={}'.format(self.device), None

        raise ValueError('Unknown audio source: {}'.format(self.audio_source))

    def _run_pipeline(self, type, stream_port, verbose):
        """Run the RTP pipeline with Gst bindings, optionally using gst-launch."""
        source = None
        module_id = None
        try:
            source, module_id = self._source_pipeline()
            #pipeline = (
            #    '{} ! audioconvert ! audioresample ! {} ! {} ! '
            #    'rtpL16pay pt={} ! udpsink host={} port={}'
            #).format(source, RESAMPLE[type], PAYLOADS[type], type,
            #         self.clientAddress, self.clientPort)
            pipeline = (
                '{} ! audioresample ! {} ! audioconvert ! {} ! '
                'rtpL16pay pt={} ! udpsink host={} port={}'
            ).format(source, RESAMPLE[type], PAYLOADS[type], type,
                     self.clientAddress, self.clientPort)
            if stream_port:
                pipeline += ' bind-port={}'.format(stream_port)

            try:
                import gi
                gi.require_version('Gst', '1.0')
                from gi.repository import Gst
                Gst.init(None)

                gst_pipeline = Gst.parse_launch(pipeline)
                try:
                    gst_pipeline.set_state(Gst.State.PLAYING)
                    bus = gst_pipeline.get_bus()
                    while True:
                        message = bus.timed_pop_filtered(
                            Gst.SECOND,
                            Gst.MessageType.ERROR | Gst.MessageType.EOS)
                        if message:
                            if message.type == Gst.MessageType.ERROR:
                                error, debug = message.parse_error()
                                print('GStreamer pipeline error: {}'.format(error),
                                      file=sys.stderr)
                                if debug and verbose:
                                    print(debug, file=sys.stderr)
                                return -1
                            return 0
                finally:
                    gst_pipeline.set_state(Gst.State.NULL)
            except Exception as error:
                if not self.gst_launch_fallback:
                    raise
                print('Could not run GStreamer bindings: {}'.format(error),
                      file=sys.stderr)
                print('Trying gst-launch-1.0', file=sys.stderr)
                cmd = ['gst-launch-1.0']
                if verbose:
                    cmd.append('-v')
                cmd.extend(self._gst_launch_arguments(type, stream_port))
                return subprocess.call(cmd)
        finally:
            if module_id:
                subprocess.run(['pactl', 'unload-module', module_id],
                               check=False)

    def _gst_launch_arguments(self, type, stream_port):
        if self.audio_source == 'system':
            source = ['pulsesrc', 'device=@DEFAULT_MONITOR@']
        elif self.audio_source == 'sink':
            source = ['pulsesrc', 'device={}.monitor'.format(self.sink_name)]
        else:
            source = ['alsasrc', 'device={}'.format(self.device)]

        result = source + [
            '!', 'audioconvert', '!', 'audioresample', '!',
            RESAMPLE[type], '!', PAYLOADS[type], '!', 'rtpL16pay',
            'pt={}'.format(type), '!', 'udpsink',
            'host={}'.format(self.clientAddress),
            'port={}'.format(self.clientPort)]
        if stream_port:
            result.append('bind-port={}'.format(stream_port))
        return result


def main():
    supportedPayloads = PAYLOADS.keys()

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--interface', help='Interface (address) to use', default='192.168.10.1')
    parser.add_argument('-p', '--port', help='Port to listen on', default=5000, type=int)
    parser.add_argument('-P', '--stream-port', help='Port from which to stream out', default=0, type=int)
    parser.add_argument('-T', '--timeout', help='Timeout waiting for connection (s)', default=60, type=int)
    parser.add_argument('-d', '--device', help='ALSA sound device when --audio-source=alsa', default='hw:1,1,0')
    parser.add_argument('--audio-source', choices=('system', 'sink', 'alsa'),
                        default='system',
                        help='Audio source: default sink monitor, generated isolated sink, or ALSA device')
    parser.add_argument('--sink-name', default='tmlink_rtp_sink',
                        help='Name of the generated PulseAudio/PipeWire sink')
    parser.add_argument('--gst-launch-fallback', action='store_true',
                        help='Fall back to the gst-launch-1.0 debug tool if Gst bindings fail')
    parser.add_argument('-t', '--type', help='Stream (RTP payload) type', default=99, type=int, choices=supportedPayloads)
    parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    args = parser.parse_args()

    interface = args.interface
    port = args.port
    stream_port = args.stream_port
    timeout=args.timeout
    device = args.device
    audio_source = args.audio_source
    sink_name = args.sink_name
    type=args.type
    verbose=args.verbose

    rtpServer = RTPServer(interface, port, device, audio_source, sink_name,
                          args.gst_launch_fallback)
    uri = rtpServer.launch()
    rtpServer.run(uri, type, timeout, stream_port, verbose)


if __name__ == '__main__':
    main()
