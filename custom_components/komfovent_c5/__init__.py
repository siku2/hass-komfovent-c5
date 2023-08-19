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
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import services
from .api import (
    Alarm,
    AlarmHistoryEntry,
    Alarms,
    Client,
    Functions,
    FunctionsState,
    Modes,
    ModesState,
    Monitoring,
    MonitoringState,
    Settings,
    SettingsState,
)
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, _config) -> bool:
    hass.data[DOMAIN] = {}
    await services.register(hass)
    return True


@dataclasses.dataclass()
class KomfoventState:
    active_alarms: list[Alarm]
    alarm_history: list[AlarmHistoryEntry]
    functions: FunctionsState
    modes: ModesState
    monitoring: MonitoringState

    @classmethod
    async def read_all(cls, client: Client, settings: SettingsState):
        alarms = Alarms(client)
        return cls(
            active_alarms=await alarms.read_active(),
            alarm_history=await alarms.read_history(),
            functions=await Functions(client).read_all(),
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
    except Exception as exc:
        raise ConfigEntryNotReady() from exc

    coordinator = await KomfoventCoordinator.build(
        hass,
        client,
        entry,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await setup_coordinator(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: KomfoventCoordinator | None = hass.data[DOMAIN].pop(entry.entry_id)
        if coordinator:
            await coordinator.destroy()

    return unload_ok


class KomfoventEntity(CoordinatorEntity):
    coordinator: KomfoventCoordinator

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def _active_alarms(self) -> list[Alarm]:
        return self.coordinator.data.active_alarms

    @property
    def _alarm_history(self) -> list[AlarmHistoryEntry]:
        return self.coordinator.data.alarm_history

    @property
    def _functions_client(self) -> Functions:
        return Functions(self.coordinator.client)

    @property
    def _functions_state(self) -> FunctionsState:
        return self.coordinator.data.functions

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
