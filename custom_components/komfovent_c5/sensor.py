from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_TEMPERATURE,
    PRESSURE_PA,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import StateType

from . import KomfoventCoordinator, KomfoventEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> bool:
    c: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    diagram_sensors = (
        cls(c)
        for cls in (
            ExtractAirflowSetpoint,
            ExtractAirflowActual,
            ExtractAirflowFanLevel,
            ExhaustTemperature,
            ExtractTemperatureSetpoint,
            ExtractTemperatureActual,
            SupplyTemperatureSetpoint,
            SupplyTemperatureActual,
            OutdoorTemperature,
            HeatExchangerLevel,
            HeatExchangerEfficiency,
            InternalSupplyTemperature,
            SupplyAirflowSetpoint,
            SupplyAirflowActual,
            SupplyAirflowFanLevel,
            ReturnWaterTemperature,
            ElectricalHeaterLevel,
            WaterHeaterLevel,
            DxLevel,
            HeatpumpLevel,
            WaterCoolerLevel,
        )
    )
    async_add_entities(
        [
            VavSensorsRange(c),
            NominalSupplyPressure(c),
            NominalExhaustPressure(c),
            ActiveModeSupplyFlow(c),
            ActiveModeExtractFlow(c),
            ActiveModeTemperatureSetpoint(c),
            *diagram_sensors,
        ]
    )
    return True


class VavSensorsRange(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} VAV Sensors Range"

    @property
    def device_class(self) -> str:
        return DEVICE_CLASS_PRESSURE

    @property
    def native_value(self) -> StateType:
        return self._modes_state.vav_sensors_range

    @property
    def native_unit_of_measurement(self) -> str:
        return PRESSURE_PA

    @property
    def state_class(self) -> str:
        return STATE_CLASS_MEASUREMENT


class NominalSupplyPressure(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Nominal Supply Pressure"

    @property
    def device_class(self) -> str:
        return DEVICE_CLASS_PRESSURE

    @property
    def native_value(self) -> StateType:
        return self._modes_state.nominal_supply_pressure

    @property
    def native_unit_of_measurement(self) -> str:
        return PRESSURE_PA

    @property
    def state_class(self) -> str:
        return STATE_CLASS_MEASUREMENT


class NominalExhaustPressure(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Nominal Exhaust Pressure"

    @property
    def device_class(self) -> str:
        return DEVICE_CLASS_PRESSURE

    @property
    def native_value(self) -> StateType:
        return self._modes_state.nominal_exhaust_pressure

    @property
    def native_unit_of_measurement(self) -> str:
        return PRESSURE_PA

    @property
    def state_class(self) -> str:
        return STATE_CLASS_MEASUREMENT


class FlowSensor(KomfoventEntity, SensorEntity):
    @property
    def icon(self) -> str:
        return "mdi:air-filter"

    @property
    def native_unit_of_measurement(self) -> str:
        return self.coordinator.settings_state.flow_units.unit_symbol()

    @property
    def state_class(self) -> str:
        return STATE_CLASS_MEASUREMENT


class ActiveModeSupplyFlow(FlowSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Active Mode Supply Flow"

    @property
    def native_value(self) -> StateType:
        return self._modes_state.active_mode.supply_flow


class ActiveModeExtractFlow(FlowSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Active Mode Extract Flow"

    @property
    def native_value(self) -> StateType:
        return self._modes_state.active_mode.extract_flow


class TemperatureSensor(KomfoventEntity, SensorEntity):
    @property
    def device_class(self) -> str:
        return DEVICE_CLASS_TEMPERATURE

    @property
    def native_unit_of_measurement(self) -> str:
        return TEMP_CELSIUS

    @property
    def state_class(self) -> str:
        return STATE_CLASS_MEASUREMENT


class ActiveModeTemperatureSetpoint(TemperatureSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Active Mode Temperature Setpoint"

    @property
    def native_value(self) -> StateType:
        return self._modes_state.active_mode.setpoint_temperature


# The following sensors are all modeled after the diagram shown on page 3 of the MODBUS_C5_manual_EN.pdf manual.

# Extract airflow
class ExtractAirflowSetpoint(FlowSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Extract airflow Setpoint"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.extract_flow_setpoint


class ExtractAirflowActual(FlowSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Extract airflow Actual"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.exhaust_flow


class ExtractAirflowFanLevel(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Extract airflow Fan level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.exhaust_fan_level


# Exhaust temperature
class ExhaustTemperature(TemperatureSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Exhaust temperature"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.exhaust_temp


# Extract temperature
class ExtractTemperatureSetpoint(TemperatureSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Extract temperature Setpoint"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.temp_setpoint


class ExtractTemperatureActual(TemperatureSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Extract temperature Actual"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.extract_temp


# Supply temperature


class SupplyTemperatureSetpoint(TemperatureSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Supply temperature Setpoint"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.supply_air_temp_setpoint


class SupplyTemperatureActual(TemperatureSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Supply temperature Actual"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.supply_temp


# Outdoot temperature
class OutdoorTemperature(TemperatureSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Outdoor temperature"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.outdoor_temp


# Heat exchanger
class HeatExchangerLevel(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Heat exchanger Level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.heat_exchanger_level


# TODO this should have a percentage unit and stuff
class HeatExchangerEfficiency(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Heat exchanger Efficiency"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.heat_exchanger_thermal_efficiency


# Internal supply temperature
class InternalSupplyTemperature(TemperatureSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Internal supply temperature"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.internal_supply_temp


# Supply airflow
class SupplyAirflowSetpoint(FlowSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Supply airflow Setpoint"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.supply_flow_setpoint


class SupplyAirflowActual(FlowSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Supply airflow Actual"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.supply_flow


class SupplyAirflowFanLevel(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Supply airflow Fan level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.supply_fan_level


# Return water temperature
class ReturnWaterTemperature(TemperatureSensor):
    @property
    def name(self) -> str:
        return f"{super().name} Return water temperature"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.return_water_temp


# Air heaters/coolers
class ElectricalHeaterLevel(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Electrical heater Level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.electric_heater_level


class WaterHeaterLevel(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Water heater Level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.water_heater_level


class DxLevel(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} DX level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.dx_level


class HeatpumpLevel(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Heat-pump level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.heat_pump_level


class WaterCoolerLevel(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Water cooler Level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.water_cooler_level
