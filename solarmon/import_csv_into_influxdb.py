import datetime
import logging
import optparse
from os import name
import sys

from influxdb import InfluxDB

class Parameter:

    def __init__(self, name):
        self.name = name


class Device:

    def __init__(self, name):
        self.name = name
        self._param_names = []
        self._param_indexes = []

    def add_param(self, name, index):
        self._param_names.append(Parameter(name))
        self._param_indexes.append(index)

    def params(self):
        return self._param_names

    def param_indexes(self):
        return self._param_indexes


class Csv:

    def __init__(self, path):
        self._file = open(path)
        headers = self._read_next_line()
        self._devices = {}
        for i, header in enumerate(headers):
            # The first column is `time_stamp`, ignore it
            if i == 0:
                continue
            device_name, param_name = header.split('.')
            if not device_name in self._devices:
                self._devices[device_name] = Device(device_name)
            self._devices[device_name].add_param(param_name, i)

    def read(self):
        row = self._read_next_line()
        timestamp = row[0]
        data = []
        for device in self._devices.values():
            values = []
            for i in device.param_indexes():
                values.append(row[i])
            data.append((device, values))
        return timestamp, data

    def _read_next_line(self):
        line = self._file.readline()
        if line == '':
            raise StopIteration
        return line.strip().split(',')


if __name__ == '__main__':

    parser = optparse.OptionParser()
    parser.add_option('-p', '--path', dest='path', type='string',
            help='Path of the CSV file')
    parser.add_option('-t', '--api-token', dest='api_token',
            help='InfluxDB API Token', metavar='APITOKEN')
    parser.add_option('-a', '--api-base-uri', type='string',
            dest='api_base_uri', default='http://127.0.0.1:8086',
            help='InfluxDB Base API URI (default http://127.0.0.1:8086)',
            metavar='URL')
    parser.add_option('-o', '--organization', type='string',
            dest='organization', help='Organization name',
            metavar='ORGANIZATION')
    parser.add_option('-b', '--bucket', type='string',
            dest='bucket', help='Destination bucket name', metavar='BUCKET')

    (options, args) = parser.parse_args()

    logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            handlers=[logging.StreamHandler()],
            datefmt='%Y-%m-%dT%H:%M:%S')

    if not options.path:
        logging.error('CSV file path not supplied')
        sys.exit(-1)

    if not options.api_token:
        logging.error('InfluxDB API Token not supplied')
        sys.exit(-1)

    if not options.organization:
        logging.error('Organization name not supplied')
        sys.exit(-1)

    if not options.bucket:
        logging.error('Bucket name not supplied')
        sys.exit(-1)

    logging.info('Connecting to InfluxDB API at %s...', options.api_base_uri)

    try:
        influx_db = InfluxDB(
            options.api_base_uri,
            options.api_token,
            options.organization,
            options.bucket)

        csv = Csv(options.path)

        while True:
            timestamp, data = csv.read()
            date = datetime.datetime.strptime(timestamp[:19], "%Y-%m-%dT%H:%M:%S")
            elapsed = date - datetime.datetime(1970, 1, 1)
            influx_db.write(data, int(elapsed.total_seconds()))

    except StopIteration:
        logging.info('Done')
    except Exception as e:
        logging.exception('Unexpected exception caught')
    except KeyboardInterrupt:
        logging.warning('KeyboardInterrupt excpetion caught')
