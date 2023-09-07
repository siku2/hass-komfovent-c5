import dataclasses
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import api, services
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, _config) -> bool:
    hass.data[DOMAIN] = {}
    await services.register(hass)
    return True


@dataclasses.dataclass(slots=True, kw_only=True)
class KomfoventState:
    active_alarms: list[api.Alarm]
    alarm_history_count: int
    functions: api.FunctionsState
    modes: api.ModesState
    monitoring: api.MonitoringState

    @classmethod
    async def read_all(cls, client: api.Client, settings: api.SettingsState):
        alarms = api.Alarms(client)
        return cls(
            active_alarms=await alarms.read_active(),
            alarm_history_count=await alarms.read_history_count(),
            functions=await api.Functions(client).read_all(),
            modes=await api.Modes(client).read_all(),
            monitoring=await api.Monitoring(client).read_all(units=settings.flow_units),
        )


class KomfoventCoordinator(DataUpdateCoordinator[KomfoventState]):
    host_id: str

    def __init__(
        self,
        hass: HomeAssistant,
        client: api.Client,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.__client = client
        self.__settings: api.SettingsState | None = None

        host, port = client.host_and_port
        self.host_id = f"{host}:{port}"

    @property
    def client(self) -> api.Client:
        return self.__client

    @property
    def settings_state(self) -> api.SettingsState:
        assert self.__settings
        return self.__settings

    @property
    def device_info(self) -> DeviceInfo:
        assert self.__device_info
        return self.__device_info

    async def _async_update_data(self) -> KomfoventState:
        await self.__client.connect()
        return await KomfoventState.read_all(self.client, self.settings_state)

    async def _do_init(self) -> None:
        await self.__client.connect()
        self.__settings = await api.Settings(self.__client).read_all()

        try:
            sw_version = await api.Service(self.__client).read_firmware_version()
            sw_version = f"{sw_version / 1000.0:.3f}"
        except Exception:
            _LOGGER.warn("failed to read firmware version", exc_info=True)
            sw_version = None

        self.__device_info = DeviceInfo(
            identifiers={(DOMAIN, self.__settings.ahu_serial_number)},
            name=self.__settings.ahu_name,
            configuration_url=f"http://{self.__client.host_and_port[0]}",
            manufacturer="KOMFOVENT",
            sw_version=sw_version,
        )

    async def async_config_entry_first_refresh(self) -> None:
        try:
            await self._do_init()
        except Exception as exc:
            raise ConfigEntryNotReady from exc
        await super().async_config_entry_first_refresh()

    async def async_shutdown(self) -> None:
        await super().async_shutdown()
        await self.client.disconnect()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    coordinator = KomfoventCoordinator(hass, api.Client(host=host, port=port))
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: KomfoventCoordinator | None = hass.data[DOMAIN].pop(entry.entry_id)
        if coordinator:
            await coordinator.async_shutdown()

    return unload_ok


class KomfoventEntity(CoordinatorEntity[KomfoventCoordinator]):
    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        super().__init__(coordinator)

        settings = self.coordinator.settings_state

        self._attr_has_entity_name = True
        # legacy unique id format for compatibility
        self._attr_unique_id = (
            f"{DOMAIN}-{settings.ahu_serial_number}-{type(self).__qualname__}"
        )
        self._attr_device_info = self.coordinator.device_info

    @property
    def _active_alarms(self) -> list[api.Alarm]:
        return self.coordinator.data.active_alarms

    @property
    def _functions_client(self) -> api.Functions:
        return api.Functions(self.coordinator.client)

    @property
    def _functions_state(self) -> api.FunctionsState:
        return self.coordinator.data.functions

    @property
    def _modes_client(self) -> api.Modes:
        return api.Modes(self.coordinator.client)

    @property
    def _modes_state(self) -> api.ModesState:
        return self.coordinator.data.modes

    @property
    def _monitoring_state(self) -> api.MonitoringState:
        return self.coordinator.data.monitoring
