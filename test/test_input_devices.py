import random
import unittest

import daikin
import deye
import huawei_sun2000
import meters


class MockModbusResponse:

    def __init__(self, addr, count):
        self.registers = [random.randrange(65536)] * count

    def isError(self):
        return False


class MockModbusProxy:

    def read_input_registers(self, addr, count, timeout, unit):
        self.read_input_registers_called = True
        return MockModbusResponse(addr, count)

    def read_holding_registers(self, addr, count, timeout, unit):
        self.read_holding_registers_called = True
        return MockModbusResponse(addr, count)


class MockCanBusProxy:

    def set_header(self, _):
        return b'OK\r'

    def send_request(self, request):
        response = list(request)
        response[1] = ord('2') # set the 'request' mark
        if request[4:6] == b'FA':
            value_pos = 10
        else:
            value_pos = 6
        value = '%04X' % random.getrandbits(16)
        for i in range(4):
            response[value_pos + i] = ord(value[i])
        return [bytes(response)]


class TestInputDevices(unittest.TestCase):

    def test_reading_from_input_devices_is_safe(self):
        modbus_proxy = MockModbusProxy()
        canbus_proxy = MockCanBusProxy()

        input_devices = [
            huawei_sun2000.Inverter('SUN2000', modbus_proxy, 0),
            meters.JSY_MK_323('JSY_MK_323', modbus_proxy, 1),
            meters.DDS238_1_ZN('DDS238_1_ZN', modbus_proxy, 2),
            meters.SDM120M('SDM120M', modbus_proxy, 3),
            deye.Inverter('DEYE', modbus_proxy,  4),
            daikin.Altherma('ALTHERMA', canbus_proxy),
        ]

        for _ in range(1000):
            for d in input_devices:
                d.read()
