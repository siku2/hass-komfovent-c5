import asyncio
import ctypes
import datetime
import itertools
from ipaddress import IPv4Address
from typing import Iterator, List, Tuple

from pymodbus.client.asynchronous.async_io import ReconnectingAsyncioModbusTcpClient
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

        #  TODO this needs to be done on every reconnect!
        if modbus_client.protocol:
            modbus_client.protocol._timeout = 20.0

        inst = cls()
        inst._modbus = modbus_client
        inst._lock = asyncio.Lock()
        return inst

    async def disconnect(self) -> None:
        async with self._lock:
            self._modbus.stop()

    async def read_u16(self, address: int) -> int:
        async with self._lock:
            rr: ReadHoldingRegistersResponse = (
                await self._modbus.protocol.read_holding_registers(address, count=1)
            )
        assert not rr.isError()
        return rr.registers[0]

    async def write_u16(self, address: int, value: int) -> None:
        async with self._lock:
            wr: WriteSingleRegisterResponse = (
                await self._modbus.protocol.write_register(address, value & 0xFFFF)
            )
        assert not wr.isError()

    async def read_u8_couple(self, address: int) -> Tuple[int, int]:
        value = await self.read_u16(address)
        return consume_u8_couple_from_u16(value)

    async def write_u8_couple(self, address: int, lo: int, hi: int) -> None:
        value = ((hi << 8) & 0xFF00) | (lo & 0x00FF)
        await self.write_u16(address, value)

    async def read_u32(self, address: int) -> int:
        async with self._lock:
            rr: ReadHoldingRegistersResponse = (
                await self._modbus.protocol.read_holding_registers(address, count=2)
            )
        assert not rr.isError()
        return consume_u32(iter(rr.registers))

    async def write_u32(self, address: int, value: int) -> None:
        lo = value & 0x0000FFFF
        hi = (value & 0xFFFF0000) >> 16
        async with self._lock:
            wr: WriteMultipleRegistersResponse = (
                await self._modbus.protocol.write_registers(address, (hi, lo))
            )
        assert not wr.isError()

    async def read_many_u16(self, address: int, count: int) -> List[int]:
        async with self._lock:
            rr: ReadHoldingRegistersResponse = (
                await self._modbus.protocol.read_holding_registers(address, count=count)
            )
        assert not rr.isError()
        return rr.registers


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
        hi, lo = next(registers), next(registers)
    except StopIteration:
        raise ValueError("missing register(s) to consume u32") from None
    return ((hi << 16) & 0xFFFF0000) | lo & 0x0000FFFF


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
