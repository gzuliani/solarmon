import unittest

from solarmon.deye import *


class FaultCodes:

    def __init__(self):
        self._descriptions = {
             1: 'DC input polarity reverse fault',
             7: 'DC start failure',
            13: 'Working mode change',
            15: 'AC over current fault of software',
            16: 'AC leakage current fault',
            18: 'AC over current fault of hardware',
            20: 'DC over current fault of the hardware',
            21: 'Bus over current',
            22: 'Emergency stop',
            23: 'AC leak current or transient over current',
            24: 'DC insulation failure',
            26: 'DC busbar is unbalanced',
            29: 'Parallel CAN Bus fault',
            34: 'AC Overcurrent fault',
            35: 'No AC grid',
            41: 'Parallel system stop',
            42: 'AC line low voltage',
            46: 'backup battery fault',
            47: 'AC over frequency',
            48: 'AC lower frequency',
            55: 'DC busbar voltage is too high',
            56: 'DC busbar voltage is too low',
            58: 'BMS communication fault',
            62: 'DRM stop',
            63: 'ARC fault',
            64: 'Heat sink high temperature failure',
        }

    def description_of(self, code):
        return self._descriptions.get(code, 'N/A')

    def decode(self, mask):
        '''Fault codes are one plus the position of a set bit'''
        faults = []
        for i in range(64):
            if mask & (1 << i):
                faults.append(i + 1)
        return faults
        

class TestFaultCodes(unittest.TestCase):

    def setUp(self):
        self.fault_codes = FaultCodes()

    def test_no_fault(self):
        self.assertEqual(self.fault_codes.decode(0x0000000000000000), [])

    def test_fault_F01(self):
        self.assertEqual(self.fault_codes.decode(0x0000000000000001), [1])

    def test_fault_F55(self):
        self.assertEqual(self.fault_codes.decode(0x0040000000000000), [55])

    def test_fault_F64(self):
        self.assertEqual(self.fault_codes.decode(0x8000000000000000), [64])

    def test_faults_F05_F28_F47(self):
        self.assertEqual(self.fault_codes.decode(0x0000400008000010), [5, 28, 47])

    def test_description_of_an_unknown_code(self):
        self.assertEqual(self.fault_codes.description_of(99), 'N/A')

    def test_description_of_fault_F07(self):
        self.assertEqual(self.fault_codes.description_of(7), 'DC start failure')

    def test_description_of_fault_F34(self):
        self.assertEqual(self.fault_codes.description_of(34), 'AC Overcurrent fault')

    def test_description_of_fault_F55(self):
        self.assertEqual(self.fault_codes.description_of(55), 'DC busbar voltage is too high')


class TestQwordLE(unittest.TestCase):

    def test_decoding_of_a_dword(self):
        p = QwordLE('qword', 1)
        self.assertEqual(p.decode([0x0000, 0x0000, 0x0000, 0x0000]), 0x0000000000000000)
        self.assertEqual(p.decode([0x0000, 0x0000, 0x0000, 0x0001]), 0x0000000000000001)
        self.assertEqual(p.decode([0xcf2d, 0xc74b, 0xfa72, 0xa77f]), 0xcf2dc74bfa72a77f)
        self.assertEqual(p.decode([0xee5e, 0xcc3f, 0xc03f, 0x4e4c]), 0xee5ecc3fc03f4e4c)
        self.assertEqual(p.decode([0xffff, 0xffff, 0xffff, 0xffff]), 0xffffffffffffffff)
