import logging
import os
import psutil
import re
import subprocess
import time


class Command:

    def __init__(self, command):
        self._command = command

    def run(self):
        logging.debug('Running command "%s"...', self._command)
        result = subprocess.run(
            self._command, capture_output=True, shell=True)
        logging.debug('Command returned %s - %s',
            result.returncode, result.stdout)
        return result.stdout


class CpuLoadPercent:

    def __init__(self):
        self.name = 'cpu-load-percent'

    def read(self):
        return psutil.cpu_percent(.1)


class CpuTemperature:

    def __init__(self):
        self.name = 'cpu-temperature'

    def read(self):
        return int(open('/sys/class/thermal/thermal_zone0/temp').read())/1000


class RamUsedPercent:

    def __init__(self):
        self.name = 'ram-used-percent'

    def read(self):
        memory = psutil.virtual_memory()
        return memory.percent


class DiskUsedPercent:

    def __init__(self, path):
        self.name = 'disk-used-percent'
        self._path = path

    def read(self):
        stats = os.statvfs(self._path)
        return (1 - stats.f_bfree / stats.f_blocks) * 100


class WifiSignalStrength:

    def __init__(self):
        self.name = 'wifi-signal-strength'
        self._command = Command('iwconfig')
        self._signal_level = re.compile(b'Signal level=(-\d+)')

    def read(self):
        output = self._command.run()
        match = self._signal_level.search(output)
        return int(match.group(1)) if match else None


class UpTime:

    def __init__(self):
        self.name = 'up-time'

    def read(self):
        return float(open('/proc/uptime').read().split()[0])


class RaspberryPi4:

    def __init__(self, name):
        self.name = name
        self._params = [
            UpTime(),
            CpuLoadPercent(),
            CpuTemperature(),
            RamUsedPercent(),
            DiskUsedPercent('/'),
            WifiSignalStrength(),
        ]

    def params(self):
        return self._params

    def read(self):
        return [x.read() for x in self._params]

    def reconfigure(self):
        pass


if __name__ == '__main__':

    device = RaspberryPi4("rasp")
    print(','.join(x.name for x in device.params()))

    while True:
        print(','.join([str(x) for x in device.read()]))
        time.sleep(1)
