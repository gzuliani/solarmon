#!env/bin/python -u
# the line above disables stdout/stderr buffering

import logging

from pysolarmanv5 import PySolarmanV5


# Mimics the pymodbus.Response
class Response:

    def __init__(self, data, error=None):
        self.registers = data
        self._error = error

    def isError(self):
        return self._error


class StickLoggerWiFi:

    def __init__(self, ip_addr, serial_no):
        self.ip_addr = ip_addr
        self.serial_no = serial_no
        self._connected = False

    def connect(self):
        if not self._connected:
            print('Connecting to "%s"...' % self.ip_addr)
            logging.info('Connecting to "%s"...' % self.ip_addr)
            try:
                self._client = PySolarmanV5(
                    self.ip_addr, self.serial_no, port=8899, mb_slave_id=1)
                self._connected = True
                print('Connection established!')
                logging.info('Connection established!')
            except Exception as e:
                print('Could not connect, reason: %s' % e)
                logging.info('Could not connect, reason: %s' % e)

    def disconnect(self):
        if self._connected:
            try:
                logging.info('Disconnecting from "%s"...', self._name)
                self._client.disconnect()
                self._connected = False
                logging.info('Connection closed!')
            except Exception as e:
                logging.info('Could not disconnect, reason: %s...', e)

    def reconnect(self):
        self.disconnect()
        self.connect()

    def read_holding_registers(self, addr, count, unit):
        try:
            return Response(
                self._client.read_holding_registers(
                    register_addr=addr, quantity=count))
        except Exception as e:
            return Response(None, error=str(e))

    def read_input_registers(self, addr, count, unit):
        try:
            return Response(
                self._client.read_input_registers(
                    register_addr=addr, quantity=count))
        except Exception as e:
            return Response(None, error=str(e))
