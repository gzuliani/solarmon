import time

from modbus import TcpLink, HoldingRegisters, STR, I16, U16, U32, I32

class HuaweiWifi(TcpLink):
    def __init__(self, host, port, timeout, boot_time=2):
        super().__init__(host, port, timeout)
        self._boot_time = boot_time

    def connect(self):
        TcpLink.connect(self)
        time.sleep(self._boot_time)


class Dongle(HoldingRegisters):
    def __init__(self, name, connection, addr):
        super().__init__(name, connection, addr)
        self._add_param_array([
            U32('total_input_power',              'kW', 1000, 0, 37498    ), # Total input power
            U32('load_power',                     'kW', 1000, 0, 37500    ), # Load power
            I32('grid_power',                     'kW', 1000, 0, 37502    ), # Grid power
            I32('total_battery_power',            'kW', 1000, 0, 37504    ), # Total battery power
            I32('total_active_power',             'kW', 1000, 0, 37516    ), # Total active power
        ])


# register ranges common to single and three-phase inverters
class CommonRegisters(HoldingRegisters):
    def __init__(self, name, connection, addr):
        super().__init__(name, connection, addr)
        self._add_32xxx_params()
        self._add_371xx_params()
        self._add_param_array([
            I16('T-esu2',                         '°C',   10, 0, 37752    ), # [Energy storage unit 2] Battery temperature
            U16('SOC-battery',                     '%',   10, 0, 37760    ), # [Energy storage] SOC
            # the following register actually has unit 'W' and gain 1
            I32('P-to_battery',                   'kW', 1000, 0, 37765    ), # [Energy storage] Charge/Discharge power
            U32('E-to_battery-total',            'kWh',  100, 0, 37780    ), # [Energy storage] Total charge
            U32('E-from_battery-total',          'kWh',  100, 0, 37782    ), # [Energy storage] Total discharge
            U32('E-to_battery-day',              'kWh',  100, 0, 37784    ), # [Energy storage] Current-day charge capacity
            U32('E-from_battery-day',            'kWh',  100, 0, 37786    ), # [Energy storage] Current-day discharge capacity
        ])
        self._add_param_array([
            U16('X-esu1-b1-soh-cal-status',         '',    1, 0, 37920    ), # [Energy storage unit 1][Battery pack 1] SOH Calibration Status
            U16('X-esu1-b2-soh-cal-status',         '',    1, 0, 37921    ), # [Energy storage unit 1][Battery pack 2] SOH Calibration Status
            U16('X-esu1-b3-soh-cal-status',         '',    1, 0, 37922    ), # [Energy storage unit 1][Battery pack 3] SOH Calibration Status
            U16('X-esu2-b1-soh-cal-status',         '',    1, 0, 37923    ), # [Energy storage unit 2][Battery pack 1] SOH Calibration Status
            U16('X-esu2-b2-soh-cal-status',         '',    1, 0, 37924    ), # [Energy storage unit 2][Battery pack 2] SOH Calibration Status
            U16('X-esu2-b3-soh-cal-status',         '',    1, 0, 37925    ), # [Energy storage unit 2][Battery pack 3] SOH Calibration Status
            U16('X-soh-cal-status',                 '',    1, 0, 37926    ), # SOH Calibration Status
            U16('X-soh-cal-release-low-limit',      '',   10, 0, 37927    ), # SOH Calibration Release the lower discharge limit of the SOC
            U16('X-soh-cal-enable-backup-power',    '',   10, 0, 37928    ), # SOH Calibration Enable the backup power SOC
        ])
        self._add_param_array([
            # STR('S-esu1-b1-sn',                                  38200, 10), # [Energy storage unit 1][Battery pack 1] SN
            # STR('S-esu1-b1-fw-version',                          38210, 15), # [Energy storage unit 1][Battery pack 1] Firmware version
            U16('X-esu1-b1-status',                 '',    1, 0, 38228    ), # [Energy storage unit 1][Battery pack 1] Working status
            U16('X-esu1-b1-soc',                   '%',   10, 0, 38229    ), # [Energy storage unit 1][Battery pack 1] SOC
            I32('P-esu1-b1',                      'kW', 1000, 0, 38233    ), # [Energy storage unit 1][Battery pack 1] Charge/Discharge power
            U16('V-esu1-b1',                       'V',   10, 0, 38235    ), # [Energy storage unit 1][Battery pack 1] Voltage
            I16('C-esu1-b1',                       'A',   10, 0, 38236    ), # [Energy storage unit 1][Battery pack 1] Current
            U32('E-to_esu1-b1-total',            'kWh',  100, 0, 38238    ), # [Energy storage unit 1][Battery pack 1] Total charge
            U32('E-from_esu1-b1-total',          'kWh',  100, 0, 38240    ), # [Energy storage unit 1][Battery pack 1] Total discharge
            # STR('S-esu1-b2-sn',                                  38242, 10), # [Energy storage unit 1][Battery pack 2] SN
            # STR('S-esu1-b2-fw-version',                          38252, 15), # [Energy storage unit 1][Battery pack 2] Firmware version
            U16('X-esu1-b2-status',                 '',    1, 0, 38270    ), # [Energy storage unit 1][Battery pack 2] Working status
            U16('X-esu1-b2-soc',                   '%',   10, 0, 38271    ), # [Energy storage unit 1][Battery pack 2] SOC
            I32('P-esu1-b2',                      'kW', 1000, 0, 38275    ), # [Energy storage unit 1][Battery pack 2] Charge/Discharge power
            U16('V-esu1-b2',                       'V',   10, 0, 38277    ), # [Energy storage unit 1][Battery pack 2] Voltage
            I16('C-esu1-b2',                       'A',   10, 0, 38278    ), # [Energy storage unit 1][Battery pack 2] Current
        ])
        self._add_param_array([
            U32('E-to_esu1-b2-total',            'kWh',  100, 0, 38280    ), # [Energy storage unit 1][Battery pack 2] Total charge
            U32('E-from_esu1-b2-total',          'kWh',  100, 0, 38282    ), # [Energy storage unit 1][Battery pack 2] Total discharge
            # STR('S-esu1-b3-sn',                                  38284, 10), # [Energy storage unit 1][Battery pack 3] SN
            # STR('S-esu1-b3-fw-version',                          38294, 15), # [Energy storage unit 1][Battery pack 3] Firmware version
            U16('X-esu1-b3-status',                 '',    1, 0, 38312    ), # [Energy storage unit 1][Battery pack 3] Working status
            U16('X-esu1-b3-soc',                   '%',   10, 0, 38313    ), # [Energy storage unit 1][Battery pack 3] SOC
            I32('P-esu1-b3',                      'kW', 1000, 0, 38317    ), # [Energy storage unit 1][Battery pack 3] Charge/Discharge power
            U16('V-esu1-b3',                       'V',   10, 0, 38319    ), # [Energy storage unit 1][Battery pack 3] Voltage
            I16('C-esu1-b3',                       'A',   10, 0, 38320    ), # [Energy storage unit 1][Battery pack 3] Current
            U32('E-to_esu1-b3-total',            'kWh',  100, 0, 38322    ), # [Energy storage unit 1][Battery pack 3] Total charge
            U32('E-from_esu1-b3-total',          'kWh',  100, 0, 38324    ), # [Energy storage unit 1][Battery pack 3] Total discharge
            # STR('S-esu2-b1-sn',                                  38326, 10), # [Energy storage unit 2][Battery pack 1] SN
            # STR('S-esu2-b1-fw-version',                          38336, 15), # [Energy storage unit 2][Battery pack 1] Firmware version
            U16('X-esu2-b1-status',                 '',    1, 0, 38354    ), # [Energy storage unit 2][Battery pack 1] Working status
            U16('X-esu2-b1-soc',                   '%',   10, 0, 38355    ), # [Energy storage unit 2][Battery pack 1] SOC
            I32('P-esu2-b1',                      'kW', 1000, 0, 38359    ), # [Energy storage unit 2][Battery pack 1] Charge/Discharge power
            U16('V-esu2-b1',                       'V',   10, 0, 38361    ), # [Energy storage unit 2][Battery pack 1] Voltage
            I16('C-esu2-b1',                       'A',   10, 0, 38362    ), # [Energy storage unit 2][Battery pack 1] Current
            U32('E-to_esu2-b1-total',            'kWh',  100, 0, 38364    ), # [Energy storage unit 2][Battery pack 1] Total charge
            U32('E-from_esu2-b1-total',          'kWh',  100, 0, 38366    ), # [Energy storage unit 2][Battery pack 1] Total discharge
        ])
        self._add_param_array([
            # STR('S-esu2-b2-sn',                                  38368, 10), # [Energy storage unit 2][Battery pack 2] SN
            # STR('S-esu2-b2-fw-version',                          38378, 15), # [Energy storage unit 2][Battery pack 2] Firmware version
            U16('X-esu2-b2-status',                 '',    1, 0, 38396    ), # [Energy storage unit 2][Battery pack 2] Working status
            U16('X-esu2-b2-soc',                   '%',   10, 0, 38397    ), # [Energy storage unit 2][Battery pack 2] SOC
            I32('P-esu2-b2',                      'kW', 1000, 0, 38401    ), # [Energy storage unit 2][Battery pack 2] Charge/Discharge power
            U16('V-esu2-b2',                       'V',   10, 0, 38403    ), # [Energy storage unit 2][Battery pack 2] Voltage
            I16('C-esu2-b2',                       'A',   10, 0, 38404    ), # [Energy storage unit 2][Battery pack 2] Current
            U32('E-to_esu2-b2-total',            'kWh',  100, 0, 38406    ), # [Energy storage unit 2][Battery pack 2] Total charge
            U32('E-from_esu2-b2-total',          'kWh',  100, 0, 38408    ), # [Energy storage unit 2][Battery pack 2] Total discharge
            # STR('S-esu2-b3-sn',                                  38410, 10), # [Energy storage unit 2][Battery pack 3] SN
            # STR('S-esu2-b3-fw-version',                          38420, 15), # [Energy storage unit 2][Battery pack 3] Firmware version
            U16('X-esu2-b3-status',                 '',    1, 0, 38438    ), # [Energy storage unit 2][Battery pack 3] Working status
            U16('X-esu2-b3-soc',                   '%',   10, 0, 38439    ), # [Energy storage unit 2][Battery pack 3] SOC
            I32('P-esu2-b3',                      'kW', 1000, 0, 38443    ), # [Energy storage unit 2][Battery pack 3] Charge/Discharge power
            U16('V-esu2-b3',                       'V',   10, 0, 38445    ), # [Energy storage unit 2][Battery pack 3] Voltage
            I16('C-esu2-b3',                       'A',   10, 0, 38446    ), # [Energy storage unit 2][Battery pack 3] Current
            U32('E-to_esu2-b3-total',            'kWh',  100, 0, 38448    ), # [Energy storage unit 2][Battery pack 3] Total charge
            U32('E-from_esu2-b3-total',          'kWh',  100, 0, 38450    ), # [Energy storage unit 2][Battery pack 3] Total discharge
        ])
        self._add_param_array([
            I16('T-esu1-b1-max',                  '°C',   10, 0, 38452    ), # [Energy storage unit 1] [Battery pack 1] Maximum temperature
            I16('T-esu1-b1-min',                  '°C',   10, 0, 38453    ), # [Energy storage unit 1] [Battery pack 1] Minimum temperature
            I16('T-esu1-b2-max',                  '°C',   10, 0, 38454    ), # [Energy storage unit 1] [Battery pack 2] Maximum temperature
            I16('T-esu1-b2-min',                  '°C',   10, 0, 38455    ), # [Energy storage unit 1] [Battery pack 2] Minimum temperature
            I16('T-esu1-b3-max',                  '°C',   10, 0, 38456    ), # [Energy storage unit 1] [Battery pack 3] Maximum temperature
            I16('T-esu1-b3-min',                  '°C',   10, 0, 38457    ), # [Energy storage unit 1] [Battery pack 3] Minimum temperature
            I16('T-esu2-b1-max',                  '°C',   10, 0, 38458    ), # [Energy storage unit 2] [Battery pack 1] Maximum temperature
            I16('T-esu2-b1-min',                  '°C',   10, 0, 38459    ), # [Energy storage unit 2] [Battery pack 1] Minimum temperature
            I16('T-esu2-b2-max',                  '°C',   10, 0, 38460    ), # [Energy storage unit 2] [Battery pack 2] Maximum temperature
            I16('T-esu2-b2-min',                  '°C',   10, 0, 38461    ), # [Energy storage unit 2] [Battery pack 2] Minimum temperature
            I16('T-esu2-b3-max',                  '°C',   10, 0, 38462    ), # [Energy storage unit 2] [Battery pack 3] Maximum temperature
            I16('T-esu2-b3-min',                  '°C',   10, 0, 38463    ), # [Energy storage unit 2] [Battery pack 3] Minimum temperature
        ])
        self._add_sparse_params([
            I16('T-esu1',                         '°C',   10, 0, 37022    ), # temperature
        ])


