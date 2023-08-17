import functools
import logging
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry

from .api import Alarms, ConfigurationFlags, Modes, OperationMode
from .const import DOMAIN

if TYPE_CHECKING:
    from . import KomfoventCoordinator


_LOGGER = logging.getLogger(__name__)

ATTR_DEVICE = "device"
ATTR_MODE = "mode"
ATTR_TEMPERATURE = "temperature"
ATTR_VALUE = "value"

DEVICE_SCHEMA = vol.Any(vol.All(cv.ensure_list, [vol.Any(cv.dynamic_template, str)]))
MODE_SCHEMA = vol.Any(cv.enum(OperationMode), None)


def coordinators_in_call(
    hass: HomeAssistant, device_ids: Iterable[str]
) -> Iterator[tuple[str, "KomfoventCoordinator"]]:
    dev_reg = device_registry.async_get(hass)
    domain_data = hass.data[DOMAIN]

    for device_id in device_ids:
        device = dev_reg.async_get(device_id)
        if not device:
            _LOGGER.warn("device not found: %s", device_id)
            continue
        for entry_id in device.config_entries:
            coordinator: "KomfoventCoordinator" | None = domain_data.get(entry_id)
            if not coordinator:
                _LOGGER.warning("config entry has no coordinator: %s", entry_id)
                continue
            yield device_id, coordinator


SET_SETPOINT_TEMPERATURE_SCHEMA = vol.Schema(
    {
        ATTR_DEVICE: DEVICE_SCHEMA,
        vol.Optional(ATTR_MODE, default=None): MODE_SCHEMA,
        ATTR_TEMPERATURE: cv.positive_float,
    }
)


async def set_setpoint_temperature(hass: HomeAssistant, call: ServiceCall) -> None:
    device_ids = set(call.data[ATTR_DEVICE])
    mode: OperationMode = call.data[ATTR_MODE] or OperationMode.SPECIAL
    temperature: float = call.data[ATTR_TEMPERATURE]

    for device_id, coordinator in coordinators_in_call(hass, device_ids):
        try:
            mode_regs = Modes(coordinator.client).mode_registers(mode)
            await mode_regs.set_setpoint_temperature(temperature)
        except Exception:
            _LOGGER.exception(
                "failed to set setpoint temperature for device id %s", device_id
            )


SET_SUPPLY_FLOW_SCHEMA = vol.Schema(
    {
        ATTR_DEVICE: DEVICE_SCHEMA,
        vol.Optional(ATTR_MODE, default=None): MODE_SCHEMA,
        ATTR_VALUE: cv.positive_int,
    }
)


async def set_supply_flow(hass: HomeAssistant, call: ServiceCall) -> None:
    device_ids = set(call.data[ATTR_DEVICE])
    mode: OperationMode = call.data[ATTR_MODE] or OperationMode.SPECIAL
    value: int = call.data[ATTR_VALUE]

    for device_id, coordinator in coordinators_in_call(hass, device_ids):
        try:
            mode_regs = Modes(coordinator.client).mode_registers(mode)
            await mode_regs.set_supply_flow(value)
        except Exception:
            _LOGGER.exception("failed to set supply flow for device id %s", device_id)


SET_EXTRACT_FLOW_SCHEMA = SET_SUPPLY_FLOW_SCHEMA


async def set_extract_flow(hass: HomeAssistant, call: ServiceCall) -> None:
    device_ids = set(call.data[ATTR_DEVICE])
    mode: OperationMode = call.data[ATTR_MODE] or OperationMode.SPECIAL
    value: int = call.data[ATTR_VALUE]

    for device_id, coordinator in coordinators_in_call(hass, device_ids):
        try:
            mode_regs = Modes(coordinator.client).mode_registers(mode)
            await mode_regs.set_extract_flow(value)
        except Exception:
            _LOGGER.exception("failed to set extract flow for device id %s", device_id)


SET_SPECIAL_MODE_CONFIG_SCHEMA = vol.Schema(
    {
        ATTR_DEVICE: DEVICE_SCHEMA,
        vol.Optional("dehumidifying", default=None): vol.Any(cv.boolean, None),
        vol.Optional("humidifying", default=None): vol.Any(cv.boolean, None),
        vol.Optional("recirculation", default=None): vol.Any(cv.boolean, None),
        vol.Optional("cooling", default=None): vol.Any(cv.boolean, None),
        vol.Optional("heating", default=None): vol.Any(cv.boolean, None),
    }
)


async def set_special_mode_config(hass: HomeAssistant, call: ServiceCall) -> None:
    device_ids = set(call.data[ATTR_DEVICE])
    dehumidifying: bool | None = call.data["dehumidifying"]
    humidifying: bool | None = call.data["humidifying"]
    recirculation: bool | None = call.data["recirculation"]
    cooling: bool | None = call.data["cooling"]
    heating: bool | None = call.data["heating"]

    def maybe_set_bit(
        flags: ConfigurationFlags, flag: ConfigurationFlags, control: bool | None
    ) -> ConfigurationFlags:
        if control is True:
            return flags | flag
        elif control is False:
            return flags & (~flag)
        else:
            return flags

    for device_id, coordinator in coordinators_in_call(hass, device_ids):
        try:
            mode_regs = Modes(coordinator.client).mode_registers(OperationMode.SPECIAL)
            flags = await mode_regs.configuration()
            flags = maybe_set_bit(
                flags, ConfigurationFlags.DEHUMIDIFYING, dehumidifying
            )
            flags = maybe_set_bit(flags, ConfigurationFlags.HUMIDIFYING, humidifying)
            flags = maybe_set_bit(
                flags, ConfigurationFlags.RECIRCULATION, recirculation
            )
            flags = maybe_set_bit(flags, ConfigurationFlags.COOLING, cooling)
            flags = maybe_set_bit(flags, ConfigurationFlags.HEATING, heating)
            _LOGGER.info("setting config for device id %s: %s", device_id, flags)
            await mode_regs.set_configuration(flags)
        except Exception:
            _LOGGER.exception("failed to set extract flow for device id %s", device_id)


RESET_ACTIVE_ALARMS_SCHEMA = vol.Schema(
    {
        ATTR_DEVICE: DEVICE_SCHEMA,
    }
)


async def reset_active_alarms(hass: HomeAssistant, call: ServiceCall) -> None:
    device_ids = set(call.data[ATTR_DEVICE])
    for device_id, coordinator in coordinators_in_call(hass, device_ids):
        try:
            alarms = Alarms(coordinator.client)
            _LOGGER.info("resetting active alarms for device id %s: %s", device_id)
            await alarms.reset_active()
        except Exception:
            _LOGGER.exception("failed to set extract flow for device id %s", device_id)


async def register(hass: HomeAssistant) -> None:
    hass.services.async_register(
        DOMAIN,
        "set_setpoint_temperature",
        functools.partial(set_setpoint_temperature, hass),
        SET_SETPOINT_TEMPERATURE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "set_supply_flow",
        functools.partial(set_supply_flow, hass),
        SET_SUPPLY_FLOW_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "set_extract_flow",
        functools.partial(set_extract_flow, hass),
        SET_EXTRACT_FLOW_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "set_special_mode_config",
        functools.partial(set_special_mode_config, hass),
        SET_SPECIAL_MODE_CONFIG_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "reset_active_alarms",
        functools.partial(reset_active_alarms, hass),
        RESET_ACTIVE_ALARMS_SCHEMA,
    )
