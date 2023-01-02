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
    parser.add_option("-i", "--interval",
                      dest="interval", type="int", default=30,
                      help="interval between samples")
    (options, args) = parser.parse_args()

    logging.basicConfig(
            filename='./daikin_altherma_sniffer.log',
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

    heading = ['date'] + [x.name for x in device.registers()] + ['duration']
    output.write(','.join(heading) + '\n')

    try:
        timer = Timer(options.interval)
        while True:
            start = datetime.datetime.now()
            data = device.peek()
            end = datetime.datetime.now()
            data = [datetime.datetime.now()] + data + [end - start]
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
