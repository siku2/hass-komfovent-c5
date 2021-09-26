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
    async_add_entities(
        [
            VavSensorsRange(c),
            NominalSupplyPressure(c),
            NominalExhaustPressure(c),
            ActiveModeSupplyFlow(c),
            ActiveModeExtractFlow(c),
            ActiveModeTemperatureSetpoint(c),
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


class ActiveModeTemperatureSetpoint(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Active Mode Temperature Setpoint"

    @property
    def device_class(self) -> str:
        return DEVICE_CLASS_TEMPERATURE

    @property
    def native_value(self) -> StateType:
        return self._modes_state.active_mode.setpoint_temperature

    @property
    def native_unit_of_measurement(self) -> str:
        return TEMP_CELSIUS

    @property
    def state_class(self) -> str:
        return STATE_CLASS_MEASUREMENT
