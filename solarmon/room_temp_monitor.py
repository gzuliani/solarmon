#!env/bin/python -u
# the line above disables stdout/stderr buffering

import datetime
import logging
import signal

import bme_280
import clock
import osmer_fvg
import persistence

sampling_period = 60 # seconds

# device codes -- should be unique
osmer_name = 'osmer'

bme_280_name = 'bme280'
bme_280_port = 1
bme_280_addr = 0x76


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
    logging.basicConfig(
        # filename='/var/log/solarmon.log',
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S')
    logging.info('Booting...')

    try:
        input_devices = [
            bme_280.Bme280(bme_280_name, bme_280_port, bme_280_addr),
            osmer_fvg.OsmerFvg(osmer_name, 'UDI'), # keep it as the last one!
        ]

        qualified_param_names = [
            '{}.{}'.format(d.name, r.name)
                for d in input_devices for r in d.params()]

        output_devices = [
            persistence.CsvFile('CSV', csv_file_path(), qualified_param_names),
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
        logging.info('Exiting...')
    except:
        logging.exception('An unexpected fatal error occoured, exiting...')
