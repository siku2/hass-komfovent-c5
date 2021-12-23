import asyncio
import ctypes
import datetime
import itertools
from ipaddress import IPv4Address
from typing import Iterator, List, Tuple

from pymodbus.client.asynchronous.async_io import (
    ModbusClientProtocol,
    ReconnectingAsyncioModbusTcpClient,
)
from pymodbus.register_read_message import ReadHoldingRegistersResponse
from pymodbus.register_write_message import (
    WriteMultipleRegistersResponse,
    WriteSingleRegisterResponse,
)


class Client:
    _modbus: ReconnectingAsyncioModbusTcpClient
    _lock: asyncio.Lock

    @classmethod
    async def connect(cls, host: str, port: int, connect_timeout: float = None):
        modbus_client = ReconnectingAsyncioModbusTcpClient(
            protocol_class=None, loop=asyncio.get_running_loop()
        )
        await asyncio.wait_for(modbus_client.start(host, port), timeout=connect_timeout)

        inst = cls()
        inst._modbus = modbus_client
        inst._lock = asyncio.Lock()
        return inst

    async def _protocol(self) -> ModbusClientProtocol:
        modbus = self._modbus
        if modbus.protocol is None or not modbus.connected:
            # let's try to connect manually and see what's going on
            # TODO: let's just patch the connection_made method of self._modbus so that
            #       we know when the connection is established and use that to resume here
            await modbus.loop.create_connection(
                modbus._create_protocol, modbus.host, modbus.port
            )
        return modbus.protocol

    async def disconnect(self) -> None:
        async with self._lock:
            self._modbus.stop()

    async def read_u16(self, address: int) -> int:
        async with self._lock:
            protocol = await self._protocol()
            read_response: ReadHoldingRegistersResponse = (
                await protocol.read_holding_registers(address, count=1)
            )
        assert not read_response.isError()
        return read_response.registers[0]

    async def write_u16(self, address: int, value: int) -> None:
        async with self._lock:
            protocol = await self._protocol()
            write_response: WriteSingleRegisterResponse = await protocol.write_register(
                address, value & 0xFFFF
            )
        assert not write_response.isError()

    async def read_u8_couple(self, address: int) -> Tuple[int, int]:
        value = await self.read_u16(address)
        return consume_u8_couple_from_u16(value)

    async def write_u8_couple(
        self, address: int, low_byte: int, high_byte: int
    ) -> None:
        value = ((high_byte << 8) & 0xFF00) | (low_byte & 0x00FF)
        await self.write_u16(address, value)

    async def read_u32(self, address: int) -> int:
        async with self._lock:
            protocol = await self._protocol()
            read_response: ReadHoldingRegistersResponse = (
                await protocol.read_holding_registers(address, count=2)
            )
        assert not read_response.isError()
        return consume_u32(iter(read_response.registers))

    async def write_u32(self, address: int, value: int) -> None:
        low_register = value & 0x0000FFFF
        high_register = (value & 0xFFFF0000) >> 16
        async with self._lock:
            protocol = await self._protocol()
            write_response: WriteMultipleRegistersResponse = (
                await protocol.write_registers(address, (high_register, low_register))
            )
        assert not write_response.isError()

    async def read_many_u16(self, address: int, count: int) -> List[int]:
        async with self._lock:
            protocol = await self._protocol()
            read_respones: ReadHoldingRegistersResponse = (
                await protocol.read_holding_registers(address, count=count)
            )
        assert not read_respones.isError()
        return read_respones.registers


def consume_u16(registers: Iterator[int]) -> int:
    try:
        return next(registers)
    except StopIteration:
        raise ValueError("missing register to consume u16") from None


def consume_i16(registers: Iterator[int]) -> int:
    raw = consume_u16(registers)
    return ctypes.c_int16(raw).value


def consume_u8_couple_from_u16(register: int) -> Tuple[int, int]:
    return (register & 0xFF00) >> 8, register & 0x00FF


def consume_u8_couple(registers: Iterator[int]) -> Tuple[int, int]:
    value = consume_u16(registers)
    return consume_u8_couple_from_u16(value)


def consume_u32(registers: Iterator[int]) -> int:
    try:
        high_register, low_register = next(registers), next(registers)
    except StopIteration:
        raise ValueError("missing register(s) to consume u32") from None
    return ((high_register << 16) & 0xFFFF0000) | low_register & 0x0000FFFF


def consume_string(registers: Iterator[int], length: int) -> str:
    # preemtively consume all bytes since we need to consume `length` registers
    raw = [b for _ in range(length) for b in consume_u8_couple(registers)]
    # create a string from the bytes until the first NULL
    return "".join(map(chr, itertools.takewhile(lambda b: b != 0, raw)))


def consume_ip_address(
    registers: Iterator[int],
) -> IPv4Address:
    raw = consume_u32(registers)
    return IPv4Address(raw)


def consume_time(registers: Iterator[int], *, read_seconds: bool) -> datetime.time:
    hour, minute = consume_u8_couple(registers)
    second = 0
    if read_seconds:
        second = consume_u16(registers)
    return datetime.time(hour=hour, minute=minute, second=second)


def consume_date(registers: Iterator[int]) -> datetime.date:
    month, day = consume_u8_couple(registers)
    year = consume_u16(registers)
    return datetime.date(year=year, month=month, day=day)
