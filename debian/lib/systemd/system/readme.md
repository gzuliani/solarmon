# solarmon service

1. copy the solarmon.service file into the /lib/systemd/system folder:

        pi@raspberrypi:~ $ sudo cp solarmon/debian/lib/systemd/system/solarmon.service /lib/systemd/system

2. reload the systemd manager configuration:

        pi@raspberrypi:~ $ sudo systemctl daemon-reload

3. start/stop the service with:

        pi@raspberrypi:~ $ sudo systemctl start|stop|restart solarmon

To check the service status with:

    pi@raspberrypi:~ $ sudo systemctl status solarmon

To start the service at boot time:

    pi@raspberrypi:~ $ sudo systemctl enable solarmon

To disable the service from starting automatically:

    pi@raspberrypi:~ $ sudo systemctl disable solarmon
