import asyncio
import dataclasses
import enum
from typing import Dict, Iterator, Optional

from .client import Client, consume_u16_from_registers, consume_u32_from_registers

__all__ = [
    "ConfigurationFlags",
    "FlowControlMode",
    "Mode",
    "Modes",
    "ModesState",
    "ModeState",
    "OperationMode",
    "SpecialMode",
    "TemperatureControlMode",
    "VavStatus",
]


class OperationMode(enum.IntEnum):
    COMFORT1 = 1
    COMFORT2 = 2
    ECONOMY1 = 3
    ECONOMY2 = 4
    SPECIAL = 5
    PROGRAM = 6


class FlowControlMode(enum.IntEnum):
    CAV = 0
    VAV = 1
    DCV = 2


class TemperatureControlMode(enum.IntEnum):
    SUPPLY = 0
    EXTRACT = 1
    ROOM = 2


class VavStatus(enum.IntEnum):
    NOT_CALIBRATED = 0
    CALIBRATING = 1
    SUPPLY = 2
    EXTRACT = 3
    DOUBLE = 4


class ConfigurationFlags(enum.IntFlag):
    DEHUMIDIFYING = 1 << 4
    HUMIDIFYING = 1 << 3
    RECIRCULATION = 1 << 2
    COOLING = 1 << 1
    HEATING = 1 << 0


@dataclasses.dataclass()
class ModeState:
    supply_flow: int
    extract_flow: int
    setpoint_temperature: float
    configuration: Optional[ConfigurationFlags]

    @classmethod
    def _consume_from_registers(cls, registers: Iterator[int], special: bool):
        supply_flow = consume_u32_from_registers(registers)
        extract_flow = consume_u32_from_registers(registers)
        setpoint_temperature = consume_u16_from_registers(registers) / 10.0
        if special:
            configuration = ConfigurationFlags(consume_u16_from_registers(registers))
        else:
            configuration = None

        return cls(
            supply_flow=supply_flow,
            extract_flow=extract_flow,
            setpoint_temperature=setpoint_temperature,
            configuration=configuration,
        )


class Mode:
    REG_OFF_SUPPLY_FLOW = 0
    REG_OFF_EXTRACT_FLOW = 2
    REG_OFF_SETPOINT_TEMPERATURE = 4

    _client: Client
    _reg_start: int

    def __init__(self, client: Client, reg_start: int) -> None:
        self._client = client
        self._reg_start = reg_start

    async def read_all(self) -> ModeState:
        registers = await self._client.read_many_u16(
            self._reg_start + self.REG_OFF_SUPPLY_FLOW, 5
        )
        return ModeState._consume_from_registers(iter(registers), False)

    async def supply_flow(self) -> int:
        reg = self._reg_start + self.REG_OFF_SUPPLY_FLOW
        return await self._client.read_u32(reg)

    async def set_supply_flow(self, value: int) -> None:
        reg = self._reg_start + self.REG_OFF_SUPPLY_FLOW
        await self._client.write_u32(reg, value)

    async def extract_flow(self) -> int:
        reg = self._reg_start + self.REG_OFF_EXTRACT_FLOW
        return await self._client.read_u32(reg)

    async def set_extract_flow(self, value: int) -> None:
        reg = self._reg_start + self.REG_OFF_EXTRACT_FLOW
        await self._client.write_u32(reg, value)

    async def setpoint_temperature(self) -> float:
        reg = self._reg_start + self.REG_OFF_SETPOINT_TEMPERATURE
        value = await self._client.read_u16(reg)
        return value / 10.0

    async def set_setpoint_temperature(self, value: float) -> None:
        reg = self._reg_start + self.REG_OFF_SETPOINT_TEMPERATURE
        await self._client.write_u16(reg, round(value * 10.0))


class SpecialMode(Mode):
    REG_OFF_CONFIGURATION = 5

    async def read_all(self) -> ModeState:
        registers = await self._client.read_many_u16(
            self._reg_start + self.REG_OFF_SUPPLY_FLOW, 6
        )
        return ModeState._consume_from_registers(iter(registers), True)

    async def configuration(self) -> ConfigurationFlags:
        return ConfigurationFlags(
            await self._client.read_u16(self._reg_start + self.REG_OFF_CONFIGURATION)
        )

    async def set_configuration(self, flags: ConfigurationFlags) -> None:
        await self._client.write_u16(
            self._reg_start + self.REG_OFF_CONFIGURATION, flags.value
        )


