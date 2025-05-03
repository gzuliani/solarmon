# Solarmon

Huawei SUN2000 inverter monitoring system.

Some notes about how to talk to a Huawei SUN2000 inverter [are available here](https://gzuliani.github.io/emon/huawei_sun2000.html) (italian only).

Some notes about how to talk to a Daikin Altherma heat pump [are available here](https://gzuliani.github.io/emon/daikin-altherma.html) (italian only).

## Development environment

Follow the instructions below to set up a development environment for Solarmon. If you intend to just install the software, go to the [Installation](#installation) section.

### Dependencies

* Python >= 3.8
* [PyModbus v.3.9.2](https://pymodbus.readthedocs.io/en/v3.9.2/)
* [requests v. 2.32.3](https://pypi.org/project/requests/2.32.3/)
* [psutil](https://pypi.org/project/psutil/) (required by `raspberry_pi_4.RaspberryPi4` monitor)
* [pysolarmanv5](https://github.com/jmccrohan/pysolarmanv5) (required by the `solarman.StickLoggerWiFi` communication channel)

### Test

First install the dependencies:

    pi@raspberrypi:~ $ cd solarmon
    pi@raspberrypi:~/solarmon $ python3 -m venv venv
    pi@raspberrypi:~/solarmon$ . venv/bin/activate
    (venv) pi@raspberrypi:~/solarmon$ pip3 install requests==2.31.0
    (venv) pi@raspberrypi:~/solarmon$ pip3 install pymodbus==3.9.2
    (venv) pi@raspberrypi:~/solarmon$ pip3 install psutil
    (venv) pi@raspberrypi:~/solarmon$ pip3 install pysolarmanv5

Then run the tests with the following command:

    (venv) pi@raspberrypi:~/solarmon$ PYTHONPATH=solarmon python3 -m unittest -v

## Implementation notes

### Input devices

Input `Device`s represent a source of data such as a SUN2000 Huawei inverter, a Daikin heat pump or a generic power meter. Input devices have a `name` attribute, a set of `Parameter`s -- accessible by means of the `params` method -- and a `read` method that can be used to capture their values. The `reconfigure` method can be used to reset the device in case of errors.

Devices used to have a static set of parameters, so that the `params` method always returned the same set of objects. Starting with the `RaspberryPi4` device, the parameter set has become dynamic, i.e. it may change as a result of a call to the `read` method.

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

## Installation

### EmonSD

The starting point is the last stable image of this distribution ([emonSD-01Feb24](https://docs.openenergymonitor.org/emonsd/download.html) at the time of writing).

**Warning:** do not apply any OS upgrade to this image!

* clone this repository in the home directory of the **pi** user:

        $ cd
        pi@raspberrypi:~ $ git clone https://github.com/gzuliani/solarmon.git

* install the dependencies as root:

        pi@raspberrypi:~ $ sudo pip3 install requests==2.31.0 # READ NOTE BELOW!
        pi@raspberrypi:~ $ sudo pip3 install pymodbus==3.6.4  # READ NOTE BELOW!
        pi@raspberrypi:~ $ sudo pip3 install psutil
        pi@raspberrypi:~ $ sudo pip3 install pysolarmanv5

  The `psutil` package is required by the `raspberry_pi_4.py` module only. You don't need to install it if you do not intend to use such module.

  The `pysolarmanv5` package is required by the `solarman.py` module only. You don't need to install it if you do not intend to use such module.

> [!WARNING]
> The **EmonSD-01Feb24** image contains `requests` v. 2.28.0 and `pymodbus` v. 3.0.0. Updating these packages made the RS485 communication problematic, so better stay with the preinstalled ones.

* connect the USB adapters to the Raspberry and set up the `etc/udev/rules.d/10-local.rules` to ensure they get a unique name. The document [docs/how-to-usb-static-names.md](https://github.com/gzuliani/solarmon/blob/main/docs/how-to-usb-static-names.md) explains how to do it, the folder [debian/udev](https://github.com/gzuliani/solarmon/tree/main/debian/udev) contains some working examples. When done, restart the **udev** server:

        pi@raspberrypi:~ $ sudo udevadm trigger

* define the set of input and output devices in the `solarmon/main.py` source file; you can use the `solarmon/main_andrea.py` and `solarmon/main_laura.py` templates. Set the `api_key` global variable to the "Write API Key" of the EmonCMS local installation.

* install and customize the **solarmon** configuration file following the instructions in [debian/etc/readme.md](https://github.com/gzuliani/solarmon/tree/main/debian/etc/readme.md).

* configure **solarmon** to run as a service following the instructions in [debian/lib/systemd/system/readme.md](https://github.com/gzuliani/solarmon/tree/main/debian/lib/systemd/system/readme.md).

### Raspberry Pi OS + InfluxDB + Grafana

TODO. Some notes are available [here](docs/plants/mine/README.md) (italian only).

## Extensions

`solarmon/room_temp_monitor.py` is a script that has been used to evaluate the efficiency of an heating system by monitoring indoor vs. outdoor temperatures. The former was acquired using a BME280 sensor, the latter was downloaded from a local weather service. In order for the `bme_280.Bme280` input device to work, an additional Python package must be installed:

    pi@raspberrypi:~/solarmon $ pip3 install RPi.bme280

The support for the I2C bus must be installed too:

    pi@raspberrypi:~/solarmon $ sudo apt install i2c-tools python3-smbus

To make it available automatically at start up the system configuration must be changed:

    pi@raspberrypi:~/solarmon $ sudo raspi-config

A configuration menu appears. Select "5 Interfacing Options", then "P5 I2C". Enable the "ARM I2C interface". Reboot the Raspberry Pi. To verify that the BME280 sensor has been identified, issue the command:

    pi@raspberrypi:~ $ sudo i2cdetect -y 1
         0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
    00:                         -- -- -- -- -- -- -- -- 
    10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
    70: -- -- -- -- -- -- 76 --                         

where `76` is the default address of the BME280 device.
