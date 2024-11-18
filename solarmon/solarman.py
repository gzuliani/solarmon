#!env/bin/python -u
# the line above disables stdout/stderr buffering

import logging

from pysolarmanv5 import PySolarmanV5


# Mimics the pymodbus.Response
class Response:
    def __init__(self, data):
        self.registers = data

    def isError(self):
        return False


class StickLoggerWiFi:
    def __init__(self, ip_addr, serial, unit):
        self.ip_addr = ip_addr
        self.serial = serial
        self.unit = unit
        self._connected = False
        self._client = None

    def connect(self):
        if not self._connected:
            logging.info('Connecting to "%s@%s"...', self.unit, self.ip_addr)
            try:
                self._client = PySolarmanV5(
                    self.ip_addr, self.serial, mb_slave_id=self.unit)
                self._connected = True
                logging.info('Connection established!')
            except Exception as e:
                logging.info('Could not connect, reason: %s', e)

    def disconnect(self):
        if self._connected:
            try:
                logging.info('Disconnecting from "%s@%s"...',
                    self.unit, self.ip_addr)
                self._client.disconnect()
                self._client = None
                self._connected = False
                logging.info('Connection closed!')
            except Exception as e:
                logging.info('Could not disconnect, reason: %s...', e)

    def reconnect(self):
        self.disconnect()
        self.connect()

    def read_holding_registers(self, addr, count, unit):
        assert unit == self.unit
        if not self._connected:
            raise RuntimeError('No connection available')
        return Response(
            self._client.read_holding_registers(
                register_addr=addr, quantity=count))

    def read_input_registers(self, addr, count, unit):
        assert unit == self.unit
        if not self._connected:
            raise RuntimeError('No connection available')
        return Response(
            self._client.read_input_registers(
                register_addr=addr, quantity=count))
