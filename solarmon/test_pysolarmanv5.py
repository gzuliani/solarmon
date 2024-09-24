#!env/bin/python -u
# the line above disables stdout/stderr buffering

import time

import deye
import sample
import solarman
import ui


if __name__ == '__main__':

    solarman_wifi = solarman.StickLoggerWiFi('192.168.1.2', 2777916217)
#    solarman_wifi = solarman.StickLoggerWiFi('10.10.100.254', 2777916217)
    solarman_wifi.connect()

    input_device = deye.Inverter('inverter', solarman_wifi,  1)
    print(','.join(x.name for x in input_device.params()))

    exit_guard = ui.ShutdownRequest()

    while not exit_guard.should_exit:
        data = sample.read_from(input_device)
        if data.is_error():
            print('ERROR:', data.error())
        else:
            print(','.join(f'{x:.01f}' for x in data.values))
        time.sleep(10)

    solarman_wifi.disconnect()
