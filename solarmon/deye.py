from modbus import HoldingRegisters, Parameter

class Inverter(HoldingRegisters):

    def __init__(self, name, connection, addr, timeout=5):
        HoldingRegisters.__init__(self, name, connection, addr, timeout)
        self._add_param_array([
            Parameter('run_state',           'U16',     '',    1,    0,  59, 1),
            Parameter('total_active_energy', 'I32',  'kWh',   10,    0,  63, 2),
            Parameter('grid_frequency',      'U16',   'Hz',  100,    0,  79, 1),
            Parameter('heat_sink_temp',      'U16',   '°C',   10, 1000,  90, 1),
            Parameter('igbt_module_temp',    'U16',   '°C',   10, 1000,  91, 1),
        ])
        self._add_param_array([
            Parameter('pv1_voltage',         'U16',    'V',   10,    0, 109, 1),
            Parameter('pv2_voltage',         'U16',    'V',   10,    0, 111, 1),
            Parameter('grid_v_l1_n',         'U16',    'V',   10,    0, 150, 1),
            Parameter('inverter_v_l1_n',     'U16',    'V',   10,    0, 154, 1),
            Parameter('load_v_l1',           'U16',    'V',   10,    0, 157, 1),
            Parameter('grid_l1_power',       'I16',   'kW', 1000,    0, 167, 1),
            Parameter('grid_power',          'I16',   'kW', 1000,    0, 169, 1),
            Parameter('grid_ct_power',       'I16',   'kW', 1000,    0, 172, 1),
            Parameter('inverter_l1_power',   'I16',   'kW', 1000,    0, 173, 1),
            Parameter('inverter_power',      'I16',   'kW', 1000,    0, 175, 1),
            Parameter('load_l1_power',       'I16',   'kW', 1000,    0, 176, 1),
            Parameter('load_power',          'I16',   'kW', 1000,    0, 178, 1),
            Parameter('battery_temp',        'U16',   '°C',   10, 1000, 182, 1),
            Parameter('battery_voltage',     'U16',    'V',  100,    0, 183, 1),
            Parameter('battery_soc',         'U16',    '%',    1,    0, 184, 1),
            Parameter('pv1_power',           'I16',   'kW', 1000,    0, 186, 1),
            Parameter('pv2_power',           'I16',   'kW', 1000,    0, 187, 1),
            Parameter('battery_power',       'I16',   'kW', 1000,    0, 190, 1),
        ])
