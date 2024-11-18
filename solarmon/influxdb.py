import logging
import requests
import time


def quote_string(s):
    return '"{}"'.format(
        ' '.join(s.split()).translate(
            str.maketrans(
                {
                    # Do not change the order of transformations!
                    '\\': '\\\\',
                    '\"': '\\\"'
                })))


def quote_if_string(x):
    if isinstance(x, str):
        return quote_string(x)
    else:
        return x


class LineProtocol:
    def __init__(self, measurement):
        self._measurement = measurement

    def encode_error(self, unit, code, detail, timestamp):
        tags = {'source': 'program'}
        fields = {
            'unit': quote_string(unit),
            'code': quote_string(code),
            'detail': quote_string(detail),
        }
        return self._encode(tags, fields, timestamp)

    def encode_sample(self, sample, timestamp):
        device = sample.device
        params = [(p.name, 'u' if p.type == 'bit_field' else '')
                for p in device.params()]
        data = zip(params, sample.values)
        fields = dict((n, f'{quote_if_string(v)}{s}') for (n, s), v in data if v is not None)
        if fields:
            return self._encode({'source': device.name}, fields, timestamp)
        else:
            return None

    def _encode(self, tags, fields, timestamp):
        tags = ','.join(f'{k}={v}' for k, v in tags.items())
        fields = ','.join(f'{k}={v}' for k, v in fields.items())
        return f'{self._measurement},{tags} {fields} {timestamp}'


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
        self._protocol = LineProtocol(measurement)

    def write(self, samples, timestamp=None):
        if not timestamp:
            timestamp = int(time.time())
        for sample in samples:
            if sample.is_error():
                self._store_alert(sample, timestamp)
            else:
                self._store_data(sample, timestamp)

    def _store_alert(self, sample, timestamp):
        self._send_request(
            self._protocol.encode_error(
                sample.device.name, 'READ_ERROR', sample.error(), timestamp))

    def _store_data(self, sample, timestamp):
        data = self._protocol.encode_sample(sample, timestamp)
        if data:
            self._send_request(data)
        else:
            pass
            #logging.warning(
            #    'No data available for device "%s"...', sample.device.name)

    def _send_request(self, data):
        logging.debug('Sending "%s" to %s...', data, self._base_uri)
        response = requests.post(
            self._base_uri, headers=self._headers, data=data)
        if not response.status_code in [200, 204]:
            logging.warning('Unexpected InfluxDB response: %s - %s',
                    response.status_code, response.reason)
