"""Config flow for TGE RDN integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import CONF_NAME
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    UNIT_PLN_MWH,
    UNIT_PLN_KWH,
    UNIT_EUR_MWH,
    UNIT_EUR_KWH,
    CONF_UNIT,
    DEFAULT_UNIT,
    CONF_EXCHANGE_FEE,
    CONF_VAT_RATE,
    CONF_DIST_LOW,
    CONF_DIST_MED,
    CONF_DIST_HIGH,
    DEFAULT_EXCHANGE_FEE,
    DEFAULT_VAT_RATE,
    DEFAULT_DIST_LOW,
    DEFAULT_DIST_MED,
    DEFAULT_DIST_HIGH,
    REQUIRED_LIBRARIES,
)

_LOGGER = logging.getLogger(__name__)

UNIT_OPTIONS = [
    UNIT_PLN_MWH,
    UNIT_PLN_KWH,
    UNIT_EUR_MWH,
    UNIT_EUR_KWH,
]

def _validate_libraries():
    """Validate required libraries synchronously."""
    try:
        import pandas  # noqa: F401
        import requests  # noqa: F401
        import openpyxl  # noqa: F401
        return True
    except ImportError as err:
        _LOGGER.error("Required libraries not available: %s", err)
        return False

async def validate_libraries(hass: HomeAssistant) -> bool:
    """Validate that required libraries are available."""
    return await hass.async_add_executor_job(_validate_libraries)

class TGERDNConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TGE RDN."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Check library availability
            if not await validate_libraries(self.hass):
                errors["base"] = "missing_libraries"
            else:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }),
            errors=errors,
            description_placeholders={
                "required_libraries": ", ".join(REQUIRED_LIBRARIES)
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return TGERDNOptionsFlowHandler(config_entry)

class TGERDNOptionsFlowHandler(config_entries.OptionsFlow):
    """TGE RDN options flow handler - FIXED deprecated API."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        # FIXED: Don't set self.config_entry explicitly (deprecated in HA 2025.12)
        # The config_entry is available through self.config_entry property automatically
        super().__init__()

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Access config_entry through the property (not self.config_entry assignment)
        config_entry = self.config_entry

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_UNIT,
                    default=config_entry.options.get(CONF_UNIT, DEFAULT_UNIT)
                ): vol.In(UNIT_OPTIONS),
                vol.Optional(
                    CONF_EXCHANGE_FEE,
                    default=config_entry.options.get(CONF_EXCHANGE_FEE, DEFAULT_EXCHANGE_FEE)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_VAT_RATE,
                    default=config_entry.options.get(CONF_VAT_RATE, DEFAULT_VAT_RATE)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_DIST_LOW,
                    default=config_entry.options.get(CONF_DIST_LOW, DEFAULT_DIST_LOW)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_DIST_MED,
                    default=config_entry.options.get(CONF_DIST_MED, DEFAULT_DIST_MED)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_DIST_HIGH,
                    default=config_entry.options.get(CONF_DIST_HIGH, DEFAULT_DIST_HIGH)
                ): vol.Coerce(float),
            }),
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class MissingLibraries(HomeAssistantError):
    """Error to indicate missing required libraries."""
