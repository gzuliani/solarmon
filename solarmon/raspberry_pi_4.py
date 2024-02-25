import logging
import os
import psutil
import re
import subprocess
import time


class FileSystem:

    def __init__(self, mount_point, name, type):
        self.mount_point = mount_point
        self.name = name
        self.type = type

    def list():
        file_systems = []
        df_output = Command('df -T').run().decode()
        # skip the the heading
        for line in df_output.split('\n')[1:]:
            if not line:
                break
            tokens = line.split()
            if len(tokens) != 7:
                break
            file_systems.append(FileSystem(
                tokens[6], # mount point
                tokens[0], # file system
                tokens[1], # file system type
            ))
        return file_systems


class WirelessInterface:

    def __init__(self, name, ssid):
        self.name = name
        self.ssid = ssid

    def list():
        ifaces = []
        iwconfig_output = Command('iwconfig').run().decode()
        for line in iwconfig_output.split('\n'):
            match = re.search('^([\w]+)\s+ IEEE.*ESSID:"([^"]*)"', line)
            if match:
                name, ssid = match.group(1), match.group(2)
                ifaces.append(WirelessInterface(name, ssid))
        return ifaces


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
        self.name = 'cpu-load'

    def read(self):
        return psutil.cpu_percent(.1)


class CpuTemperature:

    def __init__(self):
        self.name = 'cpu-t'

    def read(self):
        return int(open('/sys/class/thermal/thermal_zone0/temp').read())/1000


class RamUsedPercent:

    def __init__(self):
        self.name = 'ram-usage'

    def read(self):
        memory = psutil.virtual_memory()
        return memory.percent


class DiskUsedPercent:

    def __init__(self, name, path):
        self.name = name
        self._path = path

    def read(self):
        stats = os.statvfs(self._path)
        return (1 - stats.f_bfree / stats.f_blocks) * 100


class WifiSignalStrength:

    def __init__(self, name, interface):
        self.name = name
        self.interface = interface
        self._command = Command(f'iwconfig {self.interface}')
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
        ]
        # file system usage
        for fs in [
            x for x in FileSystem.list()
                if x.type not in ['vfat', 'squashfs']
                    and not x.name in ['tmpfs', 'devtmpfs', 'udev']]:
            self._params.append(
                DiskUsedPercent(
                    f'disk-usage_{fs.mount_point}',
                    fs.mount_point))
        # wifi signal strength
        for iface in WirelessInterface.list():
            self._params.append(
                WifiSignalStrength(
                    f'rssi_{iface.ssid}',
                    iface.name))

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
