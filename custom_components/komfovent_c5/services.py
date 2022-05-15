import functools
import logging
from typing import TYPE_CHECKING, Optional

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry
from homeassistant.helpers.service import ServiceTargetSelector

from .api import Modes, OperationMode
from .const import DOMAIN

if TYPE_CHECKING:
    from . import KomfoventCoordinator


_LOGGER = logging.getLogger(__name__)

ATTR_MODE = "mode"
ATTR_TEMPERATURE = "temperature"

SET_SETPOINT_TEMPERATURE_SCHEMA = cv.make_entity_service_schema(
    {
        vol.Optional(ATTR_MODE, default=OperationMode.SPECIAL): cv.enum(OperationMode),
        vol.Required(ATTR_TEMPERATURE): cv.positive_float(),
    }
)


async def set_setpoint_temperature(hass: HomeAssistant, call: ServiceCall) -> None:
    selector = ServiceTargetSelector(call)
    mode: OperationMode = call.data[ATTR_MODE]
    temperature: float = call.data[ATTR_TEMPERATURE]

    dev_reg = device_registry.async_get(hass)

    domain_data = hass.data[DOMAIN]

    for device_id in selector.device_ids:
        device = dev_reg.async_get(device_id)
        if not device:
            _LOGGER.warn("device not found: %s", device_id)
            continue
        for entry_id in device.config_entries:
            coordinator: Optional["KomfoventCoordinator"] = domain_data.get(entry_id)
            if not coordinator:
                continue
            try:
                modes = Modes(coordinator.client)
                mode_regs = modes.mode_registers(mode)
                mode_regs.set_setpoint_temperature(temperature)
            except Exception:
                _LOGGER.exception(
                    "failed to set setpoint temperature for device id %s", device_id
                )


async def register(hass: HomeAssistant) -> None:
    hass.services.async_register(
        DOMAIN,
        "set_setpoint_temperature",
        functools.partial(set_setpoint_temperature, hass),
    )
