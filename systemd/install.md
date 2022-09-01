# solarmon service

1. copy the solarmon.service file into the /lib/systemd/system folder
2. reload the systemd manager configuration:

        $ sudo systemctl daemon-reload

3. start/stop the service with:

        $ sudo systemctl start|stop|restart solarmon

To check the service status with:

    $ sudo systemctl status solarmon

To start the service at boot time:

    $ sudo systemctl enable solarmon

To disable the service from starting automatically:

    $ sudo systemctl disable huawei_sun2000
