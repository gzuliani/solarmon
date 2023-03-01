import logging
from pymodbus.client.sync import ModbusSerialClient, ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

import clock


class Connection:

    def __init__(self, name, client, delay_between_reads=0):
        self._name = name
        self._client = client
        self._connected = False
        self._read_timer = clock.Timer(delay_between_reads)

    def connect(self):
        if not self._connected:
            logging.info('Connecting to "%s"...', self._name)
            try:
                if self._client.connect():
                    error = ''
                else:
                    error = 'unknown error'
            except Exception as e:
                error = str(e)
            if error:
                logging.info('Could not connect, reason: %s', error)
            else:
                self._connected = True
                logging.info('Connection established!')

    def disconnect(self):
        if self._connected:
            try:
                logging.info('Disconnecting from "%s"...', self._name)
                self._client.close()
                self._connected = False
                logging.info('Connection closed!')
            except Exception as e:
                logging.info('Could not disconnect, reason: %s...', e)

    def reconnect(self):
        self.disconnect()
        self.connect()

    def read_holding_registers(self, addr, count, timeout, unit):
        self._read_timer.wait_next_tick()
        return self._client.read_holding_registers(
                addr, count, timeout=timeout, unit=unit)

    def read_input_registers(self, addr, count, timeout, unit):
        self._read_timer.wait_next_tick()
        return self._client.read_input_registers(
                addr, count, timeout=timeout, unit=unit)


class UsbRtuAdapter(Connection):

    def __init__(self, port, delay_between_reads=0):
        super().__init__(port,
                ModbusSerialClient(method='rtu', port=port, baudrate=9600),
                delay_between_reads)


class TcpLink(Connection):

    def __init__(self, host, port):
        super().__init__('{}:{}'.format(host, port),
                ModbusTcpClient(host, port=port))


class Parameter:

    def __init__(self, name, regs):
        self.name = name
        self.regs = regs

    def decode(self, values):
        assert len(values) == len(self.regs)
        return self._decode(values)

    def _decode(self, values):
        raise NotImplementedError


class AsciiString:

    def __init__(self, name, addr, count):
        self.name = name
        self.regs = [x for x in range(addr, addr + count)]

    def decode(self, values):
        assert len(values) == len(self.regs)
        return ''.join([chr((x & 0xff00) >> 8) + chr(x & 0xff) for x in values])


class Number(Parameter):

    def __init__(self, name, unit, gain, bias, regs):
        super().__init__(name, regs)
        self.unit = unit
        self.gain = gain
        self.bias = bias

    def _decode(self, values):
        assert len(values) == len(self.regs)
        return (self._combine(values) - self.bias) / self.gain

    def _combine(self, values):
        raise NotImplementedError


class UnsignedShort(Number):

    def __init__(self, name, unit, gain, bias, addr):
        super().__init__(name, unit, gain, bias, [addr])

    def _combine(self, values):
        return values[0]


class SignedShort(Number):

    def __init__(self, name, unit, gain, bias, addr):
        super().__init__(name, unit, gain, bias, [addr])

    def _combine(self, values):
        result = values[0]
        if (result & 0x8000) == 0x8000:
            result = -((result ^ 0xffff) + 1)
        return result


class UnsignedLong(Number):

    def __init__(self, name, unit, gain, bias, hi_addr, lo_addr):
        super().__init__(name, unit, gain, bias, [hi_addr, lo_addr])

    def _combine(self, values):
        return values[0] * 65536 + values[1]


class UnsignedLongBE(UnsignedLong):

    def __init__(self, name, unit, gain, bias, addr):
        super().__init__(name, unit, gain, bias, addr, addr + 1)


class UnsignedLongLE(UnsignedLong):

    def __init__(self, name, unit, gain, bias, addr):
        super().__init__(name, unit, gain, bias, addr + 1, addr)


class SignedLong(Number):

    def __init__(self, name, unit, gain, bias, hi_addr, lo_addr):
        super().__init__(name, unit, gain, bias, [hi_addr, lo_addr])

    def _combine(self, values):
        result = values[0] * 65536 + values[1]
        if (result & 0x80000000) == 0x80000000:
            result = -((result ^ 0xffffffff) + 1)
        return result


class SignedLongBE(SignedLong):

    def __init__(self, name, unit, gain, bias, addr):
        super().__init__(name, unit, gain, bias, addr, addr + 1)


class SignedLongLE(SignedLong):

    def __init__(self, name, unit, gain, bias, addr):
        super().__init__(name, unit, gain, bias, addr + 1, addr)


class Float(Number):

    def __init__(self, name, unit, gain, bias, addr):
        super().__init__(name, unit, gain, bias, [addr, addr + 1])

    def _combine(self, values):
        return BinaryPayloadDecoder.fromRegisters(
                values, byteorder=Endian.Big, wordorder=Endian.Big
        ).decode_32bit_float()


class Device:

    def __init__(self, name, connection, addr, timeout):
        self.name = name
        self.addr = addr
        self._connection = connection
        self._timeout = timeout
        self._param_arrays = []
        self._sparse_params = []

    def params(self):
        return [
                x for array_ in self._param_arrays for x in array_
        ] + self._sparse_params

    def read(self):
        data = []
        for array_ in self._param_arrays:
            data.extend(self._read_param_array(array_))
        data.extend(self._read_sparse_params(self._sparse_params))
        return data

    def reconfigure(self):
        self._connection.reconnect()

    def _add_param_array(self, params):
        self._param_arrays.append(params)

    def _add_sparse_params(self, params):
        self._sparse_params.extend(params)

    def _read_param_array(self, params):
        regs = [r for p in params for r in p.regs]
        addr, count = self._to_range(regs)
        response = self._read_register_span(addr, count)
        data = []
        for p in params:
            values = self._extract_values(response, addr, p.regs)
            data.append(p.decode(values))
        return data

    def _read_sparse_params(self, params):
        data = []
        for p in params:
            response = self._read_param(p)
            values = self._extract_values(response, min(p.regs), p.regs)
            data.append(p.decode(values))
        return data

    def _read_param(self, param):
        addr, count = self._to_range(param.regs)
        return self._read_register_span(addr, count)

    def _read_register_span(self, addr, count):
        response = self._read_registers(addr, count, self._timeout, self.addr)
        if response.isError():
            raise RuntimeError(response)
        return response.registers

    def _read_registers(self, addr, count, timeout, unit):
        raise NotImplementedError

    @staticmethod
    def _to_range(regs):
        '''
        Given a list of register addresses
        return the lower one and the total number of registers.
        '''
        first, last = min(regs), max(regs)  # should do this in one pass!
        return first, last - first + 1

    @staticmethod
    def _extract_values(response, addr, regs):
        '''
        Given a list of register values and the address of the first one,
        extract all the values of the registers which address is given.
        '''
        return [response[r - addr] for r in regs]


class InputRegisters(Device):

    def __init__(self, name, connection, addr, timeout):
        super().__init__(name, connection, addr, timeout)

    def _read_registers(self, addr, count, timeout, unit):
        return self._connection.read_input_registers(
                addr, count, timeout, unit)


class HoldingRegisters(Device):

    def __init__(self, name, connection, addr, timeout):
        super().__init__(name, connection, addr, timeout)

    def _read_registers(self, addr, count, timeout, unit):
        return self._connection.read_holding_registers(
                addr, count, timeout, unit)


# abbreviations
ASC = AsciiString
I16 = SignedShort
U16 = UnsignedShort
I32 = SignedLongBE
U32 = UnsignedLongBE
F32 = Float
