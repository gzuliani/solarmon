from modbus import Device, Register


class JSY_MK_323(Device):

    def __init__(self, connection, addr, timeout=1):
        Device.__init__(self, connection, addr, timeout)
        self._add_register_array([
            # the following register actually has unit 'W' and gain 1
            Register('a_phase_active_power', 'U16',  'kW', 1000, 0x004A, 1), # A phase active power
            # the following register actually has unit 'W' and gain 1
            Register('b_phase_active_power', 'U16',  'kW', 1000, 0x0053, 1), # B phase active power
            # the following register actually has unit 'W' and gain 1
            Register('c_phase_active_power', 'U16',  'kW', 1000, 0x005C, 1), # C phase active power
            Register('forward_energy',       'U32', 'kWh',  800, 0x0063, 2), # Three-phase active total electric energy (forward)
        ])


class DDS238_1_ZN(Device):

    def __init__(self, connection, addr, timeout=1):
        Device.__init__(self, connection, addr, timeout)
        self._add_register_array([
            Register('total_kwh',    'U32', 'kWh',  100, 0x0000, 2),
            Register('export_kwh',   'U32', 'kWh',  100, 0x0008, 2),
            Register('import_kwh',   'U32', 'kWh',  100, 0x000A, 2),
            # the following register actually has unit 'W' and gain 1
            Register('active_power', 'I16',  'kW', 1000, 0x000E, 1), # Active power
        ])
