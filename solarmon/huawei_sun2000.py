import time

from modbus import HoldingRegisters, Register, TcpLink

class HuaweiWifi(TcpLink):

    def __init__(self, host, port, boot_time=2):
        TcpLink.__init__(self, host, port)
        self._boot_time = boot_time

    def connect(self):
        TcpLink.connect(self)
        time.sleep(self._boot_time)


class Dongle(HoldingRegisters):

    def __init__(self, name, connection, addr, timeout=5):
        HoldingRegisters.__init__(self, name, connection, addr, timeout)
        self._add_register_array([
            Register('total_input_power',                      'U32', 'kW',  1000, 37498, 2), # Total input power
            Register('load_power',                             'U32', 'kW',  1000, 37500, 2), # Load power
            Register('grid_power',                             'I32', 'kW',  1000, 37502, 2), # Grid power
            Register('total_battery_power',                    'I32', 'kW',  1000, 37504, 2), # Total battery power
        ])


class Inverter(HoldingRegisters):

    def __init__(self, name, connection, addr, timeout=5):
        HoldingRegisters.__init__(self, name, connection, addr, timeout)
        self._add_register_array([
            Register('P-PV',                                   'I32', 'kW',  1000, 32064, 2), # Input power
            Register('V-L1-inverter',                          'U16',  'V',    10, 32069, 1), # Phase A voltage
            Register('V-L2-inverter',                          'U16',  'V',    10, 32070, 1), # Phase B voltage
            Register('V-L3-inverter',                          'U16',  'V',    10, 32071, 1), # Phase C voltage
            Register('P-inverter',                             'I32', 'kW',  1000, 32080, 2), # Active power
            Register('T-inverter',                             'I16', '°C',    10, 32087, 1), # Internal temperature
            Register('E-inverter-total',                       'U32', 'kW',   100, 32106, 2), # Accumulated energy yield
            Register('E-inverter-day',                         'U32', 'kW',   100, 32114, 2), # Daily energy yield
        ])
        self._add_register_array([
            Register('V-L1-grid',                              'I32',   'V',   10, 37101, 2), # Grid voltage (A phase)
            Register('V-L2-grid',                              'I32',   'V',   10, 37103, 2), # B phase voltage
            Register('V-L3-grid',                              'I32',   'V',   10, 37105, 2), # C phase voltage
            # the following register actually has unit 'W' and gain 1
            Register('P-to_grid',                              'I32',  'kW', 1000, 37113, 2), # [Power meter collection] Active power
            Register('F-grid',                                 'I16',  'Hz',  100, 37118, 1), # Grid frequency
            Register('E-to_grid-total',                        'I32', 'kWh',  100, 37119, 2), # Positive active electricity
            Register('E-from_grid-total',                      'I32', 'kWh',  100, 37121, 2), # Reverse active power
            # the following register actually has unit 'W' and gain 1
            Register('P-L1-to_grid',                           'I32',  'kW', 1000, 37132, 2), # A phase active power
            # the following register actually has unit 'W' and gain 1
            Register('P-L2-to_grid',                           'I32',  'kW', 1000, 37134, 2), # B phase active power
            # the following register actually has unit 'W' and gain 1
            Register('P-L3-to_grid',                           'I32',  'kW', 1000, 37136, 2), # C phase active power
        ])
        self._add_register_array([
            Register('T-esu2',                                 'I16',  '°C',   10, 37752, 1), # [Energy storage unit 2] Battery temperature
            Register('SOC-battery',                            'U16',   '%',   10, 37760, 1), # [Energy storage] SOC
            # the following register actually has unit 'W' and gain 1
            Register('P-to_battery',                           'I32',  'kW', 1000, 37765, 2), # [Energy storage] Charge/Discharge power
            Register('E-to_battery-total',                     'U32', 'kWh',  100, 37780, 2), # [Energy storage] Total charge
            Register('E-from_battery-total',                   'U32', 'kWh',  100, 37782, 2), # [Energy storage] Total discharge
            Register('E-to_battery-day',                       'U32', 'kWh',  100, 37784, 2), # [Energy storage] Current-day charge capacity
            Register('E-from_battery-day',                     'U32', 'kWh',  100, 37786, 2), # [Energy storage] Current-day discharge capacity
        ])
        self._add_register_array([
            Register('T-esu1-b1-max',                          'I16',  '°C',   10, 38452, 1), # [Energy storage unit 1] [Battery pack 1] Maximum temperature
            Register('T-esu1-b1-min',                          'I16',  '°C',   10, 38453, 1), # [Energy storage unit 1] [Battery pack 1] Minimum temperature
            Register('T-esu1-b2-max',                          'I16',  '°C',   10, 38454, 1), # [Energy storage unit 1] [Battery pack 2] Maximum temperature
            Register('T-esu1-b2-min',                          'I16',  '°C',   10, 38455, 1), # [Energy storage unit 1] [Battery pack 2] Minimum temperature
            Register('T-esu1-b3-max',                          'I16',  '°C',   10, 38456, 1), # [Energy storage unit 1] [Battery pack 3] Maximum temperature
            Register('T-esu1-b3-min',                          'I16',  '°C',   10, 38457, 1), # [Energy storage unit 1] [Battery pack 3] Minimum temperature
            Register('T-esu2-b1-max',                          'I16',  '°C',   10, 38458, 1), # [Energy storage unit 2] [Battery pack 1] Maximum temperature
            Register('T-esu2-b1-min',                          'I16',  '°C',   10, 38459, 1), # [Energy storage unit 2] [Battery pack 1] Minimum temperature
            Register('T-esu2-b2-max',                          'I16',  '°C',   10, 38460, 1), # [Energy storage unit 2] [Battery pack 2] Maximum temperature
            Register('T-esu2-b2-min',                          'I16',  '°C',   10, 38461, 1), # [Energy storage unit 2] [Battery pack 2] Minimum temperature
            Register('T-esu2-b3-max',                          'I16',  '°C',   10, 38462, 1), # [Energy storage unit 2] [Battery pack 3] Maximum temperature
            Register('T-esu2-b3-min',                          'I16',  '°C',   10, 38463, 1), # [Energy storage unit 2] [Battery pack 3] Minimum temperature
        ])
        self._add_sparse_registers([
            Register('T-esu1',                                 'I16',  '°C',   10, 37022, 1), # temperature
        ])
