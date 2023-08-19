import dataclasses
import enum
import itertools
from collections.abc import Iterator

from .client import Client, consume_i16, consume_u16, consume_u32
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
    def consume_from_registers(cls, registers: Iterator[int]):
        return cls(consume_u16(registers))


class AirQualitySensorType(enum.IntEnum):
    CO2 = 0
    VOC_Q = 1
    VOC_P = 2
    RH = 3
    TMP = 4

    @classmethod
    def consume_from_registers(cls, registers: Iterator[int]):
        return cls(consume_u16(registers))


class CountersEfficienciesConfiguration(enum.IntFlag):
    EXHAUST_FAN_UNIT = 1 << 8
    SUPPLY_FAN_UNIT = 1 << 7
    EXHAUST_FAN_COUNTER = 1 << 6
    HEATER_COUNTER = 1 << 5
    EXTRACT_FILTER = 1 << 4
    OUTDOOR_FILTER = 1 << 3
    EXHAUST_SFP = 1 << 2
    SUPPLY_SFP = 1 << 1
    HX_EFFICIENCY = 1 << 0

    @classmethod
    def consume_from_registers(cls, registers: Iterator[int]):
        return cls(consume_u16(registers))


class ActiveFunctions(enum.IntFlag):
    OOD = 1 << 5
    AQC = 1 << 4
    SNC = 1 << 3
    MTC = 1 << 2
    OVR = 1 << 1
    OCV = 1 << 0

    @classmethod
    def consume_from_registers(cls, registers: Iterator[int]):
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
    air_quality_sensor_type: AirQualitySensorType
    # TODO use ABC class for this combined with above type
    air_quality_level: int
    supply_air_humidity: float
    water_heater_level: float
    water_cooler_level: float
    humidity_control_level: float
    heat_exchanger_level: float
    recirculation_level: float
    supply_fan_level: float
    exhaust_fan_level: float
    outdoor_air_damper_actuator_level: float
    exhaust_air_damper_actuator_level: float
    electric_heater_level: float
    heat_pump_level: float
    dx_level: float
    ovr_input: bool
    fire_system_input: bool
    external_stop_input: bool
    control_input: bool
    temp_setpoint: float
    supply_air_temp_setpoint: float
    water_heater_pump: bool
    water_cooler_pump: bool
    supply_flow_setpoint: float
    extract_flow_setpoint: float
    internal_supply_temp: float | None
    efficiencies_configuration: CountersEfficienciesConfiguration
    heat_exchanger_thermal_efficiency: int | None
    energy_saving: int | None
    heat_exchanger_recovery: int | None
    supply_sfp: float
    exhaust_sfp: float
    outdoor_air_filter_impurity_level: int
    exhaust_air_filter_impurity_level: int
    air_heater_operation_hours: int
    supply_fan_operation_hours_or_kwh: int
    exhaust_fan_operation_hours_or_kwh: int
    supply_fan_power: int
    exhaust_fan_power: int
    active_functions: ActiveFunctions
    air_cooler_operation_hours: int
    heat_exchanger_operation_kwh: int
    air_heater_operation_kwh: int

    @classmethod
    def consume_from_registers(cls, registers: Iterator[int], *, units: FlowUnits):
        # reg: 2000
        c5_status = C5Status.consume_from_registers(registers)
        mode = OperationMode.consume_from_registers(registers)
        # reg: 2002
        supply_flow = consume_u32(registers) * units.common_factor()
        exhaust_flow = consume_u32(registers) * units.common_factor()
        # reg: 2006
        supply_temp = consume_i16(registers) / 10.0
        extract_temp = consume_i16(registers) / 10.0
        outdoor_temp = consume_i16(registers) / 10.0
        exhaust_temp = consume_i16(registers) / 10.0
        # reg: 2010
        return_water_temp = consume_i16(registers) / 10.0
        supply_air_pressure = consume_u16(registers)
        extract_air_pressure = consume_u16(registers)
        air_quality_sensor_type = AirQualitySensorType.consume_from_registers(registers)
        air_quality_level = consume_u16(registers)
        supply_air_humidity = consume_u16(registers) / 10.0
        water_heater_level = consume_u16(registers) / 10.0
        water_cooler_level = consume_u16(registers) / 10.0
        humidity_control_level = consume_u16(registers) / 10.0
        heat_exchanger_level = consume_u16(registers) / 10.0
        # reg: 2020
        recirculation_level = consume_u16(registers) / 10.0
        supply_fan_level = consume_u16(registers) / 10.0
        exhaust_fan_level = consume_u16(registers) / 10.0
        outdoor_air_damper_actuator_level = consume_u16(registers) / 10.0
        exhaust_air_damper_actuator_level = consume_u16(registers) / 10.0
        electric_heater_level = consume_u16(registers) / 10.0
        heat_pump_level = consume_i16(registers) / 10.0
        dx_level = consume_i16(registers) / 10.0
        ovr_input = bool(consume_u16(registers))
        fire_system_input = bool(consume_u16(registers))
        # reg: 2030
        external_stop_input = bool(consume_u16(registers))
        control_input = bool(consume_u16(registers))
        temp_setpoint = consume_u16(registers) / 10.0
        supply_air_temp_setpoint = consume_u16(registers) / 10.0
        water_heater_pump = bool(consume_u16(registers))
        water_cooler_pump = bool(consume_u16(registers))
        # reg: 2036
        supply_flow_setpoint = consume_u32(registers) * units.common_factor()
        extract_flow_setpoint = consume_u32(registers) * units.common_factor()
        # reg: 2040
        raw = consume_i16(registers)
        # use 'None' if register is 0xFFFF
        internal_supply_temp = None if raw == -0x8000 else raw / 10.0

        # reg: 2200
        efficiencies_configuration = (
            CountersEfficienciesConfiguration.consume_from_registers(registers)
        )
        heat_exchanger_thermal_efficiency: int | None = consume_u16(registers)
        if heat_exchanger_thermal_efficiency == 0xFF:
            heat_exchanger_thermal_efficiency = None
        energy_saving: int | None = consume_u16(registers)
        if energy_saving == 0xFF:
            energy_saving = None
        # reg: 2203
        heat_exchanger_recovery: int | None = consume_u32(registers)
        if heat_exchanger_recovery == 0xFFFF_FFFF:
            heat_exchanger_recovery = None
        # reg: 2205
        supply_sfp = consume_i16(registers) / 100.0
        exhaust_sfp = consume_i16(registers) / 100.0
        outdoor_air_filter_impurity_level = consume_u16(registers)
        exhaust_air_filter_impurity_level = consume_u16(registers)
        # reg: 2209
        air_heater_operation_hours = consume_u32(registers)
        supply_fan_operation_hours_or_kwh = consume_u32(registers)
        exhaust_fan_operation_hours_or_kwh = consume_u32(registers)
        # reg: 2215
        supply_fan_power = consume_u16(registers)
        exhaust_fan_power = consume_u16(registers)
        active_functions = ActiveFunctions.consume_from_registers(registers)
        # reg: 2218
        air_cooler_operation_hours = consume_u32(registers)
        heat_exchanger_operation_kwh = consume_u32(registers)
        air_heater_operation_kwh = consume_u32(registers)

        return cls(
            c5_status=c5_status,
            mode=mode,
            supply_flow=supply_flow,
            exhaust_flow=exhaust_flow,
            supply_temp=supply_temp,
            extract_temp=extract_temp,
            outdoor_temp=outdoor_temp,
            exhaust_temp=exhaust_temp,
            return_water_temp=return_water_temp,
            supply_air_pressure=supply_air_pressure,
            extract_air_pressure=extract_air_pressure,
            air_quality_sensor_type=air_quality_sensor_type,
            air_quality_level=air_quality_level,
            supply_air_humidity=supply_air_humidity,
            water_heater_level=water_heater_level,
            water_cooler_level=water_cooler_level,
            humidity_control_level=humidity_control_level,
            heat_exchanger_level=heat_exchanger_level,
            recirculation_level=recirculation_level,
            supply_fan_level=supply_fan_level,
            exhaust_fan_level=exhaust_fan_level,
            outdoor_air_damper_actuator_level=outdoor_air_damper_actuator_level,
            exhaust_air_damper_actuator_level=exhaust_air_damper_actuator_level,
            electric_heater_level=electric_heater_level,
            heat_pump_level=heat_pump_level,
            dx_level=dx_level,
            ovr_input=ovr_input,
            fire_system_input=fire_system_input,
            external_stop_input=external_stop_input,
            control_input=control_input,
            temp_setpoint=temp_setpoint,
            supply_air_temp_setpoint=supply_air_temp_setpoint,
            water_heater_pump=water_heater_pump,
            water_cooler_pump=water_cooler_pump,
            supply_flow_setpoint=supply_flow_setpoint,
            extract_flow_setpoint=extract_flow_setpoint,
            internal_supply_temp=internal_supply_temp,
            efficiencies_configuration=efficiencies_configuration,
            heat_exchanger_thermal_efficiency=heat_exchanger_thermal_efficiency,
            energy_saving=energy_saving,
            heat_exchanger_recovery=heat_exchanger_recovery,
            supply_sfp=supply_sfp,
            exhaust_sfp=exhaust_sfp,
            outdoor_air_filter_impurity_level=outdoor_air_filter_impurity_level,
            exhaust_air_filter_impurity_level=exhaust_air_filter_impurity_level,
            air_heater_operation_hours=air_heater_operation_hours,
            supply_fan_operation_hours_or_kwh=supply_fan_operation_hours_or_kwh,
            exhaust_fan_operation_hours_or_kwh=exhaust_fan_operation_hours_or_kwh,
            supply_fan_power=supply_fan_power,
            exhaust_fan_power=exhaust_fan_power,
            active_functions=active_functions,
            air_cooler_operation_hours=air_cooler_operation_hours,
            heat_exchanger_operation_kwh=heat_exchanger_operation_kwh,
            air_heater_operation_kwh=air_heater_operation_kwh,
        )


class Monitoring:
    REG_C5_STATUS = 1999
    REG_INTERNAL_SUPPLY_TEMP = 2039
    # some empty registers in between
    REG_COUNTERS_EFFICIENCIES_CONFIG = 2199
    REG_AIR_HEATER_OPERATION_ENERGY = 2221

    _client: Client

    def __init__(self, client: Client) -> None:
        self._client = client

    async def read_all(self, *, units: FlowUnits) -> MonitoringState:
        regs1 = await self._client.read_many_u16(
            self.REG_C5_STATUS,
            (self.REG_INTERNAL_SUPPLY_TEMP - self.REG_C5_STATUS) + 1,
        )
        regs2 = await self._client.read_many_u16(
            self.REG_COUNTERS_EFFICIENCIES_CONFIG,
            (
                (self.REG_AIR_HEATER_OPERATION_ENERGY + 1)
                - self.REG_COUNTERS_EFFICIENCIES_CONFIG
            )
            + 1,
        )
        return MonitoringState.consume_from_registers(
            itertools.chain(regs1, regs2), units=units
        )
