#!env/bin/python -u
# the line above disables stdout/stderr buffering

import datetime
import logging
import signal

import clock
import deye
import influxdb
import meters
import modbus
import persistence
import raspberry_pi_4 as rasp

sampling_period = 30  # seconds

# device codes -- should be unique
meter_x_name = 'meter-x'
inverter_name = 'inverter'
raspberry_name = 'raspberry'

# influxdb webapi
api_base_uri = 'http://127.0.0.1:8086'
api_token = '****'
api_organization = 'home'
api_bucket = 'raw'
api_measurement = 'solarmon'

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
    '''
    Queries the given device.

    Return a list of values, one for each parameter returned by the
    `params` method. `None` is used as NULL to point out the absence
    of the value of a parameter.
    '''
    try:
        data = [None if x == '' else x for x in device.read()]
    except Exception as e:
        data = [None] * len(device.params())
        logging.error('Could not read from "%s", reason: %s', device.name, e)
        logging.info('Reconfiguring device after a bad response...')
        device.reconfigure()
    return data


if __name__ == '__main__':

    logging.basicConfig(
        filename='/var/log/solarmon.log',
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S')
    logging.info('Booting...')

    try:
        rs485 = modbus.UsbRtuAdapter('/dev/ttyUSB_RS485', delay_between_reads=3)
        rs485.connect()

        input_devices = [
            rasp.RaspberryPi4(raspberry_name),
            deye.Inverter(inverter_name, rs485,  1),
#            meters.SDM120M(meter_x_name, rs485, 11),
        ]

        qualified_param_names = [
            '{}.{}'.format(d.name, r.name)
                for d in input_devices for r in d.params()]

        output_devices = [
            influxdb.InfluxDB(
                api_base_uri,
                api_token,
                api_organization,
                api_bucket,
                api_measurement),
            persistence.CsvFile('CSV', csv_file_path(), qualified_param_names),
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
        rs485.disconnect()
        logging.info('Exiting...')
    except:
        logging.exception('An unexpected fatal error occoured, exiting...')
