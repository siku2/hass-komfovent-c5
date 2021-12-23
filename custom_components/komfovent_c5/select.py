from typing import List

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import KomfoventCoordinator, KomfoventEntity
from .api import FlowControlMode, OperationMode, TemperatureControlMode
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
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
    @property
    def name(self) -> str:
        return f"{super().name} Operation Mode"

    @property
    def device_class(self) -> str:
        return f"{DOMAIN}__operation_mode"

    @property
    def current_option(self) -> str:
        return self._modes_state.operation_mode.name

    @property
    def options(self) -> List[str]:
        return [mode.name for mode in OperationMode.selectable_modes()]

    async def async_select_option(self, option: str) -> None:
        mode = OperationMode[option]
        await self._modes_client.set_operation_mode(mode)


class FlowControlModeSelect(KomfoventEntity, SelectEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Flow Control Mode"

    @property
    def device_class(self) -> str:
        return f"{DOMAIN}__flow_control_mode"

    @property
    def current_option(self) -> str:
        return self._modes_state.flow_control_mode.name

    @property
    def options(self) -> List[str]:
        return list(FlowControlMode.__members__.keys())

    async def async_select_option(self, option: str) -> None:
        mode = FlowControlMode[option]
        await self._modes_client.set_flow_control_mode(mode)


class TempControlModeSelect(KomfoventEntity, SelectEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Temperature Control Mode"

    @property
    def device_class(self) -> str:
        return f"{DOMAIN}__temperature_control_mode"

    @property
    def current_option(self) -> str:
        return self._modes_state.temperature_control_mode.name

    @property
    def options(self) -> List[str]:
        return list(TemperatureControlMode.__members__.keys())

    async def async_select_option(self, option: str) -> None:
        mode = TemperatureControlMode[option]
        await self._modes_client.set_temperature_control_mode(mode)
