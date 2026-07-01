#!/bin/bash

# suggested cron schedule: '0 0 1 * *' (at 00:00 on day-of-month 1)

INFLUX=/usr/local/bin/influx
BASE_DIR=/home/pi/solarmon/influxdb/backup
mkdir -p $BASE_DIR
BACKUP_DIR=$BASE_DIR/$(date '+%Y%m%d%H%M')
echo Creating InfluxDB backup $BACKUP_DIR...
$INFLUX backup $BACKUP_DIR -t <ROOT-TOKEN>
tar -zcvpf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR
