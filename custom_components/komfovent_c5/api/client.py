import asyncio
import ctypes
import datetime
import itertools
import logging
from collections.abc import Iterator
from ipaddress import IPv4Address
from typing import TYPE_CHECKING, cast

from pymodbus.client import AsyncModbusTcpClient

if TYPE_CHECKING:
    from pymodbus.pdu.register_message import (
        ReadHoldingRegistersResponse,
        WriteMultipleRegistersResponse,
        WriteSingleRegisterResponse,
    )

_LOGGER = logging.getLogger(__name__)


class Client:
    _modbus: AsyncModbusTcpClient
    _lock: asyncio.Lock
    _addr: tuple[str, int]

    def __init__(self, *, host: str, port: int) -> None:
        self._addr = (host, port)
        self._modbus = AsyncModbusTcpClient(host, port=port)
        self._lock = asyncio.Lock()

    @property
    def host_and_port(self) -> tuple[str, int]:
        return self._addr

    async def connect(self, connect_timeout: float | None = None) -> None:
        if self._modbus.connected:
            return
        async with self._lock:
            if connect_timeout is not None:
                self._modbus.comm_params.timeout_connect = connect_timeout
            _LOGGER.debug("connecting to %s", self.host_and_port)
            await self._modbus.connect()
            # the 'connect' function doesn't bubble the exception unfortunately
            if not self._modbus.connected:
                raise ConnectionError("failed to connect")

    async def disconnect(self) -> None:
        async with self._lock:
            _LOGGER.debug("closing the connection")
            self._modbus.close()

    async def read_u16(self, address: int) -> int:
        async with self._lock:
            read_response = cast(
                "ReadHoldingRegistersResponse",
                await self._modbus.read_holding_registers(address, count=1),
            )
        assert not read_response.isError()
        return read_response.registers[0]

    async def write_u16(self, address: int, value: int) -> None:
        async with self._lock:
            write_response = cast(
                "WriteSingleRegisterResponse",
                await self._modbus.write_register(address, value & 0xFFFF),
            )
        assert not write_response.isError()

    async def read_u8_couple(self, address: int) -> tuple[int, int]:
        value = await self.read_u16(address)
        return consume_u8_couple_from_u16(value)

    async def write_u8_couple(
        self, address: int, low_byte: int, high_byte: int
    ) -> None:
        value = ((high_byte << 8) & 0xFF00) | (low_byte & 0x00FF)
        await self.write_u16(address, value)

    async def read_u32(self, address: int) -> int:
        async with self._lock:
            read_response = cast(
                "ReadHoldingRegistersResponse",
                await self._modbus.read_holding_registers(address, count=2),
            )
        assert not read_response.isError()
        return consume_u32(iter(read_response.registers))

    async def write_u32(self, address: int, value: int) -> None:
        low_register = value & 0x0000FFFF
        high_register = (value & 0xFFFF0000) >> 16
        async with self._lock:
            write_response = cast(
                "WriteMultipleRegistersResponse",
                await self._modbus.write_registers(
                    address,
                    (high_register, low_register),  # type: ignore
                ),
            )
        assert not write_response.isError()

    async def _read_batch(self, address: int, count: int) -> list[int]:
        response = cast(
            "ReadHoldingRegistersResponse",
            await self._modbus.read_holding_registers(address, count=count),
        )
        assert not response.isError()
        return response.registers

    async def read_many_u16(self, address: int, count: int) -> list[int]:
        registers: list[int] = []
        async with self._lock:
            address_end = address + count
            for batch_start in range(address, address_end, _MAX_REGISTERS_PER_READ):
                batch_end = min(batch_start + _MAX_REGISTERS_PER_READ, address_end)
                registers.extend(
                    await self._read_batch(batch_start, count=batch_end - batch_start)
                )
        return registers


_MAX_REGISTERS_PER_READ = 125


def consume_u16(registers: Iterator[int]) -> int:
    try:
        return next(registers)
    except StopIteration:
        raise ValueError("missing register to consume u16") from None


def consume_i16(registers: Iterator[int]) -> int:
    raw = consume_u16(registers)
    return ctypes.c_int16(raw).value


def consume_u8_couple_from_u16(register: int) -> tuple[int, int]:
    return (register & 0xFF00) >> 8, register & 0x00FF


def consume_u8_couple(registers: Iterator[int]) -> tuple[int, int]:
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
