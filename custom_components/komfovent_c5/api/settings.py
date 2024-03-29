import dataclasses
import enum
from collections.abc import Iterator
from datetime import datetime
from ipaddress import IPv4Address

from .client import (
    Client,
    consume_date,
    consume_ip_address,
    consume_string,
    consume_time,
    consume_u16,
    consume_u32,
)

__all__ = [
    "FlowUnits",
    "Settings",
    "SettingsState",
]


class FlowUnits(enum.IntEnum):
    CUBIC_METER_PER_HOUR = 0
    LITER_PER_SECOND = 1
    CUBIC_METER_PER_SECOND = 2
    PASCAL = 3

    @classmethod
    def consume_from_registers(cls, registers: Iterator[int]):
        return cls(consume_u16(registers))

    def unit_symbol(self) -> str:
        return _FLOW_UNIT_TO_SYMBOL[self]

    def common_factor(self) -> float:
        if self == self.CUBIC_METER_PER_SECOND:
            return 1e-3

        return 1.0


@dataclasses.dataclass(slots=True, kw_only=True)
class Rs485:
    class Speed(enum.IntEnum):
        S9600 = 0
        S19200 = 1
        S38400 = 2
        S57600 = 3

    class Parity(enum.IntEnum):
        NONE = 0
        EVEN = 1

    speed: Speed
    parity: Parity
    stop_bits: int

    @classmethod
    def consume_from_registers(cls, registers: Iterator[int]):
        raw = consume_u16(registers)
        raw_stop_bits = raw & 0b0_0001
        raw_parity = (raw & 0b0_0010) >> 1
        raw_speed = (raw & 0b1_1000) >> 3
        return cls(
            speed=cls.Speed(raw_speed),
            parity=cls.Parity(raw_parity),
            stop_bits=raw_stop_bits + 1,
        )


class Language(enum.IntEnum):
    ENGLISH = 0
    LITHUANIAN = 1
    RUSSIAN = 2
    POLISH = 3
    # not mentioned in manual, but definitely there!
    GERMAN = 4

    @classmethod
    def consume_from_registers(cls, registers: Iterator[int]):
        return cls(consume_u16(registers))


@dataclasses.dataclass(slots=True, kw_only=True)
class SettingsState:
    datetime: datetime
    language: Language
    modbus_address: int
    ip_address: IPv4Address
    flow_units: FlowUnits
    ahu_serial_number: str
    ahu_name: str

    # extended set
    ip_mask: IPv4Address | None
    rs_485: Rs485 | None
    daylight_saving_time: bool | None
    bacnet_port: int | None
    bacnet_id: int | None

    @classmethod
    def consume_from_registers(cls, registers: Iterator[int], *, is_extended: bool):
        time = consume_time(registers, read_seconds=True)
        # reg 451 is the day of week, which we don't need
        _ = consume_u16(registers)
        date = consume_date(registers)
        language = Language.consume_from_registers(registers)
        modbus_address = consume_u16(registers)
        ip_address = consume_ip_address(registers)
        flow_units = FlowUnits.consume_from_registers(registers)
        ahu_serial_number = consume_string(registers, 8)
        ahu_name = consume_string(registers, 12)

        if is_extended:
            ip_mask = consume_ip_address(registers)
            rs_485 = Rs485.consume_from_registers(registers)
            daylight_saving_time = bool(consume_u16(registers))
            # reg 483 isn't documented, skip
            _ = consume_u16(registers)
            bacnet_port = consume_u16(registers)
            bacnet_id = consume_u32(registers)
        else:
            ip_mask = None
            rs_485 = None
            daylight_saving_time = None
            bacnet_port = None
            bacnet_id = None

        return cls(
            datetime=datetime.combine(date, time),
            language=language,
            modbus_address=modbus_address,
            ip_address=ip_address,
            flow_units=flow_units,
            ahu_serial_number=ahu_serial_number,
            ahu_name=ahu_name,
            ip_mask=ip_mask,
            rs_485=rs_485,
            daylight_saving_time=daylight_saving_time,
            bacnet_port=bacnet_port,
            bacnet_id=bacnet_id,
        )


class Settings:
    REG_TIME = 449
    REG_SECONDS = 450
    REG_DAY_OF_WEEK = 451
    REG_DATE = 452
    REG_YEAR = 453
    REG_LANGUAGE = 454
    REG_MODBUS_ADDRESS = 455
    REG_IP_ADDRESS = 456
    REG_FLOW_UNITS = 458
    REG_AHU_SN = 459
    REG_AHU_NAME = 467

    # extended set
    REG_IP_MASK = 479
    REG_RS485 = 481
    REG_DST = 482
    REG_BACNET_PORT = 484
    REG_BACNET_ID = 485

    _client: Client

    def __init__(self, client: Client) -> None:
        self._client = client

    async def read_all(self, *, is_extended: bool) -> SettingsState:
        end = (self.REG_BACNET_ID + 1) if is_extended else (self.REG_IP_MASK - 1)
        registers = await self._client.read_many_u16(
            self.REG_TIME,
            (end - self.REG_TIME) + 1,
        )
        return SettingsState.consume_from_registers(
            iter(registers), is_extended=is_extended
        )


_FLOW_UNIT_TO_SYMBOL = {
    FlowUnits.CUBIC_METER_PER_HOUR: "m³/h",
    FlowUnits.LITER_PER_SECOND: "L/s",
    FlowUnits.CUBIC_METER_PER_SECOND: "m³/s",
    FlowUnits.PASCAL: "Pa",
}
