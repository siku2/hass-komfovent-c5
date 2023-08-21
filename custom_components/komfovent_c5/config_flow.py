import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_BASE, CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from . import api
from .const import DOMAIN

logger = logging.getLogger(__name__)

ERR_CONNECT_FAILED = "connect_failed"


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}
        if user_input is not None:
            host: str = user_input[CONF_HOST]
            port: int = user_input[CONF_PORT]
            client = api.Client(host=host, port=port)

            try:
                await client.connect(connect_timeout=10.0)
            except (asyncio.TimeoutError, ConnectionError):
                errors[CONF_BASE] = ERR_CONNECT_FAILED
            else:
                await client.disconnect()

            if not errors:
                return self.async_create_entry(title=host, data=user_input)

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
