import logging
import serial
import threading

from elm327 import ELM327


class SerialConnection:
    def __init__(self, port, baudrate):
        self._name = port
        self._baudrate = baudrate
        # do not open the serial port now!
        self.serial = serial.Serial(port=None, baudrate=baudrate, timeout=1)
        self.serial.port = port

    def connect(self):
        if not self.serial.is_open:
            logging.info('Connecting to "%s"...', self._name)
            try:
                self.serial.open()
                logging.info('Connection established!')
            except Exception as e:
                logging.info('Could not connect, reason: %s', e)

    def disconnect(self):
        if self.serial.is_open:
            try:
                logging.info('Disconnecting from "%s"...', self._name)
                self.serial.close()
                logging.info('Connection closed!')
            except Exception as e:
                logging.info('Could not disconnect, reason: %s...', e)

    def reconnect(self):
        self.disconnect()
        self.connect()


class Packet:
    FRAME_SIZE = 14

    def __init__(self, frame):
        self.id = None
        self.is_response = False
        if len(frame) != self.FRAME_SIZE:
            raise RuntimeError(
                'wrong size for frame {} (got {}, expected {})'.format(
                frame, len(frame), self.FRAME_SIZE))
        self.is_response = (frame[1] == 0x32) # '2'
        self.id = frame[4:6]
        if self.id == b'FA':
            self.id = frame[6:10]
            self.value = frame[10:14]
        else:
            self.value = frame[6:10]


class Parameter:
    def __init__(self, name, unit, header, request):
        self.name = name
        self.unit = unit
        self.header = header
        self.request = request
        self.id = Packet(request).id

    def decode(self, data):
        assert len(data) == 4
        return self._decode(data)

    def _decode(self, data):
        raise NotImplementedError


class MostSignificantByte(Parameter):
    def __init__(self, name, unit, header, request):
        super().__init__(name, unit, header, request)

    def _decode(self, data):
        return int(data[:2], 16)


class Word(Parameter):
    def __init__(self, name, unit, header, request):
        super().__init__(name, unit, header, request)

    def _to_signed_int(self, data):
        value = int(data, 16)
        if value < 32768:
            return value
        else:
            return value - 65536


class SignedInt(Word):
    def __init__(self, name, unit, divisor, header, request):
        super().__init__(name, unit, header, request)
        self.divisor = divisor

    def _decode(self, data):
        return self._to_signed_int(data) // self.divisor


class Float(Word):
    def __init__(self, name, unit, divisor, header, request):
        super().__init__(name, unit, header, request)
        self.divisor = divisor

    def _decode(self, data):
        return self._to_signed_int(data) / self.divisor


# abbreviations
MSB = MostSignificantByte
INT = SignedInt
FLT = Float


class UsbCanAdapter:
    def __init__(self, port, baudrate):
        self._connection = SerialConnection(port, baudrate)
        self._init()

    def connect(self):
        self._connection.connect()

    def disconnect(self):
        self._connection.connect()

    def reconfigure(self):
        self._connection.reconnect()
        self._init()

    def set_header(self, header):
        if not self._elm327:
            raise RuntimeError('OBD adapter not available')
        return self._elm327.set_header(header)

    def send_request(self, data):
        if not self._elm327:
            raise RuntimeError('OBD adapter not available')
        return self._elm327.send_request(data)

    def start_monitor(self):
        if not self._elm327:
            raise RuntimeError('OBD adapter not available')
        return self._elm327.start_monitor()

    def stop_monitor(self):
        if not self._elm327:
            raise RuntimeError('OBD adapter not available')
        return self._elm327.stop_monitor()

    def consume(self):
        if not self._elm327:
            raise RuntimeError('OBD adapter not available')
        return self._elm327.consume()

    def _init(self):
        try:
            self._elm327 = ELM327(self._connection.serial)
            self._elm327.warm_start()
            self._elm327.echo_off()
            self._elm327.linefeeds_off()
            self._elm327.spaces_off()
            self._elm327.headers_off()
            # C0:
            #  b7 = 1 -> transmit 11 bit ID
            #  b6 = 1 -> variable DLC
            #  b5 = 0 -> receive 11 bit ID
            #  b4 = 0 -> baud rate multiplier "x1"
            #  b3 = 0 -> (reserved)
            #  b2 = 0
            #  b1 = 0 -> data format "none"
            #  b0 = 0
            # 19: 20Kbps
            self._elm327.set_protocol_b_params(b'C0', b'19')
            self._elm327.set_protocol(b'b')
        except Exception as e:
            self._elm327 = None
            logging.warning('Error "%s" while initializing OBD adapter...', e)


class Device:
    def __init__(self, name, obd_adapter):
        self.name = name
        self._obd_adapter = obd_adapter

    def reconfigure(self):
        self._obd_adapter.reconfigure()


