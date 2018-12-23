#!/usr/bin/env python3
import socket
from functools import reduce
from operator import add
from binascii import hexlify
import logging

logger = logging.getLogger(__name__)


def hex2dec(hex):
    return int(hex, 16)


class Bulb:
    def __init__(self, ip, port=5577, max_attempts=3, timeout=1):
        self.ip = ip
        self.port = port
        self.max_attempts = max_attempts
        self.timeout = timeout

        self.socket = None

        self.connect()

    # Internals
    def connect(self) -> None:
        logger.info('Connecting to {}:{}'.format(self.ip, self.port))
        socket.setdefaulttimeout(self.timeout)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attempt = 0
        while attempt < self.max_attempts:
            try:
                self.socket.connect((self.ip, self.port))
            except OSError:
                attempt += 1
                logger.warn('Connecting failed, trying again')
            else:
                logger.debug('Connected')
                break

    def disconnect(self) -> None:
        logger.debug('Disconnecting')
        self.socket.close()

    def reconnect(self) -> None:
        self.disconnect()
        self.connect()

    def turn_on(self):
        self._send([0x71, 0x23, 0x0f])

    def turn_off(self):
        self._send([0x71, 0x24, 0x0f])

    def status(self) -> list:
        logger.debug('Showing status')
        self._send([0x81, 0x8a, 0x8b])
        raw_status = self._receive()
        status = self._parse_status(raw_status)

        if status is False:
            return None

        return status

    def set_brightness(self, brightness) -> None:
        logger.info('Sets the lights to a nice warm light')
        self._send([0x31, 0x00, 0x00, 0x00] + [brightness] + [0x0f, 0x0f])

    def set_color(self, red, green, blue) -> None:
        logger.info('Sets the lights to the colour (R: {}, G: {}, B: {})'.format(red, green, blue))
        self._send([0x31] + [red, green, blue] + [0x00, 0xf0, 0x0f])

    def _send(self, msg) -> None:
        # self.reconnect() # This should not be necessary
        logger.debug('Sending message', msg)
        checksum = self._checksum(msg)

        attempt = 0
        e = None
        while attempt < self.max_attempts:
            try:
                self.socket.send(bytes(msg + [checksum]))
            except socket.error as error:
                e = error
                logger.warn('Failed to send, reconnecting')
                attempt += 1
                self.reconnect()
            else:
                logger.debug('Message sent')
                return
        logger.error('Failed to send. Maximum attempts ({:d}) reached'.format(MAX_ATTEMPTS))
        raise e

    def _receive(self) -> list:
        msg = ''
        try:
            while len(msg) < 28:
                data_b = self.socket.recv(14)
                data = hexlify(data_b)
                msg += data.decode('UTF-8')
        except socket.error:
            logger.error('Connection timed out while receiving message')
            raise

        msg_bytes_hex = [msg[i:i + 2] for i in range(0, len(msg), 2)]
        msg_bytes = list(map(hex2dec, msg_bytes_hex))
        return msg_bytes

    def _parse_status(self, raw_status):
        status = [
            raw_status[0:2],
            raw_status[2], 	# Status
            raw_status[3:5],
            raw_status[5],
            raw_status[6:9], 	# Color
            raw_status[9], 	# Brightness (warm setting)
            raw_status[10:12],
            raw_status[12],
            raw_status[13], 	# Checksum
        ]

        if self._validate_status(status) is False:
            return False

        response = {
            'state': status[1] == 35,
            'brightness': status[5],
            'color': status[4]
        }

        return response

    @staticmethod
    def _checksum(msg) -> int:
        return reduce(add, msg) % 256

    @staticmethod
    def _validate_status(response) -> bool:
        fixed_pos = { 0: [0x81, 0x44], 2: [0x61, 0x21], 6: [0x04, 0x00] }
        for i, v in fixed_pos.items():
            if response[i] != v:
                return False

        return True
