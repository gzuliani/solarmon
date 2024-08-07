#!env/bin/python -u
# the line above disables stdout/stderr buffering

import datetime
import json
import logging.config
import signal
import sys

import clock
import daikin
import emon
import huawei_sun2000
import meters
import modbus
import persistence

sampling_period = 30 # seconds

# device codes -- should be unique
inverter_name = 'inverter'
heat_pump_meter_name = 'heat-pump'
old_pv_meter_name = 'old-pv'
house_meter_name = 'house'
heat_pump_name = 'daikin'

# emoncms webapi
api_base_uri = 'http://127.0.0.1'
api_key = '****'

# csv
def csv_file_path():
    return 'solarmon_{}.csv'.format(
            datetime.datetime.now().strftime('%Y%m%d%H%M%S'))


class ShutdownRequest:

    def __init__(self):
        self.should_exit = False
        signal.signal(signal.SIGINT, self._exit)
        signal.signal(signal.SIGTERM, self._exit)

    def _exit(self, *args):
        logging.info('Received a shutdown request...')
        self.should_exit = True


class Sample:

    def __init__(self, device):
        self.device = device
        self.values = [None] * len(device.params())
        self.exception = None

    def load(self, values):
        self.values = [None if x == '' else x for x in values]

    def invalidate(self, exception):
        self.exception = exception

    def is_error(self):
        return self.exception is not None

    def error(self):
        return str(self.exception)


def read_from(device):
    sample = Sample(device)
    try:
        sample.load(device.read())
    except Exception as e:
        sample.invalidate(e)
        logging.error('Could not read from "%s", reason: %s', device.name, e)
        logging.info('Reconfiguring device after a bad response...')
        device.reconfigure()
    return sample


if __name__ == '__main__':

    if len(sys.argv) > 1:
        config_file_path = sys.argv[1]
    else:
        config_file_path = '/etc/solarmon.conf'

    with open(config_file_path) as f:
        config = json.load(f)

    logging.config.dictConfig(config['log'])
    logging.info('Booting...')

    try:
        huawei_wifi = huawei_sun2000.HuaweiWifi(
            '192.168.200.1', '6607', timeout=5)
        rs485_adapter = modbus.UsbRtuAdapter(
            '/dev/ttyUSB_RS485', timeout=1, delay_between_reads=3)
        can_adapter = daikin.UsbCanAdapter('/dev/ttyUSB_HSCAN', 38400)

        huawei_wifi.connect()
        rs485_adapter.connect()
        can_adapter.connect()

        input_devices = [
            huawei_sun2000.Inverter(inverter_name, huawei_wifi, 0),
            meters.JSY_MK_323(heat_pump_meter_name, rs485_adapter, 22),
            meters.DDS238_1_ZN(old_pv_meter_name, rs485_adapter, 21),
            meters.DDS238_1_ZN(house_meter_name, rs485_adapter, 23),
            daikin.Altherma(heat_pump_name, can_adapter),
        ]

        qualified_param_names = [
            '{}.{}'.format(d.name, r.name)
                    for d in input_devices for r in d.params()]

        output_devices = [
            emon.EmonCMS(api_base_uri, api_key),
            # persistence.CsvFile('CSV', csv_file_path(), qualified_param_names),
        ]

        exit_guard = ShutdownRequest()
        timer = clock.Timer(sampling_period)

        while not exit_guard.should_exit:
            timer.wait_next_tick(abort_guard=lambda: exit_guard.should_exit)

            samples = [read_from(x) for x in input_devices]

            for device in output_devices:
                try:
                    device.write(samples)
                except Exception as e:
                    logging.error('Could not write to "%s", reason: %s',
                            device.name, e)

        logging.info('Shutting down...')
        huawei_wifi.disconnect()
        rs485_adapter.disconnect()
        can_adapter.disconnect()
        logging.info('Exiting...')
    except:
        logging.exception('An unexpected fatal error occoured, exiting...')
