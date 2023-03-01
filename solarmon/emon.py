import json
import logging
import requests


class EmonCMS:

    def __init__(self, api_base_uri, api_key, json_variant='json'):
        self.name = 'EmonCMS'
        self._base_uri = api_base_uri + '/input/post.json'
        self._api_key = api_key
        self._json_variant = json_variant
        self._param_names = {}

    def write(self, data):
        for device, values in data:
            if not values:
                continue
            if not device.name in self._param_names:
                self._param_names[device.name] = [
                        x.name for x in device.params()]
            sample_as_json = json.dumps(dict(zip(
                    self._param_names[device.name], values)))
            logging.debug('Sending "%s" to EmonCMS...', sample_as_json)
            response = requests.post(self._base_uri, data={
                'node': device.name,
                'apikey': self._api_key,
                self._json_variant: sample_as_json})
            logging.debug('EmonCMS responded %s - %s',
                    response.status_code, response.reason)
            if response.reason != 'OK':
                logging.warning('Unexpected EmonCMS response: %s - %s',
                        response.status_code, response.reason)
