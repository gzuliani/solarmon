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
                logging.info('Connection closed!'.format())
            except Exception as e:
                logging.info('Could not disconnect, reason: %s...', e)

    def reconnect(self):
        self.disconnect()
        self.connect()


class Packet:

    FRAME_SIZE = 14

    def __init__(self, frame):
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


class Register:

    def __init__(self, name, type, unit, divisor, header, request):
        self.name = name
        self.type = type
        self.unit = unit
        self.divisor = divisor
        self.header = header
        self.request = request
        self.id = Packet(request).id

    def decode(self, data):
        assert len(data) == 4
        if self.type == 'float':
            value = self._to_signed_int32(data) / self.divisor
        elif self.type =='longint':
            value = self._to_signed_int32(data) // self.divisor
        elif self.type == 'int':
            value = int(data[:2], 16) // self.divisor
        else:
            raise RuntimeError('unsupported data type "{}"'.format(self.type))
        return value

    def _to_signed_int32(self, data):
        value = int(data, 16)
        if value < 32768:
            return value
        else:
            return 65536 - value


class Device:

    def __init__(self, name, connection):
        self.name = name
        self.connection = connection
        self._elm327 = ELM327(self.connection.serial)
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
        self._elm327.set_protocol_b_parameters(b'C0', b'19')
        self._elm327.set_protocol(b'b')


class Altherma(Device):

    def __init__(self, name, connection):
        Device.__init__(self, name, connection)
        self._registers = [
            Register('T-mandata',              'float',     'deg',   10, b'190', b'3100FA01D60000'),
            Register('T-mandata-SET',          'float',     'deg',   10, b'190', b'31000200000000'),
            Register('Pressione',              'float',     'bar', 1000, b'190', b'31001C00000000'),
            Register('T-ACS',                  'float',     'deg',   10, b'190', b'31000E00000000'),
            Register('T-ACS-SET',              'float',     'deg',   10, b'190', b'31000300000000'),
            Register('T-ritorno',              'float',     'deg',   10, b'190', b'31001600000000'),
            Register('Pompa-flusso',         'longint',      'lh',    1, b'190', b'3100FA01DA0000'),
         #  Register('status_pump',          'longint',        '',    1, b'190', b'3100FA0A8C0000'),
            Register('Tempo-compr',          'longint',    'hour',    1, b'190', b'3100FA06A50000'),
            Register('Tempo-pompa',          'longint',    'hour',    1, b'190', b'3100FA06A40000'),
            Register('Valvola-DHW',          'longint', 'percent',    1, b'190', b'3100FA069B0000'),
            Register('E-ACS-BUH',            'longint',     'kwh',    1, b'190', b'3100FA091C0000'),
            Register('E-risc-BUH',           'longint',     'kwh',    1, b'190', b'3100FA09200000'),
            Register('E-risc',               'longint',     'kwh',    1, b'190', b'3100FA06A70000'),
            Register('E-totale',             'longint',     'kwh',    1, b'190', b'3100FA09300000'),
            Register('E-ACS',                'longint',     'kwh',    1, b'190', b'3100FA092C0000'),
         #  Register('tvbh2',                  'float',     'deg',   10, b'190', b'3100FAC1020000'),
            Register('T-refrigerante',         'float',     'deg',   10, b'190', b'3100FAC1030000'),
         #  Register('tr2',                    'float',     'deg',   10, b'190', b'3100FAC1040000'),
         #  Register('tdhw2',                  'float',     'deg',   10, b'190', b'3100FAC1060000'),
            Register('Modo-operativo',       'longint',        '',    1, b'190', b'3100FAC0F60000'),
         #  Register('pump',                 'longint', 'percent',    1, b'190', b'3100FAC0F70000'),
            Register('P-BUH',                'longint',      'kw',    1, b'190', b'3100FAC0F90000'),
            Register('Valvola-B1',           'longint', 'percent',    1, b'190', b'3100FAC0FB0000'),
         #  Register('t_v1',                   'float',     'deg',   10, b'190', b'3100FAC0FC0000'),
         #  Register('t_dhw1',                 'float',     'deg',   10, b'190', b'3100FAC0FD0000'),
         #  Register('t_vbh',                  'float',     'deg',   10, b'190', b'3100FAC0FE0000'),
         #  Register('t_outdoor_ot1',          'float',     'deg',   10, b'190', b'3100FAC0FF0000'),
         #  Register('t_r1',                   'float',     'deg',   10, b'190', b'3100FAC1000000'),
         #  Register('v1',                   'longint',      'lh',    1, b'190', b'3100FAC1010000'),
            # parameter not found in zanac/Spanni26 code
            Register('E-totale-elettrica',   'longint',     'kWh',    1, b'190', b'3100FAC2FA0000'),
            # parameter not found in zanac/Spanni26 code
            Register('T-AU',                   'float',     'deg',   10, b'190', b'3100FAC1760000'),
            Register('T-est',                  'float',     'deg',   10, b'310', b'6100FA0A0C0000'),
            Register('T-mandata-CR-SET',       'float',     'deg',   10, b'310', b'61000400000000'),
            # parameter not found in zanac/Spanni26 code
            Register('Pompa-percentuale',    'longint', 'percent',    1, b'510', b'A100FAC10C0000'),
            Register('T-mandata-CR',           'float',     'deg',   10, b'610', b'C1000F00000000'),
        ]
        self._last_header = None

    def registers(self):
        return self._registers

    def peek(self):
        return [self._read(r) for r in self._registers]

    def _read(self, register):
        try:
            if register.header != self._last_header:
                self._last_header = register.header
                self._elm327.set_header(self._last_header)
            response = self._elm327.send_request(register.request)
            for frame in response:
                packet = Packet(frame)
                if not packet.is_response:
                    continue
                if packet.id == register.id:
                    return register.decode(packet.value)
        except Exception as e:
            logging.warning('Error "%s" while reading parameter "%s"...',
                e, register.name)
        return None


class CanBusMonitor(threading.Thread, Device):

    def __init__(self, name, connection):
        threading.Thread.__init__(self)
        Device.__init__(self, name, connection)
        self._stop_guard = threading.Event()
        self._lock = threading.Lock()
        self._registers = []
        self._pos_from_id = {}
        self._readings = []

    def set_registers(self, registers):
        self._registers = registers
        self._pos_from_id = dict([
            (Packet(x.request).id, i)
                for i, x in enumerate(self._registers)])
        self._readings = [None] * len(self._registers)

    def run(self):
        logging.info('Starting monitor...')
        self._elm327.start_monitor()
        logging.info('Monitor started')
        while not self._stop_guard.is_set():
            self._update_readings(self._elm327.consume())
        logging.info('Stopping monitor...')
        self._elm327.stop_monitor()
        logging.info('Monitor stopped')

    def terminate_and_wait(self):
        # signal the thread that is time to exit
        self._stop_guard.set()
        # wait the thread to terminate
        self.join()

    def registers(self):
        return self._registers

    def peek(self):
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
                    self._readings[i] = self._registers[i].decode(packet.value)
            except Exception as e:
                logging.warning('Packet "%s" refused, reason: %s', frame, e)
