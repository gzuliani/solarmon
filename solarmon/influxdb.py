import logging
import requests
import time

class InfluxDB:

    def __init__(self, api_base_uri, api_token, org, bucket,
                 measurement='measurement'):
        self.name = 'Influx'
        self._base_uri = api_base_uri + \
            f'/api/v2/write?org={org}&bucket={bucket}&precision=s'
        self._headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': 'text/plain; charset=utf-8',
            'Accept': 'application/json'
        }
        self._measurement = measurement
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
            data = zip(self._param_names[device.name], values)
            data = ','.join([f'{k}={v}' for k, v in data if v is not None])
            if not data:
                logging.warning('No data available for device "%s"...', device.name)
                continue
            data = f'{self._measurement},source={device.name} {data} {timestamp}'
            logging.debug('Sending "%s" to %s...', data, self._base_uri)
            response = requests.post(
                self._base_uri, headers=self._headers, data=data)
            if not response.status_code in [200, 204]:
                logging.warning('Unexpected InfluxDB response: %s - %s',
                        response.status_code, response.reason)
