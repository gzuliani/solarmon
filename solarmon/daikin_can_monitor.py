import datetime
import logging
import optparse
import sys

from daikin import UsbCanAdapter


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="write data to FILE", metavar="FILE")
    parser.add_option("-d", "--duration",
                      dest="duration", type="int", default=3600,
                      help="monitoring duration, in seconds (default 3600)")
    (options, args) = parser.parse_args()

    logging.basicConfig(
            filename='./daikin_can_monitor.log',
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S')

    can_adapter = UsbCanAdapter('/dev/ttyUSB_HSCAN', 38400)
    can_adapter.connect()

    if options.filename:
        output = open(options.filename, 'w')
    else:
        output = sys.stdout

    try:
        start = datetime.datetime.now()
        duration = datetime.timedelta(seconds=options.duration)
        can_adapter.start_monitor()
        while datetime.datetime.now() < start + duration:
            while True:
                packet = can_adapter.consume()
                if packet is None or len(packet) == 0:
                    break
                now = datetime.datetime.now()
                for x in packet:
                    output.write(f'{now} {x.decode("utf8")}\n')
            output.flush()
    except Exception as e:
        logging.warning(e)
    except KeyboardInterrupt:
        logging.warning('KeyboardInterrupt excpetion caught')
    can_adapter.stop_monitor()
    can_adapter.disconnect()
    if output is not sys.stdout:
        output.close()