# old inverter model, contains both single and three-phase data
class Inverter(CommonRegisters):
    def __init__(self, name, connection, addr):
        super().__init__(name, connection, addr)

    def _add_32xxx_params(self):
        self._add_param_array([
            I32('P-PV',                           'kW', 1000, 0, 32064    ), # Input power
            U16('V-L1-inverter',                   'V',   10, 0, 32069    ), # Phase A voltage
            U16('V-L2-inverter',                   'V',   10, 0, 32070    ), # Phase B voltage
            U16('V-L3-inverter',                   'V',   10, 0, 32071    ), # Phase C voltage
            I32('P-inverter',                     'kW', 1000, 0, 32080    ), # Active power
            I16('T-inverter',                     '°C',   10, 0, 32087    ), # Internal temperature
            U32('E-inverter-total',               'kW',  100, 0, 32106    ), # Accumulated energy yield
            U32('E-inverter-day',                 'kW',  100, 0, 32114    ), # Daily energy yield
        ])

    def _add_371xx_params(self):
        self._add_param_array([
            I32('V-L1-grid',                       'V',   10, 0, 37101    ), # Grid voltage (A phase)
            I32('V-L2-grid',                       'V',   10, 0, 37103    ), # B phase voltage
            I32('V-L3-grid',                       'V',   10, 0, 37105    ), # C phase voltage
            # the following register actually has unit 'W' and gain 1
            I32('P-to_grid',                      'kW', 1000, 0, 37113    ), # [Power meter collection] Active power
            I16('F-grid',                         'Hz',  100, 0, 37118    ), # Grid frequency
            I32('E-to_grid-total',               'kWh',  100, 0, 37119    ), # Positive active electricity
            I32('E-from_grid-total',             'kWh',  100, 0, 37121    ), # Reverse active power
            # the following register actually has unit 'W' and gain 1
            I32('P-L1-to_grid',                   'kW', 1000, 0, 37132    ), # A phase active power
            # the following register actually has unit 'W' and gain 1
            I32('P-L2-to_grid',                   'kW', 1000, 0, 37134    ), # B phase active power
            # the following register actually has unit 'W' and gain 1
            I32('P-L3-to_grid',                   'kW', 1000, 0, 37136    ), # C phase active power
        ])


