import unittest

from solarmon.modbus import *


class MockResponse:

    def __init__(self, addr, count):
        self.registers = [
            0x80c5,  # 0x0000
            0x946e,  # 0x0001
            0x53e9,  # 0x0002
            0x52d2,  # 0x0003
            0x072a,  # 0x0004
            0xf5ea,  # 0x0005
            0x88a5,  # 0x0006
            0x6644,  # 0x0007
            0x2592,  # 0x0008
            0x4aa4,  # 0x0009
            0xf7f6,  # 0x000a
            0x2f29,  # 0x000b
            0x1527,  # 0x000c
            0x5fee,  # 0x000d
            0x3275,  # 0x000e
            0x340a,  # 0x000f
            0x5f53,  # 0x0010
            0x6f6c,  # 0x0011
            0x6172,  # 0x0012
            0x4d4f,  # 0x0013
            0x4e5f,  # 0x0014
            0x2a54,  # 0x0015
            0x4553,  # 0x0016
            0x542a,  # 0x0017
        ][addr : addr + count]

    def isError(self):
        return False


class MockConnection:

    def __init__(self):
        self.read_input_registers_called = False
        self.read_holding_registers_called = False

    def read_input_registers(self, addr, count, timeout, unit):
        self.read_input_registers_called = True
        return MockResponse(addr, count)

    def read_holding_registers(self, addr, count, timeout, unit):
        self.read_holding_registers_called = True
        return MockResponse(addr, count)


class MockReadOnlyDevice(InputRegisters):

    def __init__(self, connection):
        super().__init__('name', connection, 'addr', timeout=0)
        self._add_param_array([U16('', '', 1, 0, 0)])


class MockReadWriteDevice(HoldingRegisters):

    def __init__(self, connection):
        super().__init__('name', connection, 'addr', timeout=0)
        self._add_param_array([U16('', '', 1, 0, 0)])


class MockDevice(HoldingRegisters):

    def __init__(self, connection):
        super().__init__('name', connection, 'addr', timeout=0)
        self._add_param_array([
            I16('p01', '', 1, 0, 0),
            U16('p02', '', 1, 0, 2),
            U32('p03', '', 1, 0, 3),
            I32('p04', '', 1, 0, 7),
            SignedLongBE('p05', '', 1, 0, 7),
            SignedLongLE('p06', '', 1, 0, 7),
            F32('p07', '', 1, 0, 9),
            ASC('p08', 16, 5),
        ])
        self._add_sparse_params([
            U32('p09', '', 1, 0, 12),
            UnsignedLongBE('p10', '', 1, 0, 12),
            UnsignedLongLE('p11', '', 1, 0, 12),
            SignedLong('p12', '', 1, 0, 3, 8),
            ASC('p13', 21, 3),
            UnsignedLong('p14', '', 1, 0, 5, 1),
        ])


