from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import KomfoventCoordinator, KomfoventEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    coord: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AhuControl(coord),
            OcvControl(coord),
        ]
    )
    return True


class AhuControl(KomfoventEntity, SwitchEntity):
    _attr_translation_key = "ahu_control"

    @property
    def is_on(self) -> bool:
        return self._modes_state.ahu

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._modes_client.set_ahu_on(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._modes_client.set_ahu_on(False)
        await self.coordinator.async_request_refresh()


class OcvControl(KomfoventEntity, SwitchEntity):
    _attr_translation_key = "ocv_control"

    @property
    def entity_category(self) -> EntityCategory:
        return EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        return self._functions_state.ocv_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._functions_client.set_ocv_enabled(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._functions_client.set_ocv_enabled(False)
        await self.coordinator.async_request_refresh()
