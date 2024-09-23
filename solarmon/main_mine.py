#!env/bin/python -u
# the line above disables stdout/stderr buffering

import datetime
import json
import logging.config
import sys

import clock
import deye
import influxdb
import meters
import modbus
import osmer_fvg
import persistence
import raspberry_pi_4 as rasp
import sample
import ui


sampling_period = 30  # seconds

# influxdb webapi
api_base_uri = 'http://127.0.0.1:8086'
api_token = '****'
api_organization = 'home'
api_bucket = 'raw_data'
api_measurement = 'solarmon'

# csv
def csv_file_path():
    return 'solarmon_{}.csv'.format(
        datetime.datetime.now().strftime('%Y%m%d%H%M%S'))


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
        rs485_adapter = modbus.UsbRtuAdapter(
            '/dev/ttyUSB_RS485', timeout=1, delay_between_reads=3)
        rs485_adapter.connect()

        input_devices = [
            rasp.RaspberryPi4('rasp', num_of_wifi_ifaces=1),
            deye.Inverter('inverter', rs485_adapter,  1),
            meters.SDM120M('2nd-floor', rs485_adapter, 10),
            meters.SDM120M('gnd-floor', rs485_adapter, 11),
            meters.SDM120M('air-cond', rs485_adapter, 12),
            # meters.SDM120M('ind-hob', rs485_adapter, 13),
            osmer_fvg.OsmerFvg('osmer', 'UDI'), # keep it as the last one!
        ]

        output_devices = [
            influxdb.InfluxDB(
                api_base_uri,
                api_token,
                api_organization,
                api_bucket,
                api_measurement),
            # persistence.CsvFile('CSV', csv_file_path()),
        ]

        exit_guard = ui.ShutdownRequest()
        timer = clock.Timer(sampling_period)

        while not exit_guard.should_exit:
            timer.wait_next_tick(abort_guard=lambda: exit_guard.should_exit)

            samples = [sample.read_from(x) for x in input_devices]

            for device in output_devices:
                try:
                    device.write(samples)
                except Exception as e:
                    logging.error('Could not write to "%s", reason: %s',
                                  device.name, e)

        logging.info('Shutting down...')
        rs485_adapter.disconnect()
        logging.info('Exiting...')
    except:
        logging.exception('An unexpected fatal error occoured, exiting...')
