from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import KomfoventCoordinator, KomfoventEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> bool:
    coord: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AhuControl(coord)])
    return True


class AhuControl(KomfoventEntity, SwitchEntity):
    @property
    def name(self) -> str:
        return f"{super().name} Ahu Control"

    # TODO icon
    @property
    def is_on(self) -> bool:
        return self._modes_state.ahu

    async def turn_on(self, **kwargs: Any) -> None:
        await self._modes_client.set_ahu_on(True)

    async def turn_off(self, **kwargs: Any) -> None:
        await self._modes_client.set_ahu_on(False)
