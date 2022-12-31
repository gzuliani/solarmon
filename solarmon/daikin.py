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
            logging.info('Connecting to {}...'.format(self._name))
            try:
                self.serial.open()
                logging.info('Connection established!')
            except Exception as e:
                logging.info('Could not connect, reason: {}'.format(e))

    def disconnect(self):
        if self.serial.is_open:
            try:
                logging.info('Disconnecting from {}...'.format(self._name))
                self.serial.close()
                logging.info('Connection closed!'.format())
            except Exception as e:
                logging.info('Could not disconnect, reason: {}...'.format(e))

    def reconnect(self):
        self.disconnect()
        self.connect()


class Register:

    def __init__(self, name, type, unit, divisor, header, payload):
        self.name = name
        self. type = type
        self.unit = unit
        self.divisor = divisor
        self.header = header
        self.payload = payload

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


class Packet:

    FRAME_SIZE = 14

    def __init__(self, frame):
        if len(frame) != self.FRAME_SIZE:
            raise RuntimeError(
                'invalid frame size (got {}, expected {})'.format(
                len(frame), FRAME_SIZE))
        self.is_response = (frame[0] == 0x32) # '2'
        self.id = frame[4:6]
        if self.id == b'FA':
            self.id = frame[6:10]
            self.value = frame[10:14]
        else:
            self.value = frame[6:10]


class ObdSniffer(threading.Thread):

    def __init__(self, name, connection):
        threading.Thread.__init__(self)
        self.name = name
        self.connection = connection
        self._elm327 = ELM327(self.connection.serial)
        self._elm327.warm_start()
        self._elm327.echo_off()
        self._elm327.linefeeds_off()
        self._elm327.spaces_off()
        self._elm327.headers_off()
        self._elm327.set_protocol_b_parameters('E0', '19') # 20kbps
        self._elm327.set_protocol('b')
        self._stop_guard = threading.Event()
        self._lock = threading.Lock()
        self._registers = []
        self._pos_from_id = []
        self._readings = []

    def set_registers(self, registers):
        self._registers = registers
        self._pos_from_id = dict([
            (Packet(x.payload).id, i)
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
                logging.warning('Packet "{}" refused, reason: {}', packet, str(e))
