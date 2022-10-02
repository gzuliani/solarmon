#!env/bin/python -u
# the line above disables stdout/stderr buffering

import datetime
import logging
import signal
import time

import clock
import emon
import huawei_sun2000
import meters
import modbus
import persistence

sampling_period = 30 # seconds

# huawei modbus parameters
timeout = 5

# device codes -- should be unique
inverter_name = 'inverter'
heat_pump_meter_name = 'heat-pump'
old_pv_meter_name = 'old-pv'
single_phase_load_meter_name = 'house'

# emoncms webapi
api_base_uri = 'http://127.0.0.1'
api_key = '92361dc1aacccbed7c284d6387bf9b54'

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


def read_from(device):
    try:
        data = device.peek()
    except Exception as e:
        data = [''] * len(device.registers())
        logging.error('Could not read {}, reason: {}'.format(device.name, e))
        logging.info('Reconnecting after a bad response...')
        device.connection.reconnect()
    return data


if __name__ == '__main__':

    logging.basicConfig(
            filename='/var/log/solarmon.log',
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S')
    logging.info('Booting...')

    huawei_wifi = huawei_sun2000.HuaweiWifi('192.168.200.1', '6607')
    usb_adapter = modbus.UsbRtuAdapter('/dev/ttyUSB0', delay_between_reads = 1)

    huawei_wifi.connect()
    usb_adapter.connect()

    input_devices = [
        huawei_sun2000.Inverter(inverter_name, huawei_wifi, 0, timeout),
        meters.JSY_MK_323(heat_pump_meter_name, usb_adapter, 22),
        meters.DDS238_1_ZN(old_pv_meter_name, usb_adapter, 21),
        meters.DDS238_1_ZN(single_phase_load_meter_name, usb_adapter, 23),
    ]

    qualified_register_names = ['{}.{}'.format(d.name, r.name)
                                for d in input_devices for r in d.registers()]

    output_devices = [
        emon.EmonCMS(api_base_uri, api_key),
#        persistence.CsvFile('CSV', csv_file_path(), qualified_register_names),
    ]

    exit_guard = ShutdownRequest()
    timer = clock.Timer(sampling_period)

    while not exit_guard.should_exit:
        timer.wait_next_tick(abort_guard=lambda: exit_guard.should_exit)

        data = [(x, read_from(x)) for x in input_devices]

        for device in output_devices:
            try:
                device.write(data)
            except Exception as e:
                logging.error('Could not write to {}, reason: {}'.format(
                        device.name, e))

    logging.info('Shutting down...')
    huawei_wifi.disconnect()
    usb_adapter.disconnect()
    logging.info('Exiting...')
