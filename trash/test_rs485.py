#!env/bin/python -u
# the line above disables stdout/stderr buffering

import datetime

import clock
import deye
import meters
import modbus
import pymodbus


sampling_period = 3 # seconds


if __name__ == '__main__':

    print(f'using pymodbus v. {pymodbus.__version__}')
    print(f'connecting...')
    rs485_adapter = modbus.UsbRtuAdapter(
        '/dev/ttyUSB0', timeout=1, delay_between_reads=3)
    rs485_adapter.connect()
    print(f'connection established...')

    devices = [
        deye.Inverter('inverter', rs485_adapter, 1),
        # meters.SDM120M('meter_1', rs485_adapter, 10),
    ]

    print(f'starting sampling...')
    timer = clock.Timer(sampling_period)

    while True:
        timer.wait_next_tick()
        now = datetime.datetime.now()

        for device in devices:
            try:
                device.read()
                print(f'{now} {device.name} OK')
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f'{now} {device.name} ERROR: {e}')

    rs485_adapter.disconnect()
