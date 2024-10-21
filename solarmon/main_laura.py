#!env/bin/python -u
# the line above disables stdout/stderr buffering

import datetime
import json
import logging.config
import sys

import clock
import daikin
import deye
import emon
import meters
import modbus
import persistence
import raspberry_pi_4 as rasp
import sample
import ui


sampling_period = 30 # seconds

# device codes -- should be unique
meter_1_name = 'house'
meter_2_name = 'heat-pump'
meter_3_name = 'pv'
heat_pump_name = 'daikin'
inverter_name = 'inverter'

# emoncms webapi
api_base_uri = 'http://127.0.0.1'
api_key = '****'

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
        can_adapter = daikin.UsbCanAdapter('/dev/ttyUSB_HSCAN', 38400)

        rs485_adapter.connect()
        can_adapter.connect()

        input_devices = [
            rasp.RaspberryPi4('rasp', rasp.WifiIfaceCount(1)),
            deye.Inverter(inverter_name, rs485_adapter,  1),
            meters.SDM120M(meter_1_name, rs485_adapter, 31),
            meters.SDM120M(meter_2_name, rs485_adapter, 32),
            meters.SDM120M(meter_3_name, rs485_adapter, 33),
            daikin.Altherma(heat_pump_name, can_adapter),
        ]

        output_devices = [
            emon.EmonCMS(api_base_uri, api_key),
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
        can_adapter.disconnect()
        logging.info('Exiting...')
    except:
        logging.exception('An unexpected fatal error occoured, exiting...')
