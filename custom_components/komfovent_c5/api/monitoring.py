import dataclasses
import enum
from typing import Iterator

from .client import (
    Client,
    consume_i16,
    consume_u16,
    consume_u32,
)
from .modes import OperationMode
from .settings import FlowUnits

__all__ = [
    "C5Status",
    "Monitoring",
    "MonitoringState",
]


class C5Status(enum.IntEnum):
    STOP = 0
    ENABLED_NO_FANS = 1
    RUNNING = 2

    @classmethod
    def _consume(cls, registers: Iterator[int]):
        return cls(consume_u16(registers))


class AirQualitySensorType(enum.IntEnum):
    CO2 = 0
    VOCq = 1
    VOCp = 2
    RH = 3
    TMP = 4

    @classmethod
    def _consume(cls, registers: Iterator[int]):
        return cls(consume_u16(registers))


@dataclasses.dataclass()
class MonitoringState:
    c5_status: C5Status
    mode: OperationMode
    supply_flow: float
    exhaust_flow: float
    supply_temp: float
    extract_temp: float
    outdoor_temp: float
    exhaust_temp: float
    return_water_temp: float
    supply_air_pressure: int
    extract_air_pressure: int

    @classmethod
    def _consume(cls, registers: Iterator[int], units: FlowUnits):
        return cls(
            c5_status=C5Status._consume(registers),
            mode=OperationMode._consume(registers),
            supply_flow=consume_u32(registers) * units._common_factor(),
            exhaust_flow=consume_u32(registers) * units._common_factor(),
            supply_temp=consume_i16(registers) / 10.0,
            extract_temp=consume_i16(registers) / 10.0,
            outdoor_temp=consume_i16(registers) / 10.0,
            exhaust_temp=consume_i16(registers) / 10.0,
            return_water_temp=consume_i16(registers) / 10.0,
            supply_air_pressure=consume_u16(registers),
            extract_air_pressure=consume_u16(registers),
        )


class Monitoring:
    REG_C5_STATUS = 1999
    REG_AIR_HEATER_OPERATION_ENERGY = 2221

    _client: Client

    def __init__(self, client: Client) -> None:
        self._client = client

    async def read_all(self) -> MonitoringState:
        registers = await self._client.read_many_u16(
            self.REG_C5_STATUS,
            ((self.REG_AIR_HEATER_OPERATION_ENERGY + 1) - self.REG_C5_STATUS) + 1,
        )
        return MonitoringState._consume(iter(registers))
