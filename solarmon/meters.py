from modbus import HoldingRegisters, InputRegisters, I16, U16, U32, F32


class JSY_MK_323(HoldingRegisters):

    def __init__(self, name, connection, addr):
        super().__init__(name, connection, addr)
        self._add_param_array([
            U16('V-L1',                   'V',  100, 0, 0x0048), # Phase A voltage
            # the following register actually has unit 'W' and gain 1
            U16('P-L1',                  'kW', 1000, 0, 0x004a), # A phase active power
            U32('E-L1-forward-total',   'kWh',  800, 0, 0x004b), # A-phase active energy (forward)
            U32('E-L1-reverse-total',   'kWh',  800, 0, 0x004e), # A-phase active energy (reverse)
            # the following register actually has unit 'W' and gain 1
            U16('V-L2',                   'V',  100, 0, 0x0051), # Phase B voltage
            U16('P-L2',                  'kW', 1000, 0, 0x0053), # B phase active power
            U32('E-L2-forward-total',   'kWh',  800, 0, 0x0054), # B-phase active energy (forward)
            U32('E-L2-reverse-total',   'kWh',  800, 0, 0x0057), # B-phase active energy (reverse)
            U16('V-L3',                   'V',  100, 0, 0x005a), # Phase C voltage
            # the following register actually has unit 'W' and gain 1
            U16('P-L3',                  'kW', 1000, 0, 0x005c), # C phase active power
            U32('E-L3-forward-total',   'kWh',  800, 0, 0x005d), # C-phase active energy (forward)
            U32('E-L3-reverse-total',   'kWh',  800, 0, 0x0060), # C-phase active energy (reverse)
            U32('E-forward-total',      'kWh',  800, 0, 0x0063), # Three-phase active total electric energy (forward)
            U32('E-reverse-total',      'kWh',  800, 0, 0x0066), # Three-phase active total electric energy (reverse)
        ])


class DDS238_1_ZN(HoldingRegisters):

    def __init__(self, name, connection, addr):
        super().__init__(name, connection, addr)
        self._add_param_array([
            U32('E-reverse-total',      'kWh',  100, 0, 0x0008), # Curent import energy
            U32('E-forward-total',      'kWh',  100, 0, 0x000a), # Curent import energy
            U16('V',                      'V',   10, 0, 0x000c), # Voltage
            # the following register actually has unit 'W' and gain 1
            I16('P',                     'kW', 1000, 0, 0x000e), # Active power
        ])


class SDM120M(InputRegisters):

    def __init__(self, name, connection, addr):
        super().__init__(name, connection, addr)
        self._add_param_array([
            F32('voltage',                'V',    1, 0, 0x0000), # Voltage
            F32('current',                'A',    1, 0, 0x0006), # Current
            # the following register actually has unit 'W'
            F32('active-power',          'kW', 1000, 0, 0x000c), # Active Power
            F32('frequency',             'Hz',    1, 0, 0x0046), # Frequency
            F32('import-active-energy', 'kWh',    1, 0, 0x0048), # Import Active Energy
            F32('export-active-energy', 'kWh',    1, 0, 0x004a), # Export Active Energy
        ])
        self._add_sparse_params([
            F32('total-active-energy',  'kWh',    1, 0, 0x0156), # Total Active Energy
        ])
