# Solarmon

Huawei SUN2000 inverter monitoring system.

Some notes about how to talk to a Huawei SUN2000 inverter [are available here](https://gzuliani.github.io/emon/huawei_sun2000.html) (italian only).

Some notes about how to talk to a Daikin Altherma heat pump [are available here](https://gzuliani.github.io/emon/daikin-altherma.html) (italian only).

## Dependencies

* [PyModbus v.2.5.2](https://pymodbus.readthedocs.io/en/v2.5.3/)
* [requests v. 2.21.0](https://pypi.org/project/requests/2.21.0/)
* [psutil](https://pypi.org/project/psutil/) (required by `raspberry_pi_4.RaspberryPi4` monitor)

## Test

First install the dependencies:

    $ cd solarmon
    $ python3 -m venv venv
    $ . venv/bin/activate
    $ pip3 install requests==2.21.0
    $ pip3 install pymodbus==2.5.2
    $ pip3 install psutil

Then run the tests with the following command:

    $ PYTHONPATH=solarmon python3 -m unittest -v

## Implementation notes

### Input devices

Input `Device`s represent a source of data such as a SUN2000 Huawei inverter, a Daikin heat pump or a generic power meter. Input devices have a `name` attribute, a set of `Parameter`s and a `read` method that can be used to capture their values. The `reconfigure` method can be used to reset the device in case of errors.

A `Connection` object represents a channel that can be used to communicate with a real device such a serial port or a WiFi or Ethernet connection. Device objects may use some sort of `Adapter`s to implement the communication protocol of the real device. See for example the `eml327.ELM327` OBD/Serial adapter object or the `modbus.UsbRtuAdapter` RS485/Serial adapter object.

A `Parameter` is a device-dependent object that represents a physical dimension that can be measured. A register has a `name` attribute and some other data that a `Device` object can use to acquire and decode a parameter value from the real device.

### Output devices

Output devices are used to publish the data acquired from the pool of input devices. Output devices have a `write` method that expects a list of `Samples`. A `Sample` is an object that contains a reference to a `Device` (in the `device` member) and a set of readings in the `values` member. `values` is a list that contains the values of the registers of the device. A value of `None` indicates that the value of that particular register could not be acquired.

### Main program

When started the program initializes a number of `Connection`s, then defines the set of input devices and connects them to the real one using the corresponding channel. Every device internally istantiates an adapter that implements the communication protocol to communicate with the real device. The list of output devices is finally build, currently a `EmonCMS` API client and an optional `CsvFile` output file.

The program then enters the main loop:

* loop through the list of input devices invoking the `read` method;
* if the acquistion fails for a given device, the communication channel used by that devices is reinitialized by means of the `reconnect` method of the associated `Communication` object;
* a list of (`Device`, `readings`) tuples is then build;
* the acquired data is forwared to the output device, one by one.

### Installation

#### EmonSD

The starting point is the last stable image of this distribution ([emonSD-10Nov22 (Stable)](https://docs.openenergymonitor.org/emonsd/download.html) at the time of writing).

**Warning:** do not apply any OS upgrade to this image!

* clone this repository in the home directory of the **pi** user:

        $ cd
        pi@raspberrypi:~ $ git clone https://github.com/gzuliani/solarmon.git

* install the dependencies as root:

        pi@raspberrypi:~ $ sudo pip3 install requests==2.21.0
        pi@raspberrypi:~ $ sudo pip3 install pymodbus==2.5.2
        pi@raspberrypi:~ $ sudo pip3 install psutil

  The `psutil` package is required by the `raspberry_pi_4.RaspberryPi4.py` module only. You don't need to install it if you do not intend to use such module.

* connect the USB adapters to the Raspberry and set up the `etc/udev/rules.d/10-local.rules` to ensure they get a unique name. The document [docs/how-to-usb-static-names.md](https://github.com/gzuliani/solarmon/blob/main/docs/how-to-usb-static-names.md) explains how to do it, the folder [udev](https://github.com/gzuliani/solarmon/tree/main/udev) contains some working examples. When done, restart the **udev** server:

         pi@raspberrypi:~ $ sudo udevadm trigger

* define the set of input and output devices in the `solarmon/main.py` source file; you can use the `solarmon/main_andrea.py` and `solarmon/main_laura.py` templates. Set the `api_key` global variable to the "Write API Key" of the EmonCMS local installation.

* enable the rotation of the **solarmon** log following the instructions in [debian/etc/logrotate.d/readme.md](https://github.com/gzuliani/solarmon/tree/main/debian/etc/logrotate/readme.md).

* configure **solarmon** to run as a service following the instructions in [debian/lib/systemd/system/readme.md](https://github.com/gzuliani/solarmon/tree/main/debian/lib/systemd/system/readme.md).

#### InfluxDB

TODO.
