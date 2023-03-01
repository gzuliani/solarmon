import time

from modbus import TcpLink, HoldingRegisters, I16, U16, U32, I32

class HuaweiWifi(TcpLink):

    def __init__(self, host, port, boot_time=2):
        super().__init__(host, port)
        self._boot_time = boot_time

    def connect(self):
        TcpLink.connect(self)
        time.sleep(self._boot_time)


class Dongle(HoldingRegisters):

    def __init__(self, name, connection, addr, timeout=5):
        super().__init__(name, connection, addr, timeout)
        self._add_param_array([
            U32('total_input_power',     'kW', 1000, 0, 37498), # Total input power
            U32('load_power',            'kW', 1000, 0, 37500), # Load power
            I32('grid_power',            'kW', 1000, 0, 37502), # Grid power
            I32('total_battery_power',   'kW', 1000, 0, 37504), # Total battery power
        ])


class Inverter(HoldingRegisters):

    def __init__(self, name, connection, addr, timeout=5):
        super().__init__(name, connection, addr, timeout)
        self._add_param_array([
            I32('P-PV',                  'kW', 1000, 0, 32064), # Input power
            U16('V-L1-inverter',          'V',   10, 0, 32069), # Phase A voltage
            U16('V-L2-inverter',          'V',   10, 0, 32070), # Phase B voltage
            U16('V-L3-inverter',          'V',   10, 0, 32071), # Phase C voltage
            I32('P-inverter',            'kW', 1000, 0, 32080), # Active power
            I16('T-inverter',            '°C',   10, 0, 32087), # Internal temperature
            U32('E-inverter-total',      'kW',  100, 0, 32106), # Accumulated energy yield
            U32('E-inverter-day',        'kW',  100, 0, 32114), # Daily energy yield
        ])
        self._add_param_array([
            I32('V-L1-grid',              'V',   10, 0, 37101), # Grid voltage (A phase)
            I32('V-L2-grid',              'V',   10, 0, 37103), # B phase voltage
            I32('V-L3-grid',              'V',   10, 0, 37105), # C phase voltage
            # the following register actually has unit 'W' and gain 1
            I32('P-to_grid',             'kW', 1000, 0, 37113), # [Power meter collection] Active power
            I16('F-grid',                'Hz',  100, 0, 37118), # Grid frequency
            I32('E-to_grid-total',      'kWh',  100, 0, 37119), # Positive active electricity
            I32('E-from_grid-total',    'kWh',  100, 0, 37121), # Reverse active power
            # the following register actually has unit 'W' and gain 1
            I32('P-L1-to_grid',          'kW', 1000, 0, 37132), # A phase active power
            # the following register actually has unit 'W' and gain 1
            I32('P-L2-to_grid',          'kW', 1000, 0, 37134), # B phase active power
            # the following register actually has unit 'W' and gain 1
            I32('P-L3-to_grid',          'kW', 1000, 0, 37136), # C phase active power
        ])
        self._add_param_array([
            I16('T-esu2',                '°C',   10, 0, 37752), # [Energy storage unit 2] Battery temperature
            U16('SOC-battery',            '%',   10, 0, 37760), # [Energy storage] SOC
            # the following register actually has unit 'W' and gain 1
            I32('P-to_battery',          'kW', 1000, 0, 37765), # [Energy storage] Charge/Discharge power
            U32('E-to_battery-total',   'kWh',  100, 0, 37780), # [Energy storage] Total charge
            U32('E-from_battery-total', 'kWh',  100, 0, 37782), # [Energy storage] Total discharge
            U32('E-to_battery-day',     'kWh',  100, 0, 37784), # [Energy storage] Current-day charge capacity
            U32('E-from_battery-day',   'kWh',  100, 0, 37786), # [Energy storage] Current-day discharge capacity
        ])
        self._add_param_array([
            I16('T-esu1-b1-max',         '°C',   10, 0, 38452), # [Energy storage unit 1] [Battery pack 1] Maximum temperature
            I16('T-esu1-b1-min',         '°C',   10, 0, 38453), # [Energy storage unit 1] [Battery pack 1] Minimum temperature
            I16('T-esu1-b2-max',         '°C',   10, 0, 38454), # [Energy storage unit 1] [Battery pack 2] Maximum temperature
            I16('T-esu1-b2-min',         '°C',   10, 0, 38455), # [Energy storage unit 1] [Battery pack 2] Minimum temperature
            I16('T-esu1-b3-max',         '°C',   10, 0, 38456), # [Energy storage unit 1] [Battery pack 3] Maximum temperature
            I16('T-esu1-b3-min',         '°C',   10, 0, 38457), # [Energy storage unit 1] [Battery pack 3] Minimum temperature
            I16('T-esu2-b1-max',         '°C',   10, 0, 38458), # [Energy storage unit 2] [Battery pack 1] Maximum temperature
            I16('T-esu2-b1-min',         '°C',   10, 0, 38459), # [Energy storage unit 2] [Battery pack 1] Minimum temperature
            I16('T-esu2-b2-max',         '°C',   10, 0, 38460), # [Energy storage unit 2] [Battery pack 2] Maximum temperature
            I16('T-esu2-b2-min',         '°C',   10, 0, 38461), # [Energy storage unit 2] [Battery pack 2] Minimum temperature
            I16('T-esu2-b3-max',         '°C',   10, 0, 38462), # [Energy storage unit 2] [Battery pack 3] Maximum temperature
            I16('T-esu2-b3-min',         '°C',   10, 0, 38463), # [Energy storage unit 2] [Battery pack 3] Minimum temperature
        ])
        self._add_sparse_params([
            I16('T-esu1',                '°C',   10, 0, 37022), # temperature
        ])
