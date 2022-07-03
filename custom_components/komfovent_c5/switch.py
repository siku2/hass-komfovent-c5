import time
from typing import Any, Optional

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


class CachedKomfoventSwitch(KomfoventEntity, SwitchEntity):
    CACHE_EXPIRATION = 30

    _cached_is_on: Optional[bool]
    _cached_is_on_ts: Optional[float]

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        super().__init__(coordinator)
        self._cached_is_on = None
        self._cached_is_on_ts = None

    @property
    def is_on(self) -> bool:
        if cached := self.cached_is_on is not None:
            return cached
        return self.uncached_is_on

    @property
    def cached_is_on(self) -> Optional[bool]:
        if self._cached_is_on is None or self._cached_is_on_ts is None:
            return None
        diff = time.time() - self._cached_is_on_ts
        if diff >= self.CACHE_EXPIRATION:
            # reset because cache expired
            self._cached_is_on = None
            self._cached_is_on_ts = None
        return self._cached_is_on

    @property
    def uncached_is_on(self) -> bool:
        raise NotImplementedError()

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._cached_is_on = True
        self._cached_is_on_ts = time.time()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._cached_is_on = False
        self._cached_is_on_ts = time.time()


class AhuControl(CachedKomfoventSwitch):
    @property
    def name(self) -> str:
        return f"{super().name} Ahu Control"

    @property
    def uncached_is_on(self) -> bool:
        return self._modes_state.ahu

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._modes_client.set_ahu_on(True)
        await super().async_turn_on(**kwargs)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._modes_client.set_ahu_on(False)
        await super().async_turn_off(**kwargs)


class OcvControl(CachedKomfoventSwitch):
    @property
    def name(self) -> str:
        return f"{super().name} Ocv Control"

    @property
    def entity_category(self) -> EntityCategory:
        return EntityCategory.CONFIG

    @property
    def uncached_is_on(self) -> bool:
        return self._functions_state.ocv_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._functions_client.set_ocv_enabled(True)
        await super().async_turn_on(**kwargs)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._functions_client.set_ocv_enabled(False)
        await super().async_turn_off(**kwargs)
