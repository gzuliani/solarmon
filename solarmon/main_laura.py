#!env/bin/python -u
# the line above disables stdout/stderr buffering

import datetime
import logging
import signal
import time

import clock
import emon
import meters
import modbus
import persistence

sampling_period = 30 # seconds

# device codes -- should be unique
meter_1_name = 'meter-1'
meter_2_name = 'meter-2'
meter_3_name = 'meter-3'

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

    usb_adapter = modbus.UsbRtuAdapter('/dev/ttyUSB0', delay_between_reads=3)

    usb_adapter.connect()

    input_devices = [
        meters.SDM120M(meter_1_name, usb_adapter, 31),
        meters.SDM120M(meter_2_name, usb_adapter, 32),
        meters.SDM120M(meter_3_name, usb_adapter, 33),
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
    usb_adapter.disconnect()
    logging.info('Exiting...')