#!env/bin/python -u
# the line above disables stdout/stderr buffering

import datetime
import logging
import signal
import time

import clock
import daikin
import emon
import meters
import modbus
import persistence

sampling_period = 30  # seconds

# device codes -- should be unique
meter_1_name = 'house'
meter_2_name = 'heat-pump'
meter_3_name = 'pv'
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


def read_from(device):
    try:
        data = [None if x == '' else x for x in device.peek()]
    except Exception as e:
        data = [None] * len(device.registers())
        logging.error('Could not read from "%s", reason: %s', device.name, e)
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

    try:
        rs485_bus = modbus.UsbRtuAdapter('/dev/ttyUSB_RS485', delay_between_reads=3)
        can_bus = daikin.SerialConnection('/dev/ttyUSB_HSCAN', 38400)

        rs485_bus.connect()
        can_bus.connect()

        input_devices = [
            meters.SDM120M(meter_1_name, rs485_bus, 31),
            meters.SDM120M(meter_2_name, rs485_bus, 32),
            meters.SDM120M(meter_3_name, rs485_bus, 33),
            daikin.Altherma(heat_pump_name, can_bus),
        ]

        qualified_register_names = ['{}.{}'.format(d.name, r.name)
                                    for d in input_devices for r in d.registers()]

        output_devices = [
            emon.EmonCMS(api_base_uri, api_key),
#            persistence.CsvFile('CSV', csv_file_path(), qualified_register_names),
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
                    logging.error('Could not write to "%s", reason: %s',
                                  device.name, e)

        logging.info('Shutting down...')
        rs485_bus.disconnect()
        can_bus.disconnect()
        logging.info('Exiting...')
    except:
        logging.exception('An unexpected fatal error occoured, exiting...')