class SinglePhaseInverter(CommonRegisters):
    def __init__(self, name, connection, addr):
        super().__init__(name, connection, addr)

    def _add_32xxx_params(self):
        self._add_param_array([
            I16('V-PV1',                           'V',   10, 0, 32016    ), # PV1 voltage
            I16('C-PV1',                           'A',  100, 0, 32017    ), # PV1 current
            I16('V-PV2',                           'V',   10, 0, 32018    ), # PV2 voltage
            I16('C-PV2',                           'A',  100, 0, 32019    ), # PV2 current
            I32('P-PV',                           'kW', 1000, 0, 32064    ), # Input power
            U16('V-power-grid',                    'V',   10, 0, 32066    ), # Power grid voltage/Line voltage between phases A and B
            I32('C-power-grid',                    'A', 1000, 0, 32072    ), # Power grid current/Phase A current
            I32('P-inverter',                     'kW', 1000, 0, 32080    ), # Active power
            I16('T-inverter',                     '°C',   10, 0, 32087    ), # Internal temperature
            U16('Status',                           '',    1, 0, 32089    ), # Device status
            U32('E-inverter-total',               'kW',  100, 0, 32106    ), # Accumulated energy yield
            U32('E-inverter-day',                 'kW',  100, 0, 32114    ), # Daily energy yield
        ])

    def _add_371xx_params(self):
        self._add_param_array([
            I32('V-grid',                          'V',   10, 0, 37101    ), # Grid voltage (A phase)
            I32('C-meter-grid',                    'A',  100, 0, 37107    ), # Grid current (A phase)
            # the following register actually has unit 'W' and gain 1
            I32('P-to_grid',                      'kW', 1000, 0, 37113    ), # [Power meter collection] Active power
            I16('F-grid',                         'Hz',  100, 0, 37118    ), # Grid frequency
            I32('E-to_grid-total',               'kWh',  100, 0, 37119    ), # Positive active electricity
            I32('E-from_grid-total',             'kWh',  100, 0, 37121    ), # Reverse active power
        ])


