# logrotate

Copy the `solarmon` file in the `/etc/logrotate.d` and assign it to the `root` user and group:

    pi@raspberrypi:~ $ sudo chown root:root /etc/logrotate.d/solarmon

To check if the configuration is ok:

    pi@raspberrypi:~ $ sudo /usr/sbin/logrotate -d /etc/logrotate.d/solarmon

or

    pi@raspberrypi:~ $ sudo /usr/sbin/logrotate -d /etc/logrotate.conf

to consider the global options too.

To check the last time logrotate run on the `/var/log/solarmon.log` file:

    pi@raspberrypi:~ $ cat /var/lib/logrotate/status | grep solarmon
