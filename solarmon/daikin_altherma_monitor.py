import datetime
import logging
import optparse
import sys

from clock import Timer
from daikin import SerialConnection, Altherma


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="write data to FILE", metavar="FILE")
    parser.add_option("-p", "--period",
                      dest="period", type="int", default=30,
                      help="period between samples, in seconds (default 30)")
    parser.add_option("-d", "--duration",
                      dest="duration", type="int", default=3600,
                      help="monitoring duration, in seconds (default 3600)")
    (options, args) = parser.parse_args()

    logging.basicConfig(
            filename='./daikin_altherma_monitor.log',
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S')

    connection = SerialConnection('/dev/ttyUSB_HSCAN', 38400)
    connection.connect()
    device = Altherma('altherma', connection)

    if options.filename:
        output = open(options.filename, 'w')
    else:
        output = sys.stdout

    heading = ['date'] + [x.name for x in device.params()] + ['duration']
    output.write(','.join(heading) + '\n')

    try:
        start = datetime.datetime.now()
        duration = datetime.timedelta(seconds=options.duration)
        timer = Timer(options.period)
        while datetime.datetime.now() < start + duration:
            read_start = datetime.datetime.now()
            data = device.read()
            read_duration = datetime.datetime.now() - read_start
            data = [datetime.datetime.now()] + data + [read_duration]
            output.write(','.join([str(x) for x in data]) + '\n')
            output.flush()
            timer.wait_next_tick()
    except Exception as e:
        logging.warning(e)
    except KeyboardInterrupt:
        logging.warning('KeyboardInterrupt excpetion caught')
    connection.disconnect()
    if output is not sys.stdout:
        output.close()
