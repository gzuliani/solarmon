import os
import subprocess
import time


class Command:

    def __init__(self, command):
        self._command = command

    def run(self):
        return subprocess.run(
            self._command, capture_output=True, shell=True).stdout


class Cpu:

    def __init__(self):
        self._command = Command(
            "top -n1 | awk '/Cpu/ {print $2,$4,$6,$8,$10}'")
        self.refresh()

    def refresh(self):
        self.user, \
        self.system, \
        self.nice, \
        self.idle, \
        self.io_wait = [float(x.replace(b',', b'.'))
                        for x in self._command.run().split()]


class Ram:

    def __init__(self):
        self._command = Command(
            "free | awk '/Mem/ {print $2,$3,$4,$5,$6,$7}'")
        self.refresh()

    def refresh(self):
        self.total, \
        self.used, \
        self.free, \
        self.shared, \
        self.cache, \
        self.available = [int(x) for x in self._command.run().split()]


class CpuLoadPercent:

    def __init__(self, cpu):
        self.name = 'cpu-load-percent'
        self._cpu = cpu

    def read(self):
        return 100 - self._cpu.idle
        

class CpuTemperature:

    def __init__(self):
        self.name = 'cpu-temperature'

    def read(self):
        return int(open('/sys/class/thermal/thermal_zone0/temp').read())/1000


class RamUsedPercent:

    def __init__(self, ram):
        self.name = 'ram-used-percent'
        self._ram = ram

    def read(self):
        return self._ram.used / self._ram.total * 100


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
        self._command = Command(
            "iwconfig 2>/dev/null | grep -oP 'Signal level=\K(-\d+)'")

    def read(self):
        return int(self._command.run())


class UpTime:

    def __init__(self):
        self.name = 'up-time'
        self._command = Command('cat /proc/uptime')

    def read(self):
        return float(self._command.run().split()[0])
    

class RaspberryPi4:

    def __init__(self, name):
        self.name = name
        self._cpu = Cpu()
        self._ram = Ram()
        self._params = [
            UpTime(),
            CpuLoadPercent(self._cpu),
            CpuTemperature(),
            RamUsedPercent(self._ram),
            DiskUsedPercent('/'),
            WifiSignalStrength(),
        ]

    def params(self):
        return self._params

    def read(self):
        self._cpu.refresh()
        self._ram.refresh()
        return [x.read() for x in self._params]


if __name__ == '__main__':

    device = RaspberryPi4("rasp")
    print(','.join(x.name for x in device.params()))

    while True:
        print(','.join([str(x) for x in device.read()]))
        time.sleep(1)
