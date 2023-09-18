from modbus import HoldingRegisters, I16, U16

class Inverter(HoldingRegisters):

    def __init__(self, name, connection, addr, timeout=5):
        super().__init__(name, connection, addr, timeout)
        self._add_param_array([
            U16('run_state',               '',    1,    0,  59),
            U16('grid_frequency',        'Hz',  100,    0,  79),
            U16('heat_sink_temp',        '°C',   10, 1000,  90),
            U16('igbt_module_temp',      '°C',   10, 1000,  91),
            U16('environment_temp',      '°C',   10, 1000,  95),
        ])
        self._add_param_array([
            U16('pv1_voltage',            'V',   10,    0, 109),
            U16('pv2_voltage',            'V',   10,    0, 111),
            U16('grid_v_l1_n',            'V',   10,    0, 150),
            U16('inverter_v_l1_n',        'V',   10,    0, 154),
            U16('load_v_l1',              'V',   10,    0, 157),
            I16('grid_l1_power',         'kW', 1000,    0, 167),
            I16('grid_power',            'kW', 1000,    0, 169),
            I16('grid_ct_power',         'kW', 1000,    0, 172),
            I16('inverter_l1_power',     'kW', 1000,    0, 173),
            I16('inverter_power',        'kW', 1000,    0, 175),
            I16('load_l1_power',         'kW', 1000,    0, 176),
            I16('load_power',            'kW', 1000,    0, 178),
            U16('battery_temp',          '°C',   10, 1000, 182),
            U16('battery_voltage',        'V',  100,    0, 183),
            U16('battery_soc',            '%',    1,    0, 184),
            I16('pv1_power',             'kW', 1000,    0, 186),
            I16('pv2_power',             'kW', 1000,    0, 187),
            I16('battery_power',         'kW', 1000,    0, 190),
        ])