class TestParameter(unittest.TestCase):

    def test_name_is_persistent(self):
        p = Parameter('name', [])
        self.assertEqual(p.name, 'name')

    def test_unit_is_persistent_in_numeric_parameters(self):
        p = Number('name', 'unit', None, None, None)
        self.assertEqual(p.name, 'name')
        self.assertEqual(p.unit, 'unit')

    def test_decoding_of_16_bit_signed_int(self):
        p = I16('', '', 1, 0, 0)
        self.assertEqual(p.decode([0x0000]),      0)
        self.assertEqual(p.decode([0x7fff]),  32767)
        self.assertEqual(p.decode([0x8000]), -32768)
        self.assertEqual(p.decode([0x8001]), -32767)
        self.assertEqual(p.decode([0xffff]),     -1)

    def test_decoding_of_16_bit_unsigned_int(self):
        p = U16('', '', 1, 0, 0)
        self.assertEqual(p.decode([0x0000]),     0)
        self.assertEqual(p.decode([0x7fff]), 32767)
        self.assertEqual(p.decode([0x8000]), 32768)
        self.assertEqual(p.decode([0x8001]), 32769)
        self.assertEqual(p.decode([0xffff]), 65535)

    def test_decoding_of_32_bit_signed_int(self):
        p = I32('', '', 1, 0, 0)
        self.assertEqual(p.decode([0x0000, 0x0000]),           0)
        self.assertEqual(p.decode([0x7fff, 0xffff]),  2147483647)
        self.assertEqual(p.decode([0x8000, 0x0000]), -2147483648)
        self.assertEqual(p.decode([0x8000, 0x0001]), -2147483647)
        self.assertEqual(p.decode([0xffff, 0xffff]),          -1)

    def test_decoding_of_32_bit_unsigned_int(self):
        p = U32('', '', 1, 0, 0)
        self.assertEqual(p.decode([0x0000, 0x0000]),          0)
        self.assertEqual(p.decode([0x7fff, 0xffff]), 2147483647)
        self.assertEqual(p.decode([0x8000, 0x0000]), 2147483648)
        self.assertEqual(p.decode([0x8000, 0x0001]), 2147483649)
        self.assertEqual(p.decode([0xffff, 0xffff]), 4294967295)

    def test_decoding_of_32_bit_float(self):
        p = F32('', '', 1, 0, 0)
        self.assertAlmostEqual(p.decode([0x3e20, 0x0000]),  0.15625)
        self.assertAlmostEqual(p.decode([0x4146, 0x0000]), 12.37500)
        self.assertAlmostEqual(p.decode([0xc000, 0x0000]), -2.00000)

    def test_gain_and_bias(self):
        u16_1__0 = U16('', '', 1,  0, 0)
        u16_5_10 = U16('', '', 5, 10, 0)
        u16_2_m5 = U16('', '', 2, -5, 0)
        self.assertAlmostEqual(u16_1__0.decode([0x0005]),  5.0)
        self.assertAlmostEqual(u16_5_10.decode([0x0005]), -1.0)
        self.assertAlmostEqual(u16_2_m5.decode([0x0005]),  5.0)
        i32_1__0 = I32('', '', 1,  0, 0)
        i32_5_10 = I32('', '', 5, 10, 0)
        i32_2_m5 = I32('', '', 2, -5, 0)
        self.assertAlmostEqual(i32_1__0.decode([0x0000, 0x0005]),  5.0)
        self.assertAlmostEqual(i32_5_10.decode([0x0000, 0x0005]), -1.0)
        self.assertAlmostEqual(i32_2_m5.decode([0x0000, 0x0005]),  5.0)
        f32_1__0 = F32('', '', 1,  0, 0)
        f32_5_10 = F32('', '', 5, 10, 0)
        f32_2_m5 = F32('', '', 2, -5, 0)
        self.assertAlmostEqual(f32_1__0.decode([0x40a0, 0x0000]),  5.0)
        self.assertAlmostEqual(f32_5_10.decode([0x40a0, 0x0000]), -1.0)
        self.assertAlmostEqual(f32_2_m5.decode([0x40a0, 0x0000]),  5.0)


class TestDevice(unittest.TestCase):

    def test_read_only_devices_use_input_registers(self):
        connection = MockConnection()
        self.assertFalse(connection.read_input_registers_called)
        self.assertFalse(connection.read_holding_registers_called)
        device = MockReadOnlyDevice(connection)
        device.read()
        self.assertTrue(connection.read_input_registers_called)
        self.assertFalse(connection.read_holding_registers_called)

    def test_read_write_devices_use_holding_registers(self):
        connection = MockConnection()
        self.assertFalse(connection.read_input_registers_called)
        self.assertFalse(connection.read_holding_registers_called)
        device = MockReadWriteDevice(connection)
        device.read()
        self.assertFalse(connection.read_input_registers_called)
        self.assertTrue(connection.read_holding_registers_called)

    def test_parameter_decoding(self):
        connection = MockConnection()
        device = MockDevice(connection)
        data = device.read()
        self.assertEqual(data[ 0],     -32571.0)
        self.assertEqual(data[ 1],      21481.0)
        self.assertEqual(data[ 2], 1389496106.0)
        self.assertEqual(data[ 3], 1715742098.0)
        self.assertEqual(data[ 4], 1715742098.0)
        self.assertEqual(data[ 5],  630351428.0)
        self.assertEqual(data[ 6],    5405691.0)
        self.assertEqual(data[ 7], '_SolarMON_')
        self.assertEqual(data[ 8],  354901998.0)
        self.assertEqual(data[ 9],  354901998.0)
        self.assertEqual(data[10], 1609438503.0)
        self.assertEqual(data[11], 1389503890.0)
        self.assertEqual(data[12],     '*TEST*')
        self.assertEqual(data[13], 4125791342.0)
