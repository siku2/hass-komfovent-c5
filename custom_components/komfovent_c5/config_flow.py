import asyncio
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_BASE, CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .api import Client
from .const import DOMAIN

logger = logging.getLogger(__name__)

ERR_CONNECT_FAILED = "connect_failed"


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, info: dict) -> FlowResult:
        errors = {}
        if info is not None:
            host: str = info[CONF_HOST]
            port: int = info[CONF_PORT]

            try:
                _ = await Client.connect(host, port, connect_timeout=5.0)
            except asyncio.TimeoutError:
                errors[CONF_BASE] = ERR_CONNECT_FAILED

            if not errors:
                return self.async_create_entry(title=host, data=info)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=502): cv.port,
                }
            ),
            errors=errors,
        )
