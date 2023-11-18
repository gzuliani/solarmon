# How to: assign a static name to a USB device

A new `udev` rule must be defined for the USB device, here's how:

1. connect the USB device

2. find the `VendorId` and `productId` attribute values of the device:

        $ lsusb
        Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
        Bus 001 Device 004: ID 10c4:ea60 Cygnal Integrated Products, Inc. CP2102/CP2109 UART Bridge Controller [CP210x family]
        Bus 001 Device 003: ID 148f:7601 Ralink Technology, Corp. MT7601U Wireless Adapter
        Bus 001 Device 002: ID 2109:3431 VIA Labs, Inc. Hub
        Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

    Being "CP2102/CP2109 UART Bridge Controller" the target device, the data we're interested in are:

    * vendorId: `10c4`
    * productId: `ea60`

3. open or create the file `/etc/udev/rules.d/10-local.rules`:

        $ sudo nano /etc/udev/rules.d/10-local.rules

4. add the following line to the file:

        SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ttyUSB_RS485"

5. save, exit `nano` and then restart the `udev` service:

        $ sudo udevadm trigger

A new symbolic link with the given name is created everytime the device is connected:

    $ ls -al /dev/ttyUSB*
    crw-rw---- 1 root dialout 188, 0 Dec 19 22:34 /dev/ttyUSB0
    lrwxrwxrwx 1 root root         7 Dec 19 22:34 /dev/ttyUSB_RS485 -> ttyUSB0

**Note**: if two or more devices with the same `vendorId` and `productId` must be statically named, use the following command to find an additional, discriminating attribute:

    $ udevadm info --name=/dev/ttyUSB0 --attribute-walk

Usually `ATTRS{serial}` fixes the problem.

See also: [Writing udev rules](https://reactivated.net/writing_udev_rules.html) by Daniel Drake.
