import dataclasses
from typing import Iterator

from .client import Client, consume_u16

__all__ = [
    "Functions",
    "FunctionsState",
]


@dataclasses.dataclass()
class FunctionsState:
    ocv_enabled: bool

    @classmethod
    def consume_from_registers(cls, registers: Iterator[int]):
        _aqc_setpoint1 = consume_u16(registers)
        _aqc_mode1 = consume_u16(registers)
        _aqc_setpoint2 = consume_u16(registers)
        _aqc_mode2 = consume_u16(registers)
        ocv_enabled = consume_u16(registers)

        return cls(
            ocv_enabled=ocv_enabled,
        )


class Functions:
    REG_AQC_SETPOINT1 = 500
    REG_OCV_STATE = 504

    _client: Client

    def __init__(self, client: Client) -> None:
        self._client = client

    async def read_all(self) -> FunctionsState:
        regs = await self._client.read_many_u16(
            self.REG_AQC_SETPOINT1,
            (self.REG_OCV_STATE - self.REG_AQC_SETPOINT1) + 1,
        )
        return FunctionsState.consume_from_registers(iter(regs))

    async def set_ocv_enabled(self, enabled: bool) -> None:
        await self._client.write_u16(self.REG_OCV_STATE, int(enabled))
