import unittest

from solarmon.deye import B64, I16
from solarmon.influxdb import quote_string, LineProtocol
from solarmon.modbus import STR

class TestQuote(unittest.TestCase):
    def test_string_quoting_supports_the_empty_string(self):
        self.assertEqual(quote_string(''), '""')

    def test_string_quoting_preserves_inner_spaces(self):
        self.assertEqual(
            quote_string('Lorem ipsum dolor sit amet'),
            '"Lorem ipsum dolor sit amet"')

    def test_string_quoting_transforms_CR_LF_and_TAB_into_a_space(self):
        self.assertEqual(
            quote_string('Lorem\ripsum\ndolor\tsit amet'),
            '"Lorem ipsum dolor sit amet"')

    def test_string_quoting_collapse_multiple_spaces_into_one(self):
        self.assertEqual(
            quote_string('Lorem\r\nipsum   dolor\t sit      amet'),
            '"Lorem ipsum dolor sit amet"')

    def test_string_quoting_removes_any_leading_and_trailing_space(self):
        self.assertEqual(
            quote_string('  Lorem ipsum dolor sit amet\r\n'),
            '"Lorem ipsum dolor sit amet"')

    def test_string_quoting_escapes_backslashes(self):
        self.assertEqual(
            quote_string('Lorem\\ipsum dolor\\\\sit amet'),
            '"Lorem\\\\ipsum dolor\\\\\\\\sit amet"')

    def test_string_quoting_escapes_double_quotes(self):
        self.assertEqual(
            quote_string('Lorem \"ipsum\" dolor sit amet'),
            '"Lorem \\"ipsum\\" dolor sit amet"')

    def test_string_quoting_preserves_single_quotes(self):
        self.assertEqual(
            quote_string('Lorem ipsum \'dolor\' sit amet'),
            '"Lorem ipsum \'dolor\' sit amet"')

    def test_string_quoting_works_on_exception_messages(self):
        self.assertEqual(
            quote_string('Traceback (most recent call last):\n  File \"<stdin>\", line 1, in <module>\nNameError: name \'spam\' is not defined'),
            '"Traceback (most recent call last): File \\\"<stdin>\\\", line 1, in <module> NameError: name \'spam\' is not defined"')


class MockDevice:
    def __init__(self):
        self.name = 'inverter'
        self._params = [
            I16('voltage',       'V',  1, 0, 1),
            I16('current',       'A',  1, 0, 2),
            B64('fault_code',                3),
            I16('frequency',     'Hz', 1, 0, 2),
            STR('serial',              1,    2),]

    def params(self):
        return self._params


class MockSample:
    def __init__(self):
        self.device = MockDevice()
        self.values = [0x00dc, 0x000a, 0x0040000000000000, 0x0032, 'ABCD']
        self.exception = None


class MockSampleError:
    def __init__(self):
        self.exception = 'a \'quoted\' "string"'


class TestLineProtocol(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.protocol = LineProtocol('measurement')

    def test_encode_error(self):
        unit = 'inverter'
        code = 'READ_ERROR'
        detail = 'a \'quoted\' "string"'
        timestamp = 1710002529
        self.assertEqual(
            self.protocol.encode_error(unit, code, detail, timestamp),
            'measurement,source=program unit="inverter",code="READ_ERROR",detail="a \'quoted\' \\"string\\"" 1710002529')

    def test_encode_sample(self):
        sample = MockSample()
        timestamp = 1710015972
        self.assertEqual(
            self.protocol.encode_sample(sample, timestamp),
            'measurement,source=inverter voltage=220,current=10,fault_code=18014398509481984u,frequency=50,serial="ABCD" 1710015972')
