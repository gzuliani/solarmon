import json
import logging
import requests

class EmonCMS:

    def __init__(self, api_base_uri, api_key):
        self._base_uri = api_base_uri + '/input/post.json'
        self._api_key = api_key

    def send(self, sample, node_number):
        response = requests.post(self._base_uri, data={
            'node': node_number,
            'apikey': self._api_key,
            'json': json.dumps(dict([(s[0], s[1]) for s in sample]))})
        if response.reason != 'OK':
            logging.warning('EmonCMS responded {} - {}'.format(
                response.status_code, response.reason))