@dataclasses.dataclass()
class ModesState:
    ahu: bool
    operation_mode: OperationMode
    flow_control_mode: FlowControlMode
    temperature_control_mode: TemperatureControlMode
    vav_status: VavStatus
    vav_sensors_range: int
    nominal_supply_pressure: int
    nominal_exhaust_pressure: int

    modes: Dict[OperationMode, ModeState]

    @classmethod
    def _consume_from_registers(cls, ahu: bool, registers: Iterator[int]):
        operation_mode = OperationMode(consume_u16_from_registers(registers))
        modes = {
            OperationMode.COMFORT1: ModeState._consume_from_registers(registers, False),
            OperationMode.COMFORT2: ModeState._consume_from_registers(registers, False),
            OperationMode.ECONOMY1: ModeState._consume_from_registers(registers, False),
            OperationMode.ECONOMY2: ModeState._consume_from_registers(registers, False),
            OperationMode.SPECIAL: ModeState._consume_from_registers(registers, True),
        }

        return cls(
            ahu=ahu,
            operation_mode=operation_mode,
            modes=modes,
            flow_control_mode=FlowControlMode(consume_u16_from_registers(registers)),
            temperature_control_mode=TemperatureControlMode(
                consume_u16_from_registers(registers)
            ),
            vav_status=VavStatus(consume_u16_from_registers(registers)),
            vav_sensors_range=consume_u16_from_registers(registers),
            nominal_supply_pressure=consume_u16_from_registers(registers),
            nominal_exhaust_pressure=consume_u16_from_registers(registers),
        )

    @property
    def active_mode(self) -> ModeState:
        return self.modes[self.operation_mode]


class Modes:
    REG_AHU_ON = 0
    REG_OPERATION_MODE = 99
    REG_FLOW_CONTROL_MODE = 126
    REG_TEMPERATURE_CONTROL_MODE = 127
    REG_VAV_STATUS = 128
    REG_VAV_SENSORS_RANGE = 129
    REG_NOMINAL_SUPPLY_PRESSURE = 130
    REG_NOMINAL_EXHAUST_PRESSURE = 131

    _client: Client

    def __init__(self, client: Client) -> None:
        self._client = client

    async def read_all(self) -> ModesState:
        ahu, registers = await asyncio.gather(
            self.ahu_on(),
            self._client.read_many_u16(
                self.REG_OPERATION_MODE,
                (self.REG_NOMINAL_EXHAUST_PRESSURE - self.REG_OPERATION_MODE) + 1,
            ),
        )
        return ModesState._consume_from_registers(ahu, iter(registers))

    async def ahu_on(self) -> bool:
        return bool(await self._client.read_u16(self.REG_AHU_ON))

    async def set_ahu_on(self, on: bool) -> None:
        await self._client.write_u16(self.REG_AHU_ON, int(on))

    async def operation_mode(self) -> OperationMode:
        return OperationMode(await self._client.read_u16(self.REG_OPERATION_MODE))

    async def set_operation_mode(self, mode: OperationMode) -> None:
        await self._client.write_u16(self.REG_OPERATION_MODE, mode.value)

    def mode_registers(self, mode: OperationMode) -> Mode:
        reg_start = _OP_MODE_OFFSET[mode]
        if mode == OperationMode.SPECIAL:
            return SpecialMode(self._client, reg_start)
        return Mode(self._client, reg_start)

    async def flow_control_mode(self) -> FlowControlMode:
        return FlowControlMode(await self._client.read_u16(self.REG_FLOW_CONTROL_MODE))

    async def set_flow_control_mode(self, mode: FlowControlMode) -> None:
        await self._client.write_u16(self.REG_FLOW_CONTROL_MODE, mode.value)

    async def temperature_control_mode(self) -> TemperatureControlMode:
        return TemperatureControlMode(
            await self._client.read_u16(self.REG_TEMPERATURE_CONTROL_MODE)
        )

    async def set_temperature_control_mode(self, mode: TemperatureControlMode) -> None:
        await self._client.write_u16(self.REG_TEMPERATURE_CONTROL_MODE, mode.value)

    async def vav_status(self) -> VavStatus:
        return VavStatus(await self._client.read_u16(self.REG_VAV_STATUS))

    async def start_vav_calibration(self) -> None:
        await self._client.write_u16(self.REG_VAV_STATUS, 0x99C5)

    async def vav_sensors_range(self) -> int:
        return await self._client.read_u16(self.REG_VAV_SENSORS_RANGE)

    async def set_vav_sensors_range(self, value: int) -> None:
        await self._client.write_u16(self.REG_VAV_SENSORS_RANGE, value)

    async def nominal_supply_pressure(self) -> int:
        return await self._client.read_u16(self.REG_NOMINAL_SUPPLY_PRESSURE)

    async def set_nominal_supply_pressure(self, value: int) -> None:
        await self._client.write_u16(self.REG_NOMINAL_SUPPLY_PRESSURE, value)

    async def nominal_exhaust_pressure(self) -> int:
        return await self._client.read_u16(self.REG_VAV_SENSORS_RANGE)

    async def set_nominal_exhaust_pressure(self, value: int) -> None:
        await self._client.write_u16(self.REG_VAV_SENSORS_RANGE, value)


_OP_MODE_OFFSET = {
    OperationMode.COMFORT1: 100,
    OperationMode.COMFORT2: 105,
    OperationMode.ECONOMY1: 110,
    OperationMode.ECONOMY2: 115,
    OperationMode.SPECIAL: 120,
}
