import datetime
import logging
import urllib
import urllib.request
import re


class Param:

    def __init__(self, name, tag, factory):
        self.name = name
        self.tag = tag
        self.factory = factory


class OsmerFvg:

    BASE_URI = 'https://dev.meteo.fvg.it/xml/stazioni'


# <suggested_pickup>30 minuti dopo l'ora</suggested_pickup>
# <suggested_pickup_period>60</suggested_pickup_period>
# il dato giornaliero di radiazione equivale alla somma dei 24 dati orari

    def __init__(self, name, station_code):
        self.name = name
        self._uri = '{}/{}.xml'.format(self.BASE_URI, station_code)
        self._timeout = 3
        self._params = [
            Param('time', 'observation_time', str),
            Param('temp', 't180', float),
#            Param('cloudiness', 'cloudiness', int),
            Param('radiation', 'rg', float),
            Param('humidity', 'rh', float),
            Param('pressure', 'press', float),
        ]
        self._reading_interval = 1200 # seconds between two consecutive readings
        self._last_reading_time = None
        self._last_observation_time = None

    def reconfigure(self):
        pass

    def params(self):
        return self._params

    def read(self):
        now = datetime.datetime.now()
        if self._last_reading_time is not None:
            elapsed = now - self._last_reading_time
            if elapsed.total_seconds() < self._reading_interval:
                return self._empty_sample()
        self._last_reading_time = now
        logging.debug('Connecting to "%s"...', self._uri)
        request = urllib.request.Request(self._uri, method='GET')
        resource = urllib.request.urlopen(request, timeout=self._timeout)
        return self._decode(resource.read())

    def _decode(self, response):
        values = []
        response.decode()
        for param in self._params:
            value = self._extract_param(param.tag, response)
            if param.name == 'time':
                if value == self._last_observation_time:
                    logging.debug('Got the previous sample, ignoring it...')
                    return self._empty_sample()
                self._last_observation_time = value
            values.append(param.factory(value))
        return values

    def _extract_param(self, tag, response):
        match = re.search('<{0}\s*[^>]*>([^<]*)</{0}>'.format(tag), str(response))
        return match.group(1) if match else None

    def _empty_sample(self):
        return [None] * len(self._params)
