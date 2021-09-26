from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEVICE_CLASS_PRESSURE, PRESSURE_PA
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import StateType

from . import KomfoventCoordinator, KomfoventEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> bool:
    c: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [VavSensorsRange(c), NominalSupplyPressure(c), NominalExhaustPressure(c)]
    )
    return True


class VavSensorsRange(KomfoventEntity, SensorEntity):
    @property
    def name(self) -> str:
        return f"{super().name} VAV sensors range"

    @property
    def device_class(self) -> str:
        return DEVICE_CLASS_PRESSURE

    @property
    def native_value(self) -> StateType:
        return self._modes_state.vav_sensors_range

    @property
    def native_unit_of_measurement(self) -> str:
        return PRESSURE_PA


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
