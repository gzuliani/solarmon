from modbus import Device, Register


class JSY_MK_323(Device):

    def __init__(self, name, connection, addr, timeout=1):
        Device.__init__(self, name, connection, addr, timeout)
        self._add_register_array([
            Register('V-L1',                 'U16',   'V',  100, 0x0048, 1), # Phase A voltage
            # the following register actually has unit 'W' and gain 1
            Register('P-L1',                 'U16',  'kW', 1000, 0x004A, 1), # A phase active power
            Register('E-L1-forward-total',   'U32', 'kWh',  800, 0x004B, 2), # A-phase active energy (forward)
            Register('E-L1-reverse-total',   'U32', 'kWh',  800, 0x004E, 2), # A-phase active energy (reverse)
            # the following register actually has unit 'W' and gain 1
            Register('V-L2',                 'U16',   'V',  100, 0x0051, 1), # Phase B voltage
            Register('P-L2',                 'U16',  'kW', 1000, 0x0053, 1), # B phase active power
            Register('E-L2-forward-total',   'U32', 'kWh',  800, 0x0054, 2), # B-phase active energy (forward)
            Register('E-L2-reverse-total',   'U32', 'kWh',  800, 0x0057, 2), # B-phase active energy (reverse)
            Register('V-L3',                 'U16',   'V',  100, 0x005A, 1), # Phase C voltage
            # the following register actually has unit 'W' and gain 1
            Register('P-L3',                 'U16',  'kW', 1000, 0x005C, 1), # C phase active power
            Register('E-L3-forward-total',   'U32', 'kWh',  800, 0x005D, 2), # C-phase active energy (forward)
            Register('E-L3-reverse-total',   'U32', 'kWh',  800, 0x0060, 2), # C-phase active energy (reverse)
            Register('E-forward-total',      'U32', 'kWh',  800, 0x0063, 2), # Three-phase active total electric energy (forward)
            Register('E-reverse-total',      'U32', 'kWh',  800, 0x0066, 2), # Three-phase active total electric energy (reverse)
        ])

class DDS238_1_ZN(Device):

    def __init__(self, name, connection, addr, timeout=1):
        Device.__init__(self, name, connection, addr, timeout)
        self._add_register_array([
            Register('E-reverse-total', 'U32', 'kWh',  100, 0x0008, 2), # Curent import energy
            Register('E-forward-total', 'U32', 'kWh',  100, 0x000A, 2), # Curent import energy
            Register('V',               'U16',   'V',   10, 0x000C, 1), # Voltage
            # the following register actually has unit 'W' and gain 1
            Register('P',               'I16',  'kW', 1000, 0x000E, 1), # Active power
        ])
