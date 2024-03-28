import unittest

import os

from osmer_fvg import StationXmlData

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestStationXmlData(unittest.TestCase):

    def test_hourly_data_parsing(self):
        with open(os.path.join(THIS_DIR, 'data/UDI.xml')) as f:
            data = StationXmlData(f.read()).hourly_data()
            self.assertEqual(data['observation_time'], '19/12/2023 13.00 UTC')
            self.assertAlmostEqual(data['t180'], 14.8)
            self.assertAlmostEqual(data['rg'], 1083)
            self.assertAlmostEqual(data['rh'], 46)
            self.assertAlmostEqual(data['press'], 1011.9)

    def test_partial_data_parsing(self):
        with open(os.path.join(THIS_DIR, 'data/UDI_partial.xml')) as f:
            station_data = StationXmlData(f.read())
            self.assertRaises(RuntimeError, station_data.hourly_data)
