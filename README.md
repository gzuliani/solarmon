# Solarmon

Huawei SUN2000 inverter monitoring system.

Some notes about how to talk to a Huawei SUN2000 inverter [are available here](https://gzuliani.github.io/emon/huawei_sun2000.html) (italian only).

Some notes about how to talk to a Daikin Altherma heat pump [are available here](https://gzuliani.github.io/emon/daikin-altherma.html) (italian only).

## Implementation notes

### Input devices

Input `Device`s represent a source of data such as a SUN2000 Huawei inverter, a Daikin heat pump or a generic power meter. Input devices have a `name` attribute, a set of `Parameter`s and a `read` method that can be used to capture their values. The `reconfigure` method can be used to reset the device in case of errors.

A `Connection` object represents a channel that can be used to communicate with a real device such a serial port or a WiFi or Ethernet connection. Device objects may use some sort of `Adapter`s to implement the communication protocol of the real device. See for example the `eml327.ELM327` OBD/Serial adapter object or the `modbus.UsbRtuAdapter` RS485/Serial adapter object.

A `Parameter` is a device-dependent object that represents a physical dimension that can be measured. A register has a `name` attribute and some other data that a `Device` object can use to acquire and decode a parameter value from the real device.

### Output devices

Output devices are used to publish the data acquired from the pool of input devices. Output devices have a `write` method that expects a list of (`Device`, `readings`) tuples where `readings` is a list that contains the values of the registers of the device or `None` if a particular parameter was not acquired.

### Main program

When started the program initializes a number of `Connection`s, then defines the set of input devices and connects them to the real one using the corresponding channel. Every device internally istantiates an adapter that implements the communication protocol to communicate with the real device. The list of output devices is finally build, currently a `EmonCMS` API client and an optional `CsvFile` output file.

The program then enters the main loop:

* loop through the list of input devices invoking the `read` method;
* if the acquistion fails for a given device, the communication channel used by that devices is reinitialized by means of the `reconnect` method of the associated `Communication` object;
* a list of (`Device`, `readings`) tuples is then build;
* the acquired data is forwared to the output device, one by one.
