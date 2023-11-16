import unittest

from solarmon.influxdb import quote_string


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
        