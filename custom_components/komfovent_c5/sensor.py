from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import KomfoventCoordinator, KomfoventEntity, api
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    coord: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    alarm_sensors = (
        cls(coord)
        for cls in (
            AlarmActiveCountSensor,
            AlarmHistoryCountSensor,
        )
    )
    active_alarm_sensors = (
        AlarmActiveSensor(coord, i) for i in range(api.Alarms.MAX_ACTIVE_ALERTS)
    )
    diagram_sensors = (
        cls(coord)
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
            VavSensorsRange(coord),
            NominalSupplyPressure(coord),
            NominalExhaustPressure(coord),
            ActiveModeSupplyFlow(coord),
            ActiveModeExtractFlow(coord),
            ActiveModeTemperatureSetpoint(coord),
            *alarm_sensors,
            *active_alarm_sensors,
            *diagram_sensors,
        ]
    )
    return True


class AlarmActiveSensor(KomfoventEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "active_alarm"

    def __init__(self, coordinator: KomfoventCoordinator, number: int) -> None:
        super().__init__(coordinator)
        self._number = number

    @property
    def name(self) -> str | None:
        name_translation_key = self._name_translation_key
        if name_translation_key is None:
            return None
        name_template: str | None = self.platform.platform_translations.get(
            name_translation_key
        )
        if name_template is None:
            return None
        return name_template.format(position=self._number + 1)

    @property
    def unique_id(self) -> str:
        return f"{super().unique_id}-{self._number}"

    @property
    def _alarm(self) -> api.Alarm | None:
        active_alarms = self._active_alarms
        if self._number < len(active_alarms):
            return active_alarms[self._number]
        return None

    @property
    def native_value(self) -> StateType:
        if alarm := self._alarm:
            return alarm.message.lower()
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        code_numeric = None
        code_str = None
        if alarm := self._alarm:
            code_numeric = alarm.code
            code_str = alarm.code_str

        return {
            "code": code_str,
            "code_numeric": code_numeric,
        }


class AlarmActiveCountSensor(KomfoventEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0
    _attr_translation_key = "active_alarms"

    @property
    def native_value(self) -> StateType:
        return len(self._active_alarms)


class AlarmHistoryCountSensor(KomfoventEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0
    _attr_translation_key = "alarms_in_history"

    @property
    def native_value(self) -> StateType:
        return self.coordinator.data.alarm_history_count


class FlowMetaSensor(KomfoventEntity, SensorEntity):
    _attr_icon = "mdi:air-filter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_unit_of_measurement(self) -> str:
        return self.coordinator.settings_state.flow_units.unit_symbol()


class PercentageMetaSensor(KomfoventEntity, SensorEntity):
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT


class TemperatureMetaSensor(KomfoventEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS


class VavSensorsRange(KomfoventEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_native_unit_of_measurement = UnitOfPressure.PA
    _attr_translation_key = "vav_sensors_range"

    @property
    def native_value(self) -> StateType:
        return self._modes_state.vav_sensors_range


class NominalSupplyPressure(KomfoventEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_native_unit_of_measurement = UnitOfPressure.PA
    _attr_translation_key = "nominal_supply_pressure"

    @property
    def native_value(self) -> StateType:
        return self._modes_state.nominal_supply_pressure


class NominalExhaustPressure(KomfoventEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_native_unit_of_measurement = UnitOfPressure.PA
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "nominal_exhaust_pressure"

    @property
    def native_value(self) -> StateType:
        return self._modes_state.nominal_exhaust_pressure


class ActiveModeSupplyFlow(FlowMetaSensor):
    _attr_translation_key = "active_mode_supply_flow"

    @property
    def native_value(self) -> StateType:
        if active_mode := self._modes_state.active_mode:
            return active_mode.supply_flow
        return None


class ActiveModeExtractFlow(FlowMetaSensor):
    _attr_translation_key = "active_mode_extract_flow"

    @property
    def native_value(self) -> StateType:
        if active_mode := self._modes_state.active_mode:
            return active_mode.extract_flow
        return None


class ActiveModeTemperatureSetpoint(TemperatureMetaSensor):
    _attr_translation_key = "active_mode_temperature_setpoint"

    @property
    def native_value(self) -> StateType:
        if active_mode := self._modes_state.active_mode:
            return active_mode.setpoint_temperature
        return None


# The following sensors are all modeled after the diagram shown on page 3 of the MODBUS_C5_manual_EN.pdf manual.


# Extract airflow
class ExtractAirflowSetpoint(FlowMetaSensor):
    _attr_translation_key = "extract_airflow_setpoint"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.extract_flow_setpoint


class ExtractAirflowActual(FlowMetaSensor):
    _attr_translation_key = "extract_airflow_actual"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.exhaust_flow


class ExtractAirflowFanLevel(PercentageMetaSensor):
    _attr_translation_key = "extract_airflow_fan_level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.exhaust_fan_level


# Exhaust temperature
class ExhaustTemperature(TemperatureMetaSensor):
    _attr_translation_key = "exhaust_temperature"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.exhaust_temp


# Extract temperature
class ExtractTemperatureSetpoint(TemperatureMetaSensor):
    _attr_translation_key = "extract_temperature_setpoint"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.temp_setpoint


class ExtractTemperatureActual(TemperatureMetaSensor):
    _attr_translation_key = "extract_temperature_actual"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.extract_temp


# Supply temperature


class SupplyTemperatureSetpoint(TemperatureMetaSensor):
    _attr_translation_key = "supply_temperature_setpoint"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.supply_air_temp_setpoint


class SupplyTemperatureActual(TemperatureMetaSensor):
    _attr_translation_key = "supply_temperature_actual"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.supply_temp


# Outdoot temperature
class OutdoorTemperature(TemperatureMetaSensor):
    _attr_translation_key = "outdoor_temperature"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.outdoor_temp


# Heat exchanger
class HeatExchangerLevel(PercentageMetaSensor):
    _attr_translation_key = "heat_exchanger_level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.heat_exchanger_level


class HeatExchangerEfficiency(PercentageMetaSensor):
    _attr_translation_key = "heat_exchanger_efficiency"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.heat_exchanger_thermal_efficiency


# Internal supply temperature
class InternalSupplyTemperature(TemperatureMetaSensor):
    _attr_translation_key = "internal_supply_temperature"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.internal_supply_temp


# Supply airflow
class SupplyAirflowSetpoint(FlowMetaSensor):
    _attr_translation_key = "supply_airflow_setpoint"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.supply_flow_setpoint


class SupplyAirflowActual(FlowMetaSensor):
    _attr_translation_key = "supply_airflow_actual"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.supply_flow


class SupplyAirflowFanLevel(PercentageMetaSensor):
    _attr_translation_key = "supply_airflow_fan_level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.supply_fan_level


# Return water temperature
class ReturnWaterTemperature(TemperatureMetaSensor):
    _attr_translation_key = "return_water_temperature"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.return_water_temp


# Air heaters/coolers
class ElectricalHeaterLevel(PercentageMetaSensor):
    _attr_translation_key = "electrical_heater_level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.electric_heater_level


class WaterHeaterLevel(PercentageMetaSensor):
    _attr_translation_key = "water_heater_level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.water_heater_level


class DxLevel(PercentageMetaSensor):
    _attr_translation_key = "dx_level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.dx_level


class HeatpumpLevel(PercentageMetaSensor):
    _attr_translation_key = "heatpump_level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.heat_pump_level


class WaterCoolerLevel(PercentageMetaSensor):
    _attr_translation_key = "water_cooler_level"

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.water_cooler_level

class AirQualitySensorType(KomfoventEntity, SensorEntity):
    _attr_translation_key = "air_quality_sensor_type"

    @property
    def native_value(self) -> StateType:
        # Return the name of the enum for better readability
        return getattr(self._monitoring_state.air_quality_sensor_type, "name", str(self._monitoring_state.air_quality_sensor_type))

class AirQualityLevel(KomfoventEntity, SensorEntity):
    _attr_translation_key = "air_quality_level"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType:
        return self._monitoring_state.air_quality_level
