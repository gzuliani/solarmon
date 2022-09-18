import time

from modbus import Device, Register, TcpLink

class HuaweiWifi(TcpLink):

    def __init__(self, host, port, boot_time=2):
        TcpLink.__init__(self, host, port)
        self._boot_time = boot_time

    def connect(self):
        TcpLink.connect(self)
        time.sleep(self._boot_time)


class Dongle(Device):

    def __init__(self, name, connection, addr, timeout=5):
        Device.__init__(self, name, connection, addr, timeout)
        self._add_register_array([
            Register('total_input_power',                      'U32', 'kW',  1000, 37498, 2), # Total input power
            Register('load_power',                             'U32', 'kW',  1000, 37500, 2), # Load power
            Register('grid_power',                             'I32', 'kW',  1000, 37502, 2), # Grid power
            Register('total_battery_power',                    'I32', 'kW',  1000, 37504, 2), # Total battery power
        ])


class Inverter(Device):

    def __init__(self, name, connection, addr, timeout=5):
        Device.__init__(self, name, connection, addr, timeout)
        self._add_register_array([
            Register('input_power',                            'I32', 'kW',  1000, 32064, 2), # Input power
            Register('phase_a_voltage',                        'U16',  'V',    10, 32069, 1), # Phase A voltage
            Register('phase_b_voltage',                        'U16',  'V',    10, 32070, 1), # Phase B voltage
            Register('phase_c_voltage',                        'U16',  'V',    10, 32071, 1), # Phase C voltage
            Register('day_active_power_peak',                  'I32', 'kW',  1000, 32078, 2), # Peak active power of current day
            Register('active_power',                           'I32', 'kW',  1000, 32080, 2), # Active power
            Register('accumulated_yield_energy',               'U32', 'kW',   100, 32106, 2), # Accumulated energy yield
            Register('daily_yield_energy',                     'U32', 'kW',   100, 32114, 2), # Daily energy yield
        ])
        self._add_register_array([
            # the following register actually has unit 'W' and gain 1
            Register('maximum_charge_power',                   'U32',  'kW', 1000, 37046, 2), # [Energy storage] Maximum charge power
            # the following register actually has unit 'W' and gain 1
            Register('maximum_discharge_power',                'U32',  'kW', 1000, 37048, 2), # [Energy storage] Maximum discharge power
        ])
        self._add_register_array([
            Register('grid_voltage_a_phase',                   'I32',   'V',   10, 37101, 2), # Grid voltage (A phase)
            Register('b_phase_voltage',                        'I32',   'V',   10, 37103, 2), # B phase voltage
            Register('c_phase_voltage',                        'I32',   'V',   10, 37105, 2), # C phase voltage
            # the following register actually has unit 'W' and gain 1
            Register('power_meter_active_power',               'I32',  'kW', 1000, 37113, 2), # [Power meter collection] Active power
            Register('grid_frequency',                         'I16',  'Hz',  100, 37118, 1), # Grid frequency
            Register('grid_exported_energy',                   'I32', 'kWh',  100, 37119, 2), # Positive active electricity
            Register('grid_accumulated_energy',                'I32', 'kWh',  100, 37121, 2), # Reverse active power
            # the following register actually has unit 'W' and gain 1
            Register('a_phase_active_power',                   'I32',  'kW', 1000, 37132, 2), # A phase active power
            # the following register actually has unit 'W' and gain 1
            Register('b_phase_active_power',                   'I32',  'kW', 1000, 37134, 2), # B phase active power
            # the following register actually has unit 'W' and gain 1
            Register('c_phase_active_power',                   'I32',  'kW', 1000, 37136, 2), # C phase active power
        ])
        self._add_register_array([
            Register('storage_state_of_capacity',              'U16',   '%',   10, 37760, 1), # [Energy storage] SOC
            # the following register actually has unit 'W' and gain 1
            Register('storage_charge_discharge_power',         'I32',  'kW', 1000, 37765, 2), # [Energy storage] Charge/Discharge power
            Register('storage_current_day_charge_capacity',    'U32', 'kWh',  100, 37784, 2), # [Energy storage] Current-day charge capacity
            Register('storage_current_day_discharge_capacity', 'U32', 'kWh',  100, 37786, 2), # [Energy storage] Current-day discharge capacity
        ])
        self._add_sparse_registers([
            # No register defined
        ])
