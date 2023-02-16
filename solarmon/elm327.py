import logging
import time


class ELM327:

    def __init__(self, port):
        self._port = port
        self._is_monitoring = False

    def reset(self):
        return self._exec(b'ATZ') # expected reply is 'ELM327 vX.Y'
        #
        # >    >AT Z
        # >
        # >It takes approximately one second for the IC to
        # >perform this reset, initialize everything and then test
        # >the four status LEDs in sequence.
        #
        # (see "Restoring Order", page 52 of the ELM327 datasheet)
        time.sleep(1)

    def warm_start(self):
        return self._exec(b'ATWS') # expected reply is 'ELM327 vX.Y'

    def set_defaults(self):
        return self._exec(b'ATD')

    def echo_on(self):
        return self._exec(b'ATE1')

    def echo_off(self):
        return self._exec(b'ATE0')

    def linefeeds_on(self):
        return self._exec(b'ATL1')

    def linefeeds_off(self):
        return self._exec(b'ATL0')

    def spaces_on(self):
        return self._exec(b'ATS1')

    def spaces_off(self):
        return self._exec(b'ATS0')

    def headers_on(self):
        return self._exec(b'ATH1')

    def headers_off(self):
        return self._exec(b'ATH0')

    def start_monitor(self):
        if not self._is_monitoring:
            self._exec(b'ATMA')
            self._is_monitoring = True

    def stop_monitor(self):
        # >To stop monitoring, simply send any single
        # >character to the ELM327, then wait for it to respond
        # >with a prompt character ('>'), or a low level output on
        # >the Busy pin. (Setting the RTS input to a low level will
        # >interrupt the device as well.) Waiting for the prompt is
        # >necessary as the response time varies depending on
        # >what the IC was doing when it was interrupted.
        #
        # (see "MA [Monitor All messages]", page 22 of the ELM327 datasheet)
        if self._is_monitoring:
            self._send(b'A')
            self._recv() # expected reply ends with 'STOPPED'

    def is_monitoring(self):
        return self._is_monitoring

    def consume(self):
        if not self._is_monitoring:
            return None
        return self._recv(b'\r')

    def set_protocol_b_params(self, xx, yy):
        #
        # xx
        #
        #     b7: Transmit ID Length   0: 29 bit ID,   1: 11 bit ID
        #     b6: Data Length          0: fixed 8 byte 1: variable DLC
        #     b5: Receive ID Length    0: as set by b7 1: both 11 and 29 bit
        #     b4: baud rate multiplier 0: x1           1: x 8/7 (see note 3)
        #     b3: reserved for future - leave set at 0.
        #     b2, b1, and b0 determine the data formatting options:
        #     0 0 0: none
        #     0 0 1: ISO 15765-4
        #     0 1 0: SAE J1939
        #
        # yy
        #
        #     baud rate (in kbps) = 500 / yy
        return self._exec(b'ATPB' + xx + yy)

    def set_protocol(self, id):
        return self._exec(b'ATSP' + id)

    def set_header(self, header):
        return self._exec(b'ATSH' + header)

    def send_request(self, data):
        return self._exec(data)

    def _exec(self, command):
        self._send(command + b'\r')
        return self._recv()

    def _send(self, data):
        logging.debug('Sending %s...', str(data))
        self._port.write(data)

    def _recv(self, sentinel=b'>'):
        incoming = self._port.read_until(sentinel)
        # >There is a very small chance that NULL characters (byte value 00)
        # >may occasionally be inserted into the RS232 data that is transmitted
        # >by the ELM327.
        #
        # (see note on page 9 of the ELM327 datasheet)
        data = incoming.replace(b'\x00', b'')
        logging.debug('Received: %s', str(data))
        data = data[:-1] # remove the sentinel
        return [x for x in data.split(b'\r') if x]
