from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from . import KomfoventCoordinator, KomfoventEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
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
    @property
    def name(self) -> str:
        return f"{super().name} Ahu Control"

    # TODO icon
    @property
    def is_on(self) -> bool:
        return self._modes_state.ahu

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._modes_client.set_ahu_on(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._modes_client.set_ahu_on(False)


class OcvControl(KomfoventEntity, SwitchEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Ocv Control"

    @property
    def entity_category(self) -> EntityCategory:
        return EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        return self._functions_state.ocv_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._functions_client.set_ocv_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._functions_client.set_ocv_enabled(False)
