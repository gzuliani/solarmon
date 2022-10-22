from modbus import HoldingRegisters, InputRegisters, Register


class JSY_MK_323(HoldingRegisters):

    def __init__(self, name, connection, addr, timeout=1):
        HoldingRegisters.__init__(self, name, connection, addr, timeout)
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


class DDS238_1_ZN(HoldingRegisters):

    def __init__(self, name, connection, addr, timeout=1):
        HoldingRegisters.__init__(self, name, connection, addr, timeout)
        self._add_register_array([
            Register('E-reverse-total', 'U32', 'kWh',  100, 0x0008, 2), # Curent import energy
            Register('E-forward-total', 'U32', 'kWh',  100, 0x000A, 2), # Curent import energy
            Register('V',               'U16',   'V',   10, 0x000C, 1), # Voltage
            # the following register actually has unit 'W' and gain 1
            Register('P',               'I16',  'kW', 1000, 0x000E, 1), # Active power
        ])


class SDM120M(InputRegisters):

    def __init__(self, name, connection, addr, timeout=1):
        InputRegisters.__init__(self, name, connection, addr, timeout)
        self._add_register_array([
            Register('voltage',                 'F32',   'V',     1, 0x0000, 2), # Voltage
            # the following register actually has unit 'W'
            Register('active-power',            'F32',  'kW',  1000, 0x000C, 2), # Active Power
            Register('frequency',               'F32',  'Hz',     1, 0x0046, 2), # Frequency
            Register('import-active-energy',    'F32', 'kWh',     1, 0x0048, 2), # Import Active Energy
            Register('export-active-energy',    'F32', 'kWh',     1, 0x004A, 2), # Export Active Energy
        ])
        self._add_sparse_registers([
            Register('total-active-energy',     'F32', 'kWh',     1, 0x0156, 2), # Total Active Energy
        ])
