import datetime
import logging
import math
import optparse
import random
import sys
import time

from clock import Timer
from influxdb import InfluxDB


class Parameter:

    def __init__(self, name, fn):
        self.name = name
        self._fn = fn

    def read(self, t):
        return self._fn(t)


class VirtualDevice:

    def __init__(self):
        self.name = 'test-node'
        self._t0 = time.time()
        self._params = [
            Parameter('k', lambda _: -2.4),
            Parameter('sin', lambda x: 5 + 5 * math.sin(x / 300 * math.pi)),
            Parameter('rnd', lambda _: 6 + 2 * random.random()),
        ]

    def params(self):
        return self._params

    def read(self):
        elapsed = time.time() - self._t0
        return [x.read(elapsed) for x in self._params]


if __name__ == '__main__':

    parser = optparse.OptionParser()
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
            dest='bucket', help='Organization name', metavar='BUCKET')
    parser.add_option('-n', '--null', type='int', default=0, dest='null',
            help='Percentage of null samples to emit (default 0)',
            metavar='PERCENT')
    parser.add_option('-p', '--period', dest='period', type='int', default=30,
            help='period between samples, in seconds (default 30)')
    parser.add_option('-d', '--duration', dest='duration', type='int',
            default=3600, help='test duration, in seconds (default 3600)')

    (options, args) = parser.parse_args()

    logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            handlers=[logging.StreamHandler()],
            datefmt='%Y-%m-%dT%H:%M:%S')

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

    null_threshold = min(max(options.null, 0), 100) / 100

    influx_db = InfluxDB(
        options.api_base_uri,
        options.api_token,
        options.organization,
        options.bucket)
    device = VirtualDevice()

    try:
        start = datetime.datetime.now()
        duration = datetime.timedelta(seconds=options.duration)
        timer = Timer(options.period)
        while datetime.datetime.now() < start + duration:
            sample = device.read()
            if random.random() <= null_threshold:
                sample = [None] * len(sample)
            logging.info('Emitting sample %s...', sample)
            influx_db.write([(device, sample)])
            timer.wait_next_tick()
    except Exception as e:
        logging.exception('Unexpected exception caught')
    except KeyboardInterrupt:
        logging.warning('KeyboardInterrupt excpetion caught')
