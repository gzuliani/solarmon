import datetime
import logging
import math
import optparse
import random
import sys
import time

from clock import Timer
from emon import EmonCMS


class Parameter:

    def __init__(self, name, fn):
        self.name = name
        self._fn = fn

    def read(self, t):
        return self._fn(t)


class Sample:

    def __init__(self, device, values):
        self.device = device
        self.values = values


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
    parser.add_option('-k', '--api-key', dest='api_key',
            help='EmonCMS Input API Write Key', metavar='APIKEY')
    parser.add_option('-b', '--api-base-uri', type='string',
            dest='api_base_uri', default='http://127.0.0.1',
            help='EmonCMS Base API URI (default http://127.0.0.1)',
            metavar='URL')
    parser.add_option('-j', '--json-format', type='string', dest='json_format',
            default='json',
            help='JSON format, "fulljson" or "json" (deafult "json")',
            metavar='FORMAT')
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

    if not options.api_key:
        logging.error('EmonCMS API Key not supplied or empty')
        sys.exit(-1)

    valid_json_formats = ['json', 'fulljson']
    if not options.json_format in valid_json_formats:
        logging.error('Invalid JSON format: expected one of {}, got {}'.format(
                ', '.join(valid_json_formats), options.json_format))
        sys.exit(-1)

    logging.info('Connecting to EmonCMS API at %s...', options.api_base_uri)
    logging.info('Will use JSON format "%s"...', options.json_format)

    null_threshold = min(max(options.null, 0), 100) / 100

    emon = EmonCMS(options.api_base_uri, options.api_key, options.json_format)
    device = VirtualDevice()

    try:
        start = datetime.datetime.now()
        duration = datetime.timedelta(seconds=options.duration)
        timer = Timer(options.period)
        while datetime.datetime.now() < start + duration:
            values = device.read()
            if random.random() <= null_threshold:
                values = [None] * len(sample)
            logging.info('Emitting sample %s...', values)
            emon.write([Sample(device, values)])
            timer.wait_next_tick()
    except Exception as e:
        logging.exception('Unexpected exception caught')
    except KeyboardInterrupt:
        logging.warning('KeyboardInterrupt excpetion caught')
