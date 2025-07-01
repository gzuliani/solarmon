#!/bin/bash

# suggested cron schedule: '0 0 1 * *' (at 00:00 on day-of-month 1)

TARGET_DIR=/home/pi/solarmon/influxdb/backup
mkdir -p $TARGET_DIR
TARGET_FILE=$TARGET_DIR/$(date '+%Y%m%d%H%M')
echo Creating InfluxDB backup $TARGET_FILE...
/usr/local/bin/influx backup $TARGET_FILE -t <ROOT-TOKEN>