class ThreePhaseInverter(CommonRegisters):
    def __init__(self, name, connection, addr):
        super().__init__(name, connection, addr)

    def _add_32xxx_params(self):
        self._add_param_array([
            I16('V-PV1',                           'V',   10, 0, 32016    ), # PV1 voltage
            I16('C-PV1',                           'A',  100, 0, 32017    ), # PV1 current
            I16('V-PV2',                           'V',   10, 0, 32018    ), # PV2 voltage
            I16('C-PV2',                           'A',  100, 0, 32019    ), # PV2 current
            I32('P-PV',                           'kW', 1000, 0, 32064    ), # Input power
            U16('V-L1-inverter',                   'V',   10, 0, 32069    ), # Phase A voltage
            U16('V-L2-inverter',                   'V',   10, 0, 32070    ), # Phase B voltage
            U16('V-L3-inverter',                   'V',   10, 0, 32071    ), # Phase C voltage
            I32('P-inverter',                     'kW', 1000, 0, 32080    ), # Active power
            I16('T-inverter',                     '°C',   10, 0, 32087    ), # Internal temperature
            U16('Status',                           '',    1, 0, 32089    ), # Device status
            U32('E-inverter-total',               'kW',  100, 0, 32106    ), # Accumulated energy yield
            U32('E-inverter-day',                 'kW',  100, 0, 32114    ), # Daily energy yield
        ])

    def _add_371xx_params(self):
        self._add_param_array([
            I32('V-L1-grid',                       'V',   10, 0, 37101    ), # Grid voltage (A phase)
            I32('V-L2-grid',                       'V',   10, 0, 37103    ), # B phase voltage
            I32('V-L3-grid',                       'V',   10, 0, 37105    ), # C phase voltage
            # the following register actually has unit 'W' and gain 1
            I32('P-to_grid',                      'kW', 1000, 0, 37113    ), # [Power meter collection] Active power
            I16('F-grid',                         'Hz',  100, 0, 37118    ), # Grid frequency
            I32('E-to_grid-total',               'kWh',  100, 0, 37119    ), # Positive active electricity
            I32('E-from_grid-total',             'kWh',  100, 0, 37121    ), # Reverse active power
            # the following register actually has unit 'W' and gain 1
            I32('P-L1-to_grid',                   'kW', 1000, 0, 37132    ), # A phase active power
            # the following register actually has unit 'W' and gain 1
            I32('P-L2-to_grid',                   'kW', 1000, 0, 37134    ), # B phase active power
            # the following register actually has unit 'W' and gain 1
            I32('P-L3-to_grid',                   'kW', 1000, 0, 37136    ), # C phase active power
        ])
