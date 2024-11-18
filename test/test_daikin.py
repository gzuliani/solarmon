import unittest

from solarmon.daikin import *


class TestPacket(unittest.TestCase):
    def test_packets_are_made_of_14_bytes(self):
        with self.assertRaises(RuntimeError):
            Packet(b'0123456789ABC')
        with self.assertRaises(RuntimeError):
            Packet(b'0123456789ABCDE')

    def test_responses_have_an_ascii_2_in_second_position(self):
        frame = [0] * 14
        for i in range(0, 256):
            frame[1] = i
            p = Packet(bytes(frame))
            self.assertEqual(p.is_response, i == ord('2'))

    def test_8_bit_param_ids_are_at_position_4(self):
        p = Packet(b'00005A00000000')
        self.assertEqual(p.id, b'5A')

    def test_16_bit_param_ids_are_at_position_6(self):
        p = Packet(b'0000FA80D30000')
        self.assertEqual(p.id, b'80D3')

    def test_value_for_8_bit_params_are_at_position_6(self):
        p = Packet(b'00005A7C290000')
        self.assertEqual(p.id, b'5A')
        self.assertEqual(p.value, b'7C29')

    def test_value_for_8_bit_params_are_at_position_10(self):
        p = Packet(b'0000FA80D3F64E')
        self.assertEqual(p.id, b'80D3')
        self.assertEqual(p.value, b'F64E')


class TestParameter(unittest.TestCase):
    REQUEST = b'6100FA0A0C0000'

    def test_param_attributes_are_persistent(self):
        p = Parameter('name', 'unit', 'header', self.REQUEST)
        self.assertEqual(p.name, 'name')
        self.assertEqual(p.unit, 'unit')
        self.assertEqual(p.header, 'header')

    def test_param_id_is_extracted_from_the_request(self):
        p = Parameter('name', 'unit', 'header', b'00000C00000000')
        self.assertEqual(p.id, b'0C')
        p = Parameter('name', 'unit', 'header', b'0000FA0A0C0000')
        self.assertEqual(p.id, b'0A0C')

    def test_decoding_of_the_most_significant_byte(self):
        p = MSB('name', 'unit', 'header', self.REQUEST)
        self.assertEqual(p.decode(b'0000'),   0)
        self.assertEqual(p.decode(b'7FFF'), 127)
        self.assertEqual(p.decode(b'8000'), 128)
        self.assertEqual(p.decode(b'8001'), 128)
        self.assertEqual(p.decode(b'FFFF'), 255)

    def test_decoding_of_integral_values(self):
        p = INT('name', 'unit', 1, 'header', self.REQUEST)
        self.assertEqual(p.decode(b'0000'),      0)
        self.assertEqual(p.decode(b'7FFF'),  32767)
        self.assertEqual(p.decode(b'8000'), -32768)
        self.assertEqual(p.decode(b'8001'), -32767)
        self.assertEqual(p.decode(b'FFFF'),     -1)

    def test_decoding_of_floating_point_values(self):
        p = FLT('name', 'unit', 1, 'header', self.REQUEST)
        self.assertEqual(p.decode(b'0000'),      0.)
        self.assertEqual(p.decode(b'7FFF'),  32767.)
        self.assertEqual(p.decode(b'8000'), -32768.)
        self.assertEqual(p.decode(b'8001'), -32767.)
        self.assertEqual(p.decode(b'FFFF'),     -1.)

    def test_divisor(self):
        int_1 = INT('name', 'unit', 1, 'header', self.REQUEST)
        int_2 = INT('name', 'unit', 2, 'header', self.REQUEST)
        int_5 = INT('name', 'unit', 5, 'header', self.REQUEST)
        self.assertAlmostEqual(int_1.decode(b'0005'), 5)
        self.assertAlmostEqual(int_2.decode(b'0005'), 2)
        self.assertAlmostEqual(int_5.decode(b'0005'), 1)
        flt_1 = FLT('name', 'unit', 1, 'header', self.REQUEST)
        flt_5 = FLT('name', 'unit', 5, 'header', self.REQUEST)
        flt_2 = FLT('name', 'unit', 2, 'header', self.REQUEST)
        self.assertAlmostEqual(flt_1.decode(b'0005'), 5.0)
        self.assertAlmostEqual(flt_2.decode(b'0005'), 2.5)
        self.assertAlmostEqual(flt_5.decode(b'0005'), 1.0)
