import datetime
import logging
import time
import sys

from daikin import SerialConnection, ObdSniffer, Register


if __name__ == '__main__':
    logging.basicConfig(
            filename='./daikin_altherma_sniffer.log',
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S')
    connection = SerialConnection('/dev/ttyUSB_HSCAN', 38400)
    connection.connect()
    sniffer = ObdSniffer('altherma', connection)
    sniffer.set_registers([
        Register('t_dhw',            'float', 'deg',   10, b'190', b'31000E00000000'),
        Register('water_pressure',   'float', 'bar', 1000, b'190', b'31001C00000000'),
        Register('mode_01',            'int',    '',    1, b'190', b'3100FA01120000')
        Register('t_hs',             'float', 'deg',   10, b'190', b'3100FA01D60000'),
        Register('t_ext',            'float', 'deg',   10, b'310', b'6100FA0A0C0000'),
    ])
    heading = ['date'] + [x.name for x in sniffer.registers()]
    # output = open('./daikin_altherma_sniffer.csv', 'w')
    output = sys.stdout
    output.write(','.join(heading) + '\n')
    sniffer.start()
    try:
        while True:
            data = [datetime.datetime.now()] + sniffer.peek()
            output.write(','.join([str(x) for x in data]) + '\n')
            output.flush()
            time.sleep(30)
    except Exception as e:
        logging.warning(e)
    except KeyboardInterrupt:
        logging.warning('KeyboardInterrupt excpetion caught')
    sniffer.terminate_and_wait()
    connection.disconnect()
    if output is not sys.stdout:
        output.close()
