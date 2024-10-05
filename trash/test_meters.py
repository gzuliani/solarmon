#!env/bin/python -u
# the line above disables stdout/stderr buffering

import datetime

import clock
import meters
import modbus
import pymodbus


sampling_period = 3 # seconds


if __name__ == '__main__':

    print(f'using pymodbus v. {pymodbus.__version__}')
    print(f'connecting...')
    rs485_adapter = modbus.UsbRtuAdapter(
        '/dev/ttyUSB_RS485', timeout=1, delay_between_reads=3)
    rs485_adapter.connect()
    print(f'connection established...')

    meters = [
        meters.SDM120M('meter_1', rs485_adapter, 10),
    ]

    print(f'starting sampling...')
    timer = clock.Timer(sampling_period)

    while True:
        timer.wait_next_tick()
        now = datetime.datetime.now()

        for meter in meters:
            try:
                meter.read()
                print(f'{now} {meter.name} OK')
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f'{now} {meter.name} ERROR: {e}')

    rs485_adapter.disconnect()
