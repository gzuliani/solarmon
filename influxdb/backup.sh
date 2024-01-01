#!/bin/bash

# suggested cron schedule: '0 3 1 1,4,7,10 *' (every 3 months at 03:00)

TARGET_DIR=/home/pi/solarmon/influxdb/backup
mkdir -p $TARGET_DIR
TARGET_FILE=$TARGET_DIR/$(date '+%Y%m%d%H%M')
echo Creating InfluxDB backup $TARGET_FILE...
influx backup $TARGET_FILE -t <ROOT-TOKEN>