class Altherma(Device):
    def __init__(self, name, obd_adapter):
        super().__init__(name, obd_adapter)
        self._params = [
            FLT('T-mandata',                'deg',   10, b'190', b'3100FA01D60000'),
            FLT('T-mandata-SET',            'deg',   10, b'190', b'31000200000000'),
            FLT('Pressione',                'bar', 1000, b'190', b'31001C00000000'),
            FLT('T-ACS',                    'deg',   10, b'190', b'31000E00000000'),
            FLT('T-ACS-SET',                'deg',   10, b'190', b'31000300000000'),
            FLT('T-ritorno',                'deg',   10, b'190', b'31001600000000'),
            INT('Pompa-flusso',              'lh',    1, b'190', b'3100FA01DA0000'),
         #  INT('status_pump',                 '',    1, b'190', b'3100FA0A8C0000'),
            INT('Tempo-compr',             'hour',    1, b'190', b'3100FA06A50000'),
            INT('Tempo-pompa',             'hour',    1, b'190', b'3100FA06A40000'),
            INT('Valvola-DHW',          'percent',    1, b'190', b'3100FA069B0000'),
            INT('Termostato',                  '',    1, b'190', b'3100FA071B0000'),
            INT('E-ACS-BUH',                'kwh',    1, b'190', b'3100FA091C0000'),
            INT('E-risc-BUH',               'kwh',    1, b'190', b'3100FA09200000'),
            INT('E-risc',                   'kwh',    1, b'190', b'3100FA06A70000'),
            INT('E-totale',                 'kwh',    1, b'190', b'3100FA09300000'),
            INT('E-ACS',                    'kwh',    1, b'190', b'3100FA092C0000'),
         #  FLT('tvbh2',                    'deg',   10, b'190', b'3100FAC1020000'),
            FLT('T-refrigerante',           'deg',   10, b'190', b'3100FAC1030000'),
         #  FLT('tr2',                      'deg',   10, b'190', b'3100FAC1040000'),
         #  FLT('tdhw2',                    'deg',   10, b'190', b'3100FAC1060000'),
            INT('Modo-operativo',              '',    1, b'190', b'3100FAC0F60000'),
         #  INT('pump',                 'percent',    1, b'190', b'3100FAC0F70000'),
            INT('P-BUH',                     'kw',    1, b'190', b'3100FAC0F90000'),
            INT('Valvola-B1',           'percent',    1, b'190', b'3100FAC0FB0000'),
         #  FLT('t_v1',                     'deg',   10, b'190', b'3100FAC0FC0000'),
         #  FLT('t_dhw1',                   'deg',   10, b'190', b'3100FAC0FD0000'),
         #  FLT('t_vbh',                    'deg',   10, b'190', b'3100FAC0FE0000'),
         #  FLT('t_outdoor_ot1',            'deg',   10, b'190', b'3100FAC0FF0000'),
         #  FLT('t_r1',                     'deg',   10, b'190', b'3100FAC1000000'),
         #  INT('v1',                        'lh',    1, b'190', b'3100FAC1010000'),
            # parameter not found in zanac/Spanni26 code
            INT('E-totale-elettrica',       'kWh',    1, b'190', b'3100FAC2FA0000'),
            # parameter not found in zanac/Spanni26 code
            FLT('T-AU',                     'deg',   10, b'190', b'3100FAC1760000'),
            FLT('T-est',                    'deg',   10, b'310', b'6100FA0A0C0000'),
            FLT('T-mandata-CR-SET',         'deg',   10, b'310', b'61000400000000'),
            # parameter not found in zanac/Spanni26 code
            INT('Pompa-percentuale',    'percent',    1, b'510', b'A100FAC10C0000'),
            FLT('T-mandata-CR',             'deg',   10, b'610', b'C1000F00000000'),
        ]
        self._last_header = None

    def params(self):
        return self._params

    def read(self):
        return [self._read(r) for r in self._params]

    def _read(self, param):
        if param.header != self._last_header:
            self._last_header = param.header
            self._obd_adapter.set_header(self._last_header)
        response = self._obd_adapter.send_request(param.request)
        try:
            for frame in response:
                packet = Packet(frame)
                if not packet.is_response:
                    continue
                if packet.id == param.id:
                    return param.decode(packet.value)
        except Exception as e:
            logging.warning('Error "%s" while reading parameter "%s"...',
                e, param.name)
        return None


class CanBusMonitor(threading.Thread, Device):
    def __init__(self, name, obd_adapter):
        threading.Thread.__init__(self)
        Device.__init__(self, name, obd_adapter)
        self._stop_guard = threading.Event()
        self._lock = threading.Lock()
        self._params = []
        self._pos_from_id = {}
        self._readings = []

    def set_params(self, params):
        self._params = params
        self._pos_from_id = dict([
            (Packet(x.request).id, i)
                for i, x in enumerate(self._params)])
        self._readings = [None] * len(self._params)

    def run(self):
        logging.info('Starting monitor...')
        self._obd_adapter.start_monitor()
        logging.info('Monitor started')
        while not self._stop_guard.is_set():
            self._update_readings(self._obd_adapter.consume())
        logging.info('Stopping monitor...')
        self._obd_adapter.stop_monitor()
        logging.info('Monitor stopped')

    def terminate_and_wait(self):
        # signal the thread that is time to exit
        self._stop_guard.set()
        # wait the thread to terminate
        self.join()

    def params(self):
        return self._params

    def read(self):
        with self._lock:
            return self._readings

    def _update_readings(self, frames):
        for frame in frames:
            try:
                packet = Packet(frame)
                if not packet.is_response:
                    continue
                if not packet.id in self._pos_from_id:
                    continue
                i = self._pos_from_id[packet.id]
                with self._lock:
                    self._readings[i] = self._params[i].decode(packet.value)
            except Exception as e:
                logging.warning('Packet "%s" refused, reason: %s', frame, e)
