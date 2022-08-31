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
        self._add_register_array([
            Register('a_phase_active_power', 'U16',   'W',   1, 0x004A, 1), # A phase active power
            Register('b_phase_active_power', 'U16',   'W',   1, 0x0053, 1), # B phase active power
            Register('c_phase_active_power', 'U16',   'W',   1, 0x005C, 1), # C phase active power
            Register('forward_energy',       'U32', 'kWh', 800, 0x0063, 2), # Three-phase active total electric energy (forward)
        ])
