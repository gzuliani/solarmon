import logging
import requests
import time

class InfluxDB:

    def __init__(self, api_base_uri, api_token, org, bucket):
        self.name = 'Influx'
        self._base_uri = api_base_uri \
            + f'/api/v2/write?org={org}&bucket={bucket}&precision=s'
        self._api_token = api_token
        self._param_names = {}

    def write(self, data, timestamp=None):
        if not timestamp:
            timestamp = int(time.time())
        for device, values in data:
            if not values:
                continue
            if not device.name in self._param_names:
                self._param_names[device.name] = [
                        x.name for x in device.params()]
            headers = {
                'Authorization': f'Token {self._api_token}',
                'Content-Type': 'text/plain; charset=utf-8',
                'Accept': 'application/json'
            }
            data = zip(self._param_names[device.name], values)
            data = ','.join([f'{k}={v}' for k, v in data])
            data = f'measurement,source={device.name} {data} {timestamp}'
            logging.debug('Sending "%s" to %s...', data, self._base_uri)
            response = requests.post(
                self._base_uri, headers=headers, data=data)
            if not response.status_code in [200, 204]:
                logging.warning('Unexpected InfluxDB response: %s - %s',
                        response.status_code, response.reason)
