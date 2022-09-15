import logging
from pymodbus.client.sync import ModbusSerialClient, ModbusTcpClient

import clock


class Connection:

    def __init__(self, name, client, delay_between_reads = 0):
        self._name = name
        self._client = client
        self._connected = False
        self._read_timer = clock.Timer(delay_between_reads)

    def connect(self):
        if not self._connected:
            logging.info('Connecting to {}...'.format(self._name))
            try:
                if self._client.connect():
                    error = ''
                else:
                    error = 'unknown error'
            except Exception as e:
                error = str(e)
            if error:
                logging.info('Could not connect, reason: {}'.format(error))
            else:
                self._connected = True
                logging.info('Connection established!')

    def disconnect(self):
        if self._connected:
            try:
                logging.info('Disconnecting from {}...'.format(self._name))
                self._client.close()
                self._connected = False
                logging.info('Connection closed!'.format())
            except Exception as e:
                logging.info('Could not disconnect, reason: {}...'.format(e))

    def reconnect(self):
        self.disconnect()
        self.connect()

    def read_holding_registers(self, addr, size, timeout, unit):
        self._read_timer.wait_next_tick()
        return self._client.read_holding_registers(
                addr, size, timeout=timeout, unit=unit)


class UsbRtuAdapter(Connection):

    def __init__(self, port, delay_between_reads = 0):
        Connection.__init__(self, port,
                ModbusSerialClient(method='rtu', port=port, baudrate=9600),
                delay_between_reads)


class TcpLink(Connection):

    def __init__(self, host, port):
        Connection.__init__(self, '{}:{}'.format(host, port),
                ModbusTcpClient(host, port=port))


class Register:

    def __init__(self, name, type, unit, gain, addr, size):
        self.name = name
        self. type = type
        self.unit = unit
        self.gain = gain
        self.addr = addr
        self.size = size

    def decode(self, values):
        assert len(values) == self.size
        if self.type == 'U32':
            result = self._to_uint32(values)
        elif self.type == 'I32':
            result = self._to_int32(values)
        elif self.type == 'U16':
            result = self._to_uint16(values)
        elif self.type == 'I16':
            result = self._to_int16(values)
        else:
            raise RuntimeError('unsupported type {}'.format(self.type))
        return result / self.gain

    def _to_uint32(self, values):
        assert len(values) == 2
        return values[0] * 65536 + values[1]

    def _to_int32(self, values):
        result = self._to_uint32(values)
        if (result & 0x80000000) == 0x80000000:
            result = -((result ^ 0xFFFFFFFF) + 1)
        return result

    def _to_uint16(self, values):
        assert len(values) == 1
        return values[0]

    def _to_int16(self, values):
        result = self._to_uint16(values)
        if (result & 0x8000) == 0x8000:
            result = -((result ^ 0xFFFF) + 1)
        return result


class Device:

    def __init__(self, name, connection, addr, timeout):
        self.name = name
        self.addr = addr
        self.connection = connection
        self._timeout = timeout
        self._register_arrays = []
        self._sparse_registers = []

    def registers(self):
        return [
                x for array in self._register_arrays for x in array
        ] + self._sparse_registers

    def peek(self):
        data = []
        for array in self._register_arrays:
            data.extend(self._read_register_array(array))
        data.extend(self._read_sparse_registers(self._sparse_registers))
        return data

    def _add_register_array(self, registers):
        self._register_arrays.append(registers)

    def _add_sparse_registers(self, registers):
        self._sparse_registers.extend(registers)

    def _read_register_array(self, registers):
        base_addr = min(r.addr for r in registers)
        past_last_addr = max(r.addr + r.size for r in registers)
        size = past_last_addr - base_addr
        response = self._read_holding_registers(base_addr, size)
        data = []
        for r in registers:
            pos = r.addr - base_addr
            data.append(r.decode(response[pos:pos + r.size]))
        return data

    def _read_sparse_registers(self, registers):
        return [r.decode(self._read_register_value(r)) for r in registers]

    def _read_register_value(self, register):
        return self._read_holding_registers(register.addr, register.size)

    def _read_holding_registers(self, addr, size):
        response = self.connection.read_holding_registers(
                addr, size, self._timeout, unit=self.addr)
        if response.isError():
            raise RuntimeError(response)
        return response.registers
