import logging
from pymodbus.client.sync import ModbusTcpClient
import time

from modbus import Connection, Device, Register

class DongleEndPoint:
    host = '192.168.0.11'
    port = '502'
    addr = 100


class InverterThroughDongleEndPoint:
    host = '192.168.0.11'
    port = '502'
    addr = 1


class InverterEndPoint:
    host = '192.168.200.1'
    port = '6607'
    addr = 0


class Dongle(Device):

    def __init__(self, connection, timeout=5):
        Device.__init__(self, connection, timeout)
        self._registers = [
            Register('Total input power',                               'total_input_power',                      'U32', 'kW',  1000, 37498, 2),
            Register('Load power',                                      'load_power',                             'U32', 'kW',  1000, 37500, 2),
            Register('Grid power',                                      'grid_power',                             'I32', 'kW',  1000, 37502, 2),
            Register('Total battery power',                             'total_battery_power',                    'I32', 'kW',  1000, 37504, 2),
            Register('Total active power',                              'total_active_power',                     'I32', 'kW',  1000, 37506, 2),
        ]

    def read_registers(self):
        return self._read_register_array(self._registers)

    def register_count(self):
        return len(self._registers)


class Inverter(Device):

    def __init__(self, connection, timeout=5):
        Device.__init__(self, connection, timeout)
        self._inverter_registers = [
            Register('Input power',                                     'input_power',                            'I32', 'kW',  1000, 32064, 2),
            Register('Peak active power of current day',                'day_active_power_peak',                  'I32', 'kW',  1000, 32078, 2),
            Register('Active power',                                    'active_power',                           'I32', 'kW',  1000, 32080, 2),
            Register('Accumulated energy yield',                        'accumulated_yield_energy',               'U32', 'kW',   100, 32106, 2),
            Register('Daily energy yield',                              'daily_yield_energy',                     'U32', 'kW',   100, 32114, 2),
        ]
        self._power_meter_registers = [
            Register('[Power meter collection] Active power',           'power_meter_active_power',               'I32', 'W',      1, 37113, 2),
            Register('Positive active electricity',                     'grid_exported_energy',                   'I32', 'kWh',  100, 37119, 2),
            Register('Reverse active power',                            'grid_accumulated_energy',                'I32', 'kWh',  100, 37121, 2),
        ]
        self._storage_registers = [
            Register('[Energy storage] SOC',                            'storage_state_of_capacity',              'U16', '%',     10, 37760, 1),
            Register('[Energy storage] Charge/Discharge power',         'storage_charge_discharge_power',         'I32', 'W',      1, 37765, 2),
            Register('[Energy storage] Current-day charge capacity',    'storage_current_day_charge_capacity',    'U32', 'kWh',  100, 37784, 2),
            Register('[Energy storage] Current-day discharge capacity', 'storage_current_day_discharge_capacity', 'U32', 'kWh',  100, 37786, 2),
        ]
        self._misc_registers = [
            Register('System time',                                     'system_time',                            'U32', '',       1, 40000, 2),
            Register('[Backup] Switch to off-grid',                     'backup_switch_to_off_grid',              'U16', '',       1, 47604, 1),
        ]

    def read_registers(self):
        return self._read_register_array(self._inverter_registers) + \
                self._read_register_array(self._power_meter_registers) + \
                self._read_register_array(self._storage_registers) + \
                self._read_registers_one_by_one(self._misc_registers)

    def register_count(self):
        return len(self._inverter_registers) + \
                len(self._power_meter_registers) + \
                len(self._storage_registers) + \
                len(self._misc_registers)

class _ConnectionPool:

    def __init__(self, inverter_endpoint, boot_time=2):
        self._boot_time = boot_time
        self._clients = [
            ModbusTcpClient(DongleEndPoint.host, port=DongleEndPoint.port)
        ]
        if ((DongleEndPoint.host != inverter_endpoint.host)
                or (DongleEndPoint.port != inverter_endpoint.port)):
            self._clients.append(
                ModbusTcpClient(
                    inverter_endpoint.host, port=inverter_endpoint.port))
        self.connect()
        self._dongle = Connection(DongleEndPoint.addr, self._clients[0])
        self._inverter = Connection(inverter_endpoint.addr, self._clients[-1])

    def attach_to_dongle(self, timeout):
        return Dongle(self._dongle, timeout)

    def attach_to_inverter(self, timeout):
        return Inverter(self._inverter, timeout)

    def connect(self):
        logging.info('Opening Modbus/TCP connections...')
        for client in self._clients:
            client.connect()
        time.sleep(self._boot_time)
        logging.info('All connections are ready...')

    def close(self):
        logging.info('Closing Modbus/TCP connections...')
        for client in self._clients:
            client.close()
        logging.info('All connections closed...')

    def reconnect(self):
        self.close()
        self.connect()


class SeparateConnections(_ConnectionPool):

    def __init__(self):
        _ConnectionPool.__init__(self, InverterEndPoint)


class SharedConnection(_ConnectionPool):

    def __init__(self):
        _ConnectionPool.__init__(self, InverterThroughDongleEndPoint)
