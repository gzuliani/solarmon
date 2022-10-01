import json
import logging
import requests


class EmonCMS:

    def __init__(self, api_base_uri, api_key):
        self.name = 'EmonCMS'
        self._base_uri = api_base_uri + '/input/post.json'
        self._api_key = api_key
        self._register_names = {}

    def write(self, data):
        for device, values in data:
            if not device.name in self._register_names:
                self._register_names[device.name] = [
                        x.name for x in device.registers()]
            response = requests.post(self._base_uri, data={
                'node': device.name,
                'apikey': self._api_key,
                'json': json.dumps(dict(zip(
                        self._register_names[device.name], values)))})
            if response.reason != 'OK':
                logging.warning('Unexpected EmonCMS response: {} - {}'.format(
                    response.status_code, response.reason))
