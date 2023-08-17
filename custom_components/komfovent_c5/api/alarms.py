import dataclasses
from collections.abc import Iterator
from datetime import datetime

from .alarms_db import code_str_from_code, message_for_code
from .client import Client, consume_u8_couple, consume_u16

__all__ = [
    "Alarm",
    "AlarmHistoryEntry",
    "Alarms",
]


@dataclasses.dataclass()
class Alarm:
    code: int
    message: str

    @property
    def code_str(self) -> str:
        return code_str_from_code(self.code)

    @classmethod
    def lookup(cls, code: int):
        return cls(
            code=code,
            message=message_for_code(code),
        )

    @classmethod
    def consume_list_from_registers(cls, count: int, registers: Iterator[int]):
        alarms = []
        for _ in range(count):
            code = consume_u16(registers)
            alarm = cls.lookup(code)
            alarms.append(alarm)

        return alarms


@dataclasses.dataclass()
class AlarmHistoryEntry:
    NUM_REGISTERS = 5

    alarm: Alarm
    timestamp: datetime

    @classmethod
    def consume_from_registers(cls, registers: Iterator[int]):
        year = consume_u16(registers)
        month, day = consume_u8_couple(registers)
        hour, minute = consume_u8_couple(registers)
        second = consume_u16(registers)
        code = consume_u16(registers)

        return cls(
            alarm=Alarm.lookup(code),
            timestamp=datetime(year, month, day, hour, minute, second),
        )

    @classmethod
    def consume_list_from_registers(cls, count: int, registers: Iterator[int]):
        alarms = []
        for _ in range(count):
            alarm = cls.consume_from_registers(registers)
            alarms.append(alarm)

        return alarms


class Alarms:
    MAX_ACTIVE_ALERTS = 10
    MAX_HISTORY_ALERTS = 50

    REG_ACTIVE_ALARMS_COUNT = 999
    REG_ACTIVE_ALARM1_CODE = 1000
    REG_HISTORY_COUNT = 1099
    REG_ALARM1_YEAR = 1100

    _client: Client

    def __init__(self, client: Client) -> None:
        self._client = client

    async def read_active(self) -> list[Alarm]:
        count = await self._client.read_u16(self.REG_ACTIVE_ALARMS_COUNT)
        assert 0 <= count <= 10
        if count > 0:
            registers = await self._client.read_many_u16(
                self.REG_ACTIVE_ALARM1_CODE, count
            )
        else:
            registers = []
        return Alarm.consume_list_from_registers(count, iter(registers))

    async def reset_active(self) -> None:
        await self._client.write_u16(self.REG_ACTIVE_ALARMS_COUNT, 0x99C5)

    async def read_history(self) -> list[AlarmHistoryEntry]:
        count = await self._client.read_u16(self.REG_HISTORY_COUNT)
        assert 0 <= count <= 50
        if count > 0:
            register_count = count * AlarmHistoryEntry.NUM_REGISTERS
            registers = await self._client.read_many_u16(
                self.REG_ALARM1_YEAR, register_count
            )
        else:
            registers = []
        return AlarmHistoryEntry.consume_list_from_registers(count, iter(registers))
