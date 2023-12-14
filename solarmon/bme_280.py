import smbus2
import bme280


class Param:

    def __init__(self, name):
        self.name = name


class Bme280:

    def __init__(self, name, port, addr):
        self.name = name
        self._port = port
        self._addr = addr
        self._params = [Param(x) for x in ['temp', 'pressure', 'humidiy']]
        self.reconfigure()

    def reconfigure(self):
        self._bus = smbus2.SMBus(self._port)
        self._cal_data = bme280.load_calibration_params(self._bus, self._addr)

    def params(self):
        return self._params

    def read(self):
        data = bme280.sample(self._bus, self._addr, self._cal_data)
        return [data.temperature, data.pressure, data.humidity]
