from modbus import HoldingRegisters, I16, U16


class Qword:

    def __init__(self, name, hihi_addr, hilo_addr, lohi_addr, lolo_addr):
        self.name = name
        self.regs = [hihi_addr, hilo_addr, lohi_addr, lolo_addr]

    def decode(self, values):
        assert len(values) == len(self.regs)
        result = 0
        for i, value in enumerate(values):
            result = result * 65536 + value
        return result


class QwordLE(Qword):

    def __init__(self, name, addr):
        super().__init__(name, addr + 3, addr + 2, addr + 1, addr)


class B64(QwordLE):

    def __init__(self, name, addr):
        super().__init__(name, addr)
        self.type = 'bit_field'


class Inverter(HoldingRegisters):

    def __init__(self, name, connection, addr):
        super().__init__(name, connection, addr)
        self._add_param_array([
            U16('run_state',               '',    1,    0,  59),
            U16('grid_frequency',        'Hz',  100,    0,  79),
            U16('heat_sink_temp',        '°C',   10, 1000,  90),
            U16('igbt_module_temp',      '°C',   10, 1000,  91),
            U16('environment_temp',      '°C',   10, 1000,  95),
        ])
        self._add_param_array([
            B64('fault_code',                              103),
            U16('pv1_voltage',            'V',   10,    0, 109),
            U16('pv1_current',            'A',   10,    0, 110),
            U16('pv2_voltage',            'V',   10,    0, 111),
            U16('pv2_current',            'A',   10,    0, 112),
            U16('grid_v_l1_n',            'V',   10,    0, 150),
            U16('inverter_v_l1_n',        'V',   10,    0, 154),
            U16('load_v_l1',              'V',   10,    0, 157),
#            I16('micro_inverter_power',  'kW', 1000,    0, 166),
            I16('internal_ct_l1_power',  'kW', 1000,    0, 167),
            I16('grid_power',            'kW', 1000,    0, 169),
            I16('external_ct_l1_power',  'kW', 1000,    0, 170),
#            I16('grid_ct_power',         'kW', 1000,    0, 172),
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
            I16('battery_current',        'A',  100,    0, 191),
        ])
