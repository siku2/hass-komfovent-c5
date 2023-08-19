from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import KomfoventCoordinator, KomfoventEntity
from .api import FlowControlMode, OperationMode, TemperatureControlMode
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    coord: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            OpModeSelect(coord),
            FlowControlModeSelect(coord),
            TempControlModeSelect(coord),
        ]
    )
    return True


class OpModeSelect(KomfoventEntity, SelectEntity):
    _attr_translation_key = "op_mode"
    _attr_options = [mode.name for mode in OperationMode.selectable_modes()]

    @property
    def current_option(self) -> str:
        return self._modes_state.operation_mode.name

    async def async_select_option(self, option: str) -> None:
        mode = OperationMode[option.upper()]
        await self._modes_client.set_operation_mode(mode)
        await self.coordinator.async_request_refresh()


class FlowControlModeSelect(KomfoventEntity, SelectEntity):
    _attr_translation_key = "flow_control_mode"
    _attr_options = [mode.name for mode in FlowControlMode.__members__.values()]

    @property
    def current_option(self) -> str:
        return self._modes_state.flow_control_mode.name

    async def async_select_option(self, option: str) -> None:
        mode = FlowControlMode[option.upper()]
        await self._modes_client.set_flow_control_mode(mode)
        await self.coordinator.async_request_refresh()


class TempControlModeSelect(KomfoventEntity, SelectEntity):
    _attr_translation_key = "temperature_control_mode"
    _attr_options = [mode.name for mode in TemperatureControlMode.__members__.values()]

    @property
    def current_option(self) -> str:
        return self._modes_state.temperature_control_mode.name

    async def async_select_option(self, option: str) -> None:
        mode = TemperatureControlMode[option.upper()]
        await self._modes_client.set_temperature_control_mode(mode)
        await self.coordinator.async_request_refresh()
