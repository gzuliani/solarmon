from collections import namedtuple

Register = namedtuple("Register", "name code type unit gain addr size")


class Connection:

    def __init__(self, addr, client):
        self.addr = addr
        self.modbus_client = client


class Device:

    def __init__(self, connection, timeout):
        self.addr = connection.addr
        self._client = connection.modbus_client
        self._timeout = timeout

    def read_registers(self):
        raise NotImplementedError

    def register_count(self):
        raise NotImplementedError

    def _read_register_array(self, registers):
        base_addr = min(r.addr for r in registers)
        past_last_addr = max(r.addr + r.size for r in registers)
        size = past_last_addr - base_addr
        response = self._read_holding_registers(base_addr, size)
        values = []
        for r in registers:
            pos = r.addr - base_addr
            values.append(response[pos:pos + r.size])
        return self._decode_register_values(registers, values)

    def _read_registers_one_by_one(self, registers):
        values = [self._read_register_value(r) for r in registers]
        return self._decode_register_values(registers, values)

    def _decode_register_values(self, registers, values):
        return [(r.code, self._decode(v, r.type, r.gain), r.unit)
                for r, v in zip(registers, values)]

    def _read_register_value(self, register):
        return self._read_holding_registers(register.addr, register.size)

    def _read_holding_registers(self, addr, size):
        response = self._client.read_holding_registers(
                addr, size, timeout=self._timeout, unit=self.addr)
        if response.isError():
            raise RuntimeError(response)
        return response.registers

    def _decode(self, registers, type, gain):
        if type == 'U32':
            value = self._to_uint32(registers)
        elif type == 'I32':
            value = self._to_int32(registers)
        elif type == 'U16':
            value = self._to_uint16(registers)
        elif type == 'I16':
            value = self._to_int16(registers)
        else:
            raise RuntimeError('unsupported type {}'.format(type))
        return value / gain

    def _to_uint32(self, registers):
        assert len(registers) == 2
        return registers[0] * 65536 + registers[1]

    def _to_int32(self, registers):
        value = self._to_uint32(registers)
        if (value & 0x80000000) == 0x80000000:
            value = -((value ^ 0xFFFFFFFF) + 1)
        return value

    def _to_uint16(self, registers):
        assert len(registers) == 1
        return registers[0]

    def _to_int16(self, registers):
        value = self._to_uint16(registers)
        if (value & 0x8000) == 0x8000:
            value = -((value ^ 0xFFFF) + 1)
        return value
