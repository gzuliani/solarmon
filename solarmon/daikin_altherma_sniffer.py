import datetime
import logging
import optparse
import sys

from clock import Timer
from daikin import SerialConnection, CanBusMonitor, Parameter


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="write data to FILE", metavar="FILE")
    parser.add_option("-p", "--period",
                      dest="period", type="int", default=30,
                      help="period between samples, in seconds (default 30)")
    parser.add_option("-d", "--duration",
                      dest="duration", type="int", default=3600,
                      help="sniffing duration, in seconds (default 3600)")
    (options, args) = parser.parse_args()

    logging.basicConfig(
            filename='./daikin_altherma_sniffer.log',
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S')

    connection = SerialConnection('/dev/ttyUSB_HSCAN', 38400)
    connection.connect()
    monitor = CanBusMonitor('altherma', connection)
    monitor.set_params([
        Parameter('t_dhw',            'float', 'deg',   10, b'190', b'31000E00000000'),
        Parameter('water_pressure',   'float', 'bar', 1000, b'190', b'31001C00000000'),
        Parameter('mode_01',            'int',    '',    1, b'190', b'3100FA01120000'),
        Parameter('t_hs',             'float', 'deg',   10, b'190', b'3100FA01D60000'),
        Parameter('t_ext',            'float', 'deg',   10, b'310', b'6100FA0A0C0000'),
    ])

    if options.filename:
        output = open(options.filename, 'w')
    else:
        output = sys.stdout

    heading = ['date'] + [x.name for x in monitor.params()]
    output.write(','.join(heading) + '\n')

    monitor.start()
    try:
        start = datetime.datetime.now()
        duration = datetime.timedelta(seconds=options.duration)
        timer = Timer(options.period)
        while datetime.datetime.now() < start + duration:
            data = [datetime.datetime.now()] + monitor.read()
            output.write(','.join([str(x) for x in data]) + '\n')
            output.flush()
            timer.wait_next_tick()
    except Exception as e:
        logging.warning(e)
    except KeyboardInterrupt:
        logging.warning('KeyboardInterrupt excpetion caught')
    monitor.terminate_and_wait()
    connection.disconnect()
    if output is not sys.stdout:
        output.close()
