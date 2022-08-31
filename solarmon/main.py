#!env/bin/python -u
# the line above disables stdout/stderr buffering

# huawei modbus
timeout = 5

# emoncms webapi
api_base_uri = 'http://127.0.0.1'
api_key = '92361dc1aacccbed7c284d6387bf9b54'
dongle_node_number = 101
inverter_node_number = 102
grid_meter_node_number = 103

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
    grid_meter = usb_connection.attach_to_JSY_MK_323_meter(1)

    exit_guard = ShutdownRequest()
    clock = clock.WallClock()

    csv_file = persistence.CsvFile('huawei_sun2000_{}.csv'.format(
        datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
    csv_file.write_heading(
            ['local_time'] + \
            [x.name for x in dongle.registers()] + \
            [x.name for x in inverter.registers()] + \
            [x.name for x in grid_meter.registers()])

    while not exit_guard.should_exit:
        clock.wait_next_minute(abort_guard=lambda: exit_guard.should_exit)

        try:
            dongle_data = dongle.read_registers()
        except Exception as e:
            logging.error('Error while reading dongle: {}'.format(e))
            logging.info('Reconnecting after a bad TCP response...')
            tcp_connection_pool.reconnect()

        try:
            inverter_data = inverter.read_registers()
        except Exception as e:
            logging.error('Error while reading inverter: {}'.format(e))
            logging.info('Reconnecting after a bad TCP response...')
            tcp_connection_pool.reconnect()

        try:
            grid_meter_data = grid_meter.read_registers()
        except Exception as e:
            logging.error('Error while reading three-phase meter: {}'.format(e))
            logging.info('Reconnecting after a bad USB response...')
            usb_connection.reconnect()

        try:
            emoncms.send(dongle_data, dongle_node_number)
            emoncms.send(inverter_data, inverter_node_number)
            emoncms.send(grid_meter_data, grid_meter_node_number)
        except Exception as e:
            logging.error('Error while talking to EmonCMS: {}'.format(e))

        try:
            csv_file.write_values(
                    [datetime.datetime.now().isoformat()] + \
                    dongle_data + inverter_data + grid_meter_data)
        except Exception as e:
            logging.error('Error while writing on CSV file: {}'.format(e))

    logging.info('Shutting down...')
    tcp_connection_pool.close()
    usb_connection.close()
    logging.info('Exiting...')
