#!/bin/env python3

# RTPClient.py -- handles launching the RTP client
# Copyright (C) 2019 Lauri Peltonen

import argparse

import socket
import select
import time

import subprocess


# TODO: Command line parameters?
listenPort = 5000
listenInterface = '192.168.10.21'

# Send a single byte start packet to the host
def sendStartPacket(host, port, interface=None, local_port=0):
	if not interface:
		interface = '0.0.0.0'

	if not local_port:
		local_port = 0

	# Do an UDP "connect" to resolve the interface (and random port)
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind((interface, local_port))
		sock.connect((host, 1))
	except:
		print('Could not open socket or remote host unreachable on given (or any) interface')
		sock.close()
		return (None, None)

	interface = sock.getsockname()[0]
	port = sock.getsockname()[1]
	print(interface, port)

	# Send single null byte (byte value is not specified)
	sock.send(b'\00')

	sock.close()

	return (interface, port)


# Try to detect RTP payload type, return payload (int) or None on error
def detectPayloadType(interface, port, timeout=5, packets=3):
	# Create UDP socket
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind((interface, port))
		sock.settimeout(timeout)
	except:
		# TODO: Better error handler if port/interface error?
		print('Error opening socket')
		return None

	payload = None
	selectedPayload = None

	timeout += time.time()
	while True:
		recv = select.select([sock], [], [], 1)	# 1 sec timeout
		if recv:
			try:
				data, address = sock.recvfrom(1024)	# TODO: How many bytes??
			except socket.timeout:
				print('Receive timeout')
				return None

			# Figure out the RTP stream type
			# The payload (stream type) is the low 7 bits of 2nd byte
			oldPayload = payload
			payload = ord(data[1]) & 0x7F

			if payload != oldPayload:
				votes = 1	# Require X times the same value to be sure
			else:
				votes += 1

			if votes > packets:
				selectedPayload = payload

			if selectedPayload is not None:
				break

			if time.time() > timeout:
				break

			if sock:
				sock.close()

	return selectedPayload



stream_types = {
	# 16 bit, 48 kHz, mono
	98: 'application/x-rtp, media=audio, format=S16LE, clock-rate=48000, channels=1, payload=98',

	# 16 bit, 48 kHz, stereo
	99: 'application/x-rtp, media=audio, format=S32LE, layout=interleaved, clock-rate=48000, channels=2, payload=99',

	# 16 bit, 16 kHz, mono
	100: 'application/x-rtp, media=audio, format=S16LE, layout=interleaved, clock-rate=16000, channels=1, payload=100',
}


# Launch the RTP client. Blocks on success, returns client return code or None on error
def launchRTPClient(interface, port, stream_type, verbose=0):
	if not stream_type in stream_types:
		print('Unknown payload type: {}'.format(stream_type))
		return None

	# Launch gstreamer
	cmd = ['gst-launch-1.0']
	if verbose:
		cmd.append('-v')
	cmd.extend(['udpsrc', 'port={}'.format(listenPort), 'caps=\"{}\"'.format(stream_types[stream_type]), '!', 'rtpL16depay', '!', 'playsink'])

	print(' '.join(x for x in cmd))
	return subprocess.call(cmd)


def main():
	parser = argparse.ArgumentParser(description='RTP client launcher')
	parser.add_argument('host', help='Remote host address')
	parser.add_argument('port', help='Remote host port')
	parser.add_argument('-i', '--interface', type=str, help='Force network interface (IP) to use (default=auto)', default=None)
	parser.add_argument('-p', '--local_port', type=int, help='Force local port to use (default=random)', default=0)
	args = parser.parse_args()

	host = args.host
	port = args.port

	interface = args.interface
	local_port = args.local_port

	(interface, local_port) = sendStartPacket(host, port, interface, local_port)
	if not interface:
		return

	stream_type = detectPayloadType(interface, local_port)
	if not stream_type:
		print('Stream type was not detected, timeout')
	else:
		print('Payload type: {}'.format(stream_type))
		print('Launching RTP client')
		ret = launchRTPClient(interface, local_port, stream_type)
		print('RTP client returned {}'.format(ret))



if __name__ == '__main__':
	main()
