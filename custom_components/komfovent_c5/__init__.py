import asyncio
import dataclasses
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    ATTR_SW_VERSION,
    CONF_HOST,
    CONF_PORT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import services
from .api import (
    Client,
    Modes,
    ModesState,
    Monitoring,
    MonitoringState,
    Settings,
    SettingsState,
)
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, _config) -> bool:
    hass.data[DOMAIN] = {}
    await services.register(hass)
    return True


@dataclasses.dataclass()
class KomfoventState:
    modes: ModesState
    monitoring: MonitoringState

    @classmethod
    async def read_all(cls, client: Client, settings: SettingsState):
        return cls(
            modes=await Modes(client).read_all(),
            monitoring=await Monitoring(client).read_all(units=settings.flow_units),
        )


class KomfoventCoordinator(DataUpdateCoordinator[KomfoventState]):
    client: Client
    settings_state: SettingsState
    host_id: str

    async def __fetch_data(self) -> KomfoventState:
        return await KomfoventState.read_all(self.client, self.settings_state)

    async def _initalize(self, client: Client, entry: ConfigEntry) -> None:
        self.client = client
        self.settings_state = await Settings(client).read_all()
        self.host_id = f"{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"

        self.update_method = self.__fetch_data
        await self.async_refresh()

    @classmethod
    async def build(cls, hass: HomeAssistant, client: Client, entry: ConfigEntry):
        coordinator = cls(
            hass,
            _LOGGER,
            name="state",
            update_interval=timedelta(seconds=30),
        )
        await coordinator._initalize(client, entry)

        return coordinator

    async def destroy(self) -> None:
        await self.client.disconnect()


async def setup_coordinator(hass, entry: ConfigEntry) -> None:
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    _LOGGER.info("connecting to '%s:%d'", host, port)
    try:
        client = await Client.connect(host, port, connect_timeout=10.0)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError("failed to connect in time") from None

    coordinator = await KomfoventCoordinator.build(
        hass,
        client,
        entry,
    )
    hass.data[DOMAIN][entry.entry_id] = coordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await setup_coordinator(hass, entry)

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, platform)

    coordinator: KomfoventCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.destroy()

    return True


class KomfoventEntity(CoordinatorEntity):
    coordinator: KomfoventCoordinator

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def _modes_client(self) -> Modes:
        return Modes(self.coordinator.client)

    @property
    def _modes_state(self) -> ModesState:
        return self.coordinator.data.modes

    @property
    def _monitoring_state(self) -> MonitoringState:
        return self.coordinator.data.monitoring

    @property
    def name(self) -> str:
        return self.coordinator.settings_state.ahu_name

    @property
    def device_info(self) -> dict:
        settings = self.coordinator.settings_state
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, settings.ahu_serial_number)},
            ATTR_NAME: settings.ahu_name,
            ATTR_MANUFACTURER: "KOMFOVENT",
            ATTR_MODEL: "RHP 400 V C5",
            # TODO read controller firmware version from service regs
            ATTR_SW_VERSION: "v1",
        }

    @property
    def unique_id(self) -> str:
        settings = self.coordinator.settings_state
        return f"{DOMAIN}-{settings.ahu_serial_number}-{type(self).__qualname__}"
