import datetime
import logging
import urllib
import urllib.request
import xml.dom.minidom


class StationXmlData:

    def __init__(self, data):
        dom = xml.dom.minidom.parseString(data)
        self._data = dom.getElementsByTagName('data')[0]

    def hourly_data(self):
        hourly_data = {}
        meteo_data = self._data.getElementsByTagName('meteo_data')[0]
        for child in meteo_data.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            elif child.nodeName in ['observation_time']:
                hourly_data[child.nodeName] = self._text(child)
            elif child.nodeName in ['t180', 'rg', 'rh', 'press']:
                hourly_data[child.nodeName] = float(self._text(child))
        return hourly_data

    def _text(self, node):
        return ''.join(
            x.data for x in node.childNodes if x.nodeType == x.TEXT_NODE)


class Param:

    def __init__(self, name, tag):
        self.name = name
        self.tag = tag


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
            Param('time', 'observation_time'),
            Param('temp', 't180'),
            Param('radiation', 'rg'),
            Param('humidity', 'rh'),
            Param('pressure', 'press'),
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
        data = StationXmlData(response.decode()).hourly_data()
        for param in self._params:
            value = data[param.tag]
            if param.name == 'time':
                if value == self._last_observation_time:
                    logging.debug('Got the previous sample, ignoring it...')
                    return self._empty_sample()
                self._last_observation_time = value
            values.append(value)
        return values

    def _empty_sample(self):
        return [None] * len(self._params)
