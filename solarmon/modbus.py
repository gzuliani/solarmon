from collections import namedtuple


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


class Connection:

    def __init__(self, addr, client):
        self.addr = addr
        self.modbus_client = client


class Device:

    def __init__(self, connection, timeout):
        self.addr = connection.addr
        self._client = connection.modbus_client
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
        response = self._client.read_holding_registers(
                addr, size, timeout=self._timeout, unit=self.addr)
        if response.isError():
            raise RuntimeError(response)
        return response.registers
