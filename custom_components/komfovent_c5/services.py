import functools
import logging
from typing import TYPE_CHECKING, Optional

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry

from .api import Modes, OperationMode
from .const import DOMAIN

if TYPE_CHECKING:
    from . import KomfoventCoordinator


_LOGGER = logging.getLogger(__name__)

ATTR_DEVICE = "device"
ATTR_MODE = "mode"
ATTR_TEMPERATURE = "temperature"

SET_SETPOINT_TEMPERATURE_SCHEMA = vol.Schema(
    {
        ATTR_DEVICE: vol.Any(
            vol.All(cv.ensure_list, [vol.Any(cv.dynamic_template, str)])
        ),
        vol.Optional(ATTR_MODE, default=None): vol.Any(cv.enum(OperationMode), None),
        ATTR_TEMPERATURE: cv.positive_float,
    }
)


async def set_setpoint_temperature(hass: HomeAssistant, call: ServiceCall) -> None:
    device_ids = set(call.data[ATTR_DEVICE])
    mode: OperationMode = call.data[ATTR_MODE] or OperationMode.SPECIAL
    temperature: float = call.data[ATTR_TEMPERATURE]

    dev_reg = device_registry.async_get(hass)

    domain_data = hass.data[DOMAIN]

    for device_id in device_ids:
        device = dev_reg.async_get(device_id)
        if not device:
            _LOGGER.warn("device not found: %s", device_id)
            continue
        for entry_id in device.config_entries:
            coordinator: Optional["KomfoventCoordinator"] = domain_data.get(entry_id)
            if not coordinator:
                _LOGGER.warning("config entry has no coordinator: %s", entry_id)
                continue
            try:
                modes = Modes(coordinator.client)
                mode_regs = modes.mode_registers(mode)
                await mode_regs.set_setpoint_temperature(temperature)
            except Exception:
                _LOGGER.exception(
                    "failed to set setpoint temperature for device id %s", device_id
                )


async def register(hass: HomeAssistant) -> None:
    hass.services.async_register(
        DOMAIN,
        "set_setpoint_temperature",
        functools.partial(set_setpoint_temperature, hass),
        SET_SETPOINT_TEMPERATURE_SCHEMA,
    )
