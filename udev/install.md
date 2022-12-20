# assign a fixed name to USB adapters

1. copy the 10-usb-serial.rules file into the /etc/udev/rules.d folder
2. refresh the udev rules:

        $ sudo udevadm trigger
