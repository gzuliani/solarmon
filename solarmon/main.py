#!env/bin/python -u
# the line above disables stdout/stderr buffering

sampling_period = 30 # seconds

# huawei modbus
timeout = 5

# emoncms webapi
api_base_uri = 'http://127.0.0.1'
api_key = '92361dc1aacccbed7c284d6387bf9b54'
dongle_node_number = 101
inverter_node_number = 102
heat_pump_meter_node_number = 103

import datetime
import logging
import signal

import clock
import emon
import huawei_sun2000
import meters
import persistence


class ShutdownRequest:

    def __init__(self):
        self.should_exit = False
        signal.signal(signal.SIGINT, self._exit)
        signal.signal(signal.SIGTERM, self._exit)

    def _exit(self, *args):
        logging.info('Received shutdown request...')
        self.should_exit = True


if __name__ == '__main__':

    logging.basicConfig(
            filename='/var/log/huawei_sun2000.log',
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S')
    logging.info('Booting...')

    emoncms = emon.EmonCMS(api_base_uri, api_key)

    # use the `SeparateConnections` connection pool to connect directy
    # to the inverter, otherwise the dongle will be used as a proxy to it
    tcp_connection_pool = huawei_sun2000.SharedConnection() # This may throw!
    dongle = tcp_connection_pool.attach_to_dongle(timeout)
    inverter = tcp_connection_pool.attach_to_inverter(timeout)

    usb_connection = meters.USBConnection('/dev/ttyUSB0') # Could this throw?!
    usb_connection.connect()
    heat_pump_meter = usb_connection.attach_to_JSY_MK_323_meter(1)

    dongle_register_names = [x.name for x in dongle.registers()]
    inverter_register_names = [x.name for x in inverter.registers()]
    heat_pump_register_names = [x.name for x in heat_pump_meter.registers()]

    exit_guard = ShutdownRequest()
    timer = clock.Timer(sampling_period)

    csv_file = persistence.CsvFile('huawei_sun2000_{}.csv'.format(
            datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
    csv_file.write_heading(
            ['local_time'] + \
            dongle_register_names + \
            inverter_register_names + \
            heat_pump_register_names)

    while not exit_guard.should_exit:
        timer.wait_next_tick(abort_guard=lambda: exit_guard.should_exit)

        try:
            dongle_data = dongle.peek()
        except Exception as e:
            dongle_data = [''] * len(dongle_register_names)
            logging.error('Error while reading dongle: {}'.format(e))
            logging.info('Reconnecting after a bad TCP response...')
            tcp_connection_pool.reconnect()

        try:
            inverter_data = inverter.peek()
        except Exception as e:
            inverter_data = [''] * len(inverter_register_names)
            logging.error('Error while reading inverter: {}'.format(e))
            logging.info('Reconnecting after a bad TCP response...')
            tcp_connection_pool.reconnect()

        try:
            heat_pump_meter_data = heat_pump_meter.peek()
        except Exception as e:
            heat_pump_meter_data = [''] * len(heat_pump_meter_register_names)
            logging.error('Error while reading three-phase meter: {}'.format(e))
            logging.info('Reconnecting after a bad USB response...')
            usb_connection.reconnect()

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
            logging.error('Error while talking to EmonCMS: {}'.format(e))

        try:
            csv_file.write_values(
                    [datetime.datetime.now().isoformat()] + \
                    dongle_data + inverter_data + heat_pump_meter_data)
        except Exception as e:
            logging.error('Error while writing on CSV file: {}'.format(e))

    logging.info('Shutting down...')
    tcp_connection_pool.close()
    usb_connection.close()
    logging.info('Exiting...')
