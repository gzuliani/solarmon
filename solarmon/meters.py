import logging
from pymodbus.client.sync import ModbusSerialClient

from modbus import Connection, Device, Register

class USBConnection:

    def __init__(self, port):
        self._port = port
        self._client = ModbusSerialClient(
                method='rtu', port=self._port, baudrate=9600)

    def attach_to_JSY_MK_323_meter(self, addr):
        return JSY_MK_323(Connection(addr, self._client))

    def connect(self):
        logging.info('Opening serial connection {}...'.format(self._port))
        self._client.connect()
        logging.info('Connection opened...')

    def close(self):
        logging.info('Closing serial connection {}...'.format(self._port))
        self._client.close()
        logging.info('Connection closed...')

    def reconnect(self):
        self.close()
        self.connect()


class JSY_MK_323(Device):

    def __init__(self, connection, timeout=1):
        Device.__init__(self, connection, timeout=timeout)
        self._registers = [
            Register('Three-phase active total electric energy (forward)', 'forward_energy', 'U32', 'kWh', 800, 0x0063, 2),
            Register('Frequency',                                          'frequency',      'U16',  'Hz', 100, 0x0065, 1),
            Register('Three-phase active total electric energy (reverse)', 'reverse_energy', 'U32', 'kWh', 800, 0x0066, 2),
        ]

    def read_registers(self):
        return self._read_register_array(self._registers)

    def register_count(self):
        return len(self._registers)
