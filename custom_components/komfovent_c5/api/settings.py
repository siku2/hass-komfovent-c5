import dataclasses
import enum
from ipaddress import IPv4Address
from typing import Iterator

from .client import (
    Client,
    consume_ip_address_from_registers,
    consume_string_from_registers,
    consume_u16_from_registers,
    consume_u32_from_registers,
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
    def _consume_from_registers(cls, registers: Iterator[int]):
        return FlowUnits(consume_u16_from_registers(registers))

    def unit_symbol(self) -> str:
        return _FLOW_UNIT_TO_SYMBOL[self]


@dataclasses.dataclass()
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
    def _consume_from_registers(cls, registers: Iterator[int]):
        raw = consume_u16_from_registers(registers)
        raw_stop_bits = raw & 0b0_0001
        raw_parity = (raw & 0b0_0010) >> 1
        raw_speed = (raw & 0b1_1000) >> 3
        return cls(
            speed=cls.Speed(raw_speed),
            parity=cls.Parity(raw_parity),
            stop_bits=raw_stop_bits + 1,
        )


@dataclasses.dataclass()
class SettingsState:
    ip_address: IPv4Address
    flow_units: FlowUnits
    ahu_serial_number: str
    ahu_name: str
    ip_mask: IPv4Address
    rs_485: Rs485
    daylight_saving_time: bool
    bacnet_port: int
    bacnet_id: int

    @classmethod
    def _consume_from_registers(cls, registers: Iterator[int]):
        ip_address = consume_ip_address_from_registers(registers)
        flow_units = FlowUnits._consume_from_registers(registers)
        ahu_serial_number = consume_string_from_registers(registers, 8)
        ahu_name = consume_string_from_registers(registers, 12)
        ip_mask = consume_ip_address_from_registers(registers)
        rs_485 = Rs485._consume_from_registers(registers)
        daylight_saving_time = bool(consume_u16_from_registers(registers))
        # reg 483 isn't documented, skip
        _ = consume_u16_from_registers(registers)
        bacnet_port = consume_u16_from_registers(registers)
        bacnet_id = consume_u32_from_registers(registers)

        return cls(
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
    # TODO missing the first half!
    REG_IP_ADDRESS = 456
    REG_FLOW_UNITS = 458
    REG_AHU_SN = 459
    REG_AHU_NAME = 467
    REG_IP_MASK = 479
    REG_RS485 = 481
    REG_DST = 482
    REG_BACNET_PORT = 484
    REG_BACNET_ID = 485

    _client: Client

    def __init__(self, client: Client) -> None:
        self._client = client

    async def read_all(self) -> SettingsState:
        registers = await self._client.read_many_u16(
            self.REG_IP_ADDRESS,
            ((self.REG_BACNET_ID + 1) - self.REG_IP_ADDRESS) + 1,
        )
        return SettingsState._consume_from_registers(iter(registers))


_FLOW_UNIT_TO_SYMBOL = {
    FlowUnits.CUBIC_METER_PER_HOUR: "m³/h",
    FlowUnits.LITER_PER_SECOND: "L/s",
    FlowUnits.CUBIC_METER_PER_SECOND: "m³/s",
    FlowUnits.PASCAL: "Pa",
}
