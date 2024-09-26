#!/bin/bash

sudo systemctl stop grafana-server
sudo cp /var/lib/grafana/grafana.db .
sudo systemctl start grafana-server
sudo chown pi:pi grafana.db
