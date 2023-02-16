import time

from modbus import HoldingRegisters, Parameter, TcpLink

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
        self._add_param_array([
            Parameter('total_input_power',                      'U32', 'kW',  1000, 0, 37498, 2), # Total input power
            Parameter('load_power',                             'U32', 'kW',  1000, 0, 37500, 2), # Load power
            Parameter('grid_power',                             'I32', 'kW',  1000, 0, 37502, 2), # Grid power
            Parameter('total_battery_power',                    'I32', 'kW',  1000, 0, 37504, 2), # Total battery power
        ])


class Inverter(HoldingRegisters):

    def __init__(self, name, connection, addr, timeout=5):
        HoldingRegisters.__init__(self, name, connection, addr, timeout)
        self._add_param_array([
            Parameter('P-PV',                                   'I32',  'kW', 1000, 0, 32064, 2), # Input power
            Parameter('V-L1-inverter',                          'U16',   'V',   10, 0, 32069, 1), # Phase A voltage
            Parameter('V-L2-inverter',                          'U16',   'V',   10, 0, 32070, 1), # Phase B voltage
            Parameter('V-L3-inverter',                          'U16',   'V',   10, 0, 32071, 1), # Phase C voltage
            Parameter('P-inverter',                             'I32',  'kW', 1000, 0, 32080, 2), # Active power
            Parameter('T-inverter',                             'I16',  '°C',   10, 0, 32087, 1), # Internal temperature
            Parameter('E-inverter-total',                       'U32',  'kW',  100, 0, 32106, 2), # Accumulated energy yield
            Parameter('E-inverter-day',                         'U32',  'kW',  100, 0, 32114, 2), # Daily energy yield
        ])
        self._add_param_array([
            Parameter('V-L1-grid',                              'I32',   'V',   10, 0, 37101, 2), # Grid voltage (A phase)
            Parameter('V-L2-grid',                              'I32',   'V',   10, 0, 37103, 2), # B phase voltage
            Parameter('V-L3-grid',                              'I32',   'V',   10, 0, 37105, 2), # C phase voltage
            # the following register actually has unit 'W' and gain 1
            Parameter('P-to_grid',                              'I32',  'kW', 1000, 0, 37113, 2), # [Power meter collection] Active power
            Parameter('F-grid',                                 'I16',  'Hz',  100, 0, 37118, 1), # Grid frequency
            Parameter('E-to_grid-total',                        'I32', 'kWh',  100, 0, 37119, 2), # Positive active electricity
            Parameter('E-from_grid-total',                      'I32', 'kWh',  100, 0, 37121, 2), # Reverse active power
            # the following register actually has unit 'W' and gain 1
            Parameter('P-L1-to_grid',                           'I32',  'kW', 1000, 0, 37132, 2), # A phase active power
            # the following register actually has unit 'W' and gain 1
            Parameter('P-L2-to_grid',                           'I32',  'kW', 1000, 0, 37134, 2), # B phase active power
            # the following register actually has unit 'W' and gain 1
            Parameter('P-L3-to_grid',                           'I32',  'kW', 1000, 0, 37136, 2), # C phase active power
        ])
        self._add_param_array([
            Parameter('T-esu2',                                 'I16',  '°C',   10, 0, 37752, 1), # [Energy storage unit 2] Battery temperature
            Parameter('SOC-battery',                            'U16',   '%',   10, 0, 37760, 1), # [Energy storage] SOC
            # the following register actually has unit 'W' and gain 1
            Parameter('P-to_battery',                           'I32',  'kW', 1000, 0, 37765, 2), # [Energy storage] Charge/Discharge power
            Parameter('E-to_battery-total',                     'U32', 'kWh',  100, 0, 37780, 2), # [Energy storage] Total charge
            Parameter('E-from_battery-total',                   'U32', 'kWh',  100, 0, 37782, 2), # [Energy storage] Total discharge
            Parameter('E-to_battery-day',                       'U32', 'kWh',  100, 0, 37784, 2), # [Energy storage] Current-day charge capacity
            Parameter('E-from_battery-day',                     'U32', 'kWh',  100, 0, 37786, 2), # [Energy storage] Current-day discharge capacity
        ])
        self._add_param_array([
            Parameter('T-esu1-b1-max',                          'I16',  '°C',   10, 0, 38452, 1), # [Energy storage unit 1] [Battery pack 1] Maximum temperature
            Parameter('T-esu1-b1-min',                          'I16',  '°C',   10, 0, 38453, 1), # [Energy storage unit 1] [Battery pack 1] Minimum temperature
            Parameter('T-esu1-b2-max',                          'I16',  '°C',   10, 0, 38454, 1), # [Energy storage unit 1] [Battery pack 2] Maximum temperature
            Parameter('T-esu1-b2-min',                          'I16',  '°C',   10, 0, 38455, 1), # [Energy storage unit 1] [Battery pack 2] Minimum temperature
            Parameter('T-esu1-b3-max',                          'I16',  '°C',   10, 0, 38456, 1), # [Energy storage unit 1] [Battery pack 3] Maximum temperature
            Parameter('T-esu1-b3-min',                          'I16',  '°C',   10, 0, 38457, 1), # [Energy storage unit 1] [Battery pack 3] Minimum temperature
            Parameter('T-esu2-b1-max',                          'I16',  '°C',   10, 0, 38458, 1), # [Energy storage unit 2] [Battery pack 1] Maximum temperature
            Parameter('T-esu2-b1-min',                          'I16',  '°C',   10, 0, 38459, 1), # [Energy storage unit 2] [Battery pack 1] Minimum temperature
            Parameter('T-esu2-b2-max',                          'I16',  '°C',   10, 0, 38460, 1), # [Energy storage unit 2] [Battery pack 2] Maximum temperature
            Parameter('T-esu2-b2-min',                          'I16',  '°C',   10, 0, 38461, 1), # [Energy storage unit 2] [Battery pack 2] Minimum temperature
            Parameter('T-esu2-b3-max',                          'I16',  '°C',   10, 0, 38462, 1), # [Energy storage unit 2] [Battery pack 3] Maximum temperature
            Parameter('T-esu2-b3-min',                          'I16',  '°C',   10, 0, 38463, 1), # [Energy storage unit 2] [Battery pack 3] Minimum temperature
        ])
        self._add_sparse_params([
            Parameter('T-esu1',                                 'I16',  '°C',   10, 0, 37022, 1), # temperature
        ])
