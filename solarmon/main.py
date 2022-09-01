#!env/bin/python -u
# the line above disables stdout/stderr buffering

import datetime
import logging
import signal

import clock
import emon
import huawei_sun2000
import meters
import modbus
import persistence

sampling_period = 15 # seconds

# huawei modbus
timeout = 5

# emoncms webapi
api_base_uri = 'http://127.0.0.1'
api_key = '92361dc1aacccbed7c284d6387bf9b54'
dongle_node_number = 101
inverter_node_number = 102
heat_pump_meter_node_number = 103

# csv
save_to_csv = False

def csv_file_path():
    return 'huawei_sun2000_{}.csv'.format(
            datetime.datetime.now().strftime('%Y%m%d%H%M%S'))


class ShutdownRequest:

    def __init__(self):
        self.should_exit = False
        signal.signal(signal.SIGINT, self._exit)
        signal.signal(signal.SIGTERM, self._exit)

    def _exit(self, *args):
        logging.info('Received a shutdown request...')
        self.should_exit = True


if __name__ == '__main__':

    logging.basicConfig(
            filename='/var/log/huawei_sun2000.log',
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S')
    logging.info('Booting...')

    emoncms = emon.EmonCMS(api_base_uri, api_key)

    # inverter direct access: '192.168.200.1', '6607', 0
    huawei_wifi = huawei_sun2000.HuaweiWifi('192.168.0.11', '502')
    dongle = huawei_sun2000.Dongle(huawei_wifi, 100, timeout)
    inverter = huawei_sun2000.Inverter(huawei_wifi, 1, timeout)

    usb_adapter = modbus.UsbRtuAdapter('/dev/ttyUSB0')
    heat_pump_meter = meters.JSY_MK_323(usb_adapter, 1)

    huawei_wifi.connect()
    usb_adapter.connect()

    dongle_register_names = [x.name for x in dongle.registers()]
    inverter_register_names = [x.name for x in inverter.registers()]
    heat_pump_register_names = [x.name for x in heat_pump_meter.registers()]

    exit_guard = ShutdownRequest()
    timer = clock.Timer(sampling_period)

    if save_to_csv:
        csv_file = persistence.CsvFile(csv_file_path())
        csv_file.write_heading(
            ['local_time'] + \
            dongle_register_names + \
            inverter_register_names + \
            heat_pump_register_names)
    else:
        csv_file = None

    while not exit_guard.should_exit:
        timer.wait_next_tick(abort_guard=lambda: exit_guard.should_exit)

        try:
            dongle_data = dongle.peek()
        except Exception as e:
            dongle_data = [''] * len(dongle_register_names)
            logging.error('Could not read dongle, reason: {}'.format(e))
            logging.info('Reconnecting after a bad TCP response...')
            huawei_wifi.reconnect()

        try:
            inverter_data = inverter.peek()
        except Exception as e:
            inverter_data = [''] * len(inverter_register_names)
            logging.error('Could not read inverter, reason: {}'.format(e))
            logging.info('Reconnecting after a bad TCP response...')
            huawei_wifi.reconnect()

        try:
            heat_pump_meter_data = heat_pump_meter.peek()
        except Exception as e:
            heat_pump_meter_data = [''] * len(heat_pump_meter_register_names)
            logging.error('Could not read heat pump, reason: {}'.format(e))
            logging.info('Reconnecting after a bad USB response...')
            usb_adapter.reconnect()

        try:
            emoncms.send(
                zip(dongle_register_names, dongle_data),
                dongle_node_number)
            emoncms.send(
                zip(inverter_register_names, inverter_data),
                inverter_node_number)
            emoncms.send(
                zip(heat_pump_register_names, heat_pump_meter_data),
                heat_pump_meter_node_number)
        except Exception as e:
            logging.error('Could not post to EmonCMS, reason: {}'.format(e))

        if csv_file:
            try:
                csv_file.write_values(
                        [datetime.datetime.now().isoformat()] + \
                        dongle_data + inverter_data + heat_pump_meter_data)
            except Exception as e:
                logging.error('Could not write to CSV, reason: {}'.format(e))

    logging.info('Shutting down...')
    huawei_wifi.disconnect()
    usb_adapter.disconnect()
    logging.info('Exiting...')
