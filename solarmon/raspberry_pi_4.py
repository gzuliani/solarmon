import logging
import os
import psutil
import re
import subprocess
import time


class Param:
    def __init__(self, name):
        self.name = name
        self.type = 'number'


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
            match = re.search(r'^([\S]+)\s+ IEEE.*ESSID:"([^"]*)"', line)
            if match:
                name, ssid = match.group(1), match.group(2)
                ifaces.append(WirelessInterface(name, ssid))
        return ifaces


class WifiIfaceCount:
    def __init__(self, num_of_ifaces):
        self._num_of_ifaces = -1
        self._expected_num_of_ifaces = num_of_ifaces

    def is_fulfilled(self):
        return self._num_of_ifaces == self._expected_num_of_ifaces

    def load(self, ifaces):
        self._num_of_ifaces = len(ifaces)
        return ifaces


class WifiIfaceNames:
    def __init__(self, names):
        self._names = names
        self._ifaces = []

    def is_fulfilled(self):
        return len(self._ifaces) == len(self._names)

    def load(self, ifaces):
        self._ifaces = [x for x in ifaces if x.name in self._names]
        return self._ifaces


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


class CpuLoadPercent(Param):
    def __init__(self):
        super().__init__('cpu-load')

    def read(self):
        return psutil.cpu_percent(.1)


class CpuTemperature(Param):
    def __init__(self):
        super().__init__('cpu-t')

    def read(self):
        return int(open('/sys/class/thermal/thermal_zone0/temp').read())/1000


class RamUsedPercent(Param):
    def __init__(self):
        super().__init__('ram-usage')

    def read(self):
        memory = psutil.virtual_memory()
        return memory.percent


class DiskUsedPercent(Param):
    def __init__(self, name, path):
        super().__init__(name)
        self._path = path

    def read(self):
        stats = os.statvfs(self._path)
        return (1 - stats.f_bfree / stats.f_blocks) * 100


class WifiSignalStrength(Param):
    def __init__(self, name, interface):
        super().__init__(name)
        self.interface = interface
        self._command = Command(f'iwconfig {self.interface}')
        self._signal_level = re.compile(b'Signal level=(-\\d+)')

    def read(self):
        output = self._command.run()
        match = self._signal_level.search(output)
        if not match:
            raise RuntimeError(
                'interface "{}" not found'.format(self.interface))
        return int(match.group(1))


class UpTime(Param):
    def __init__(self):
        super().__init__('up-time')

    def read(self):
        return float(open('/proc/uptime').read().split()[0])


class RaspberryPi4:
    def __init__(self, name, wifi_filter):
        self.name = name
        self._wifi_filter = wifi_filter
        self.reconfigure()

    def params(self):
        return self._params

    def read(self):
        # keep reconfiguring until all the wifi interfaces are identified
        if not self._wifi_filter.is_fulfilled():
            self.reconfigure()
        return [x.read() for x in self._params]

    def reconfigure(self):
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
        for iface in self._wifi_filter.load(WirelessInterface.list()):
            self._params.append(
                WifiSignalStrength(f'rssi_{iface.ssid}', iface.name))


if __name__ == '__main__':

    device = RaspberryPi4("rasp", WifiIfaceCount(1))
#    device = RaspberryPi4("rasp", WifiIfaceNames(['wlan0']))
    print(','.join(x.name for x in device.params()))

    while True:
        print(','.join([str(x) for x in device.read()]))
        time.sleep(1)
