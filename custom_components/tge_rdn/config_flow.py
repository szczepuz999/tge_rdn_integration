"""Config flow for TGE RDN integration."""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import *

class TGERDNConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id("tge_rdn_integration")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="TGE RDN Energy Prices", data={}, options=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_UNIT, default=DEFAULT_UNIT): vol.In([UNIT_PLN_KWH, UNIT_PLN_MWH, UNIT_EUR_KWH, UNIT_EUR_MWH]),
                vol.Required(CONF_EXCHANGE_FEE, default=DEFAULT_EXCHANGE_FEE): vol.Coerce(float),
                vol.Required(CONF_VAT_RATE, default=DEFAULT_VAT_RATE): vol.Coerce(float),
                vol.Required(CONF_DIST_LOW, default=DEFAULT_DIST_LOW): vol.Coerce(float),
                vol.Required(CONF_DIST_MED, default=DEFAULT_DIST_MED): vol.Coerce(float),
                vol.Required(CONF_DIST_HIGH, default=DEFAULT_DIST_HIGH): vol.Coerce(float),
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TGERDNOptionsFlow(config_entry)

class TGERDNOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        opts = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_UNIT, default=opts.get(CONF_UNIT, DEFAULT_UNIT)): vol.In([UNIT_PLN_KWH, UNIT_PLN_MWH, UNIT_EUR_KWH, UNIT_EUR_MWH]),
                vol.Required(CONF_EXCHANGE_FEE, default=opts.get(CONF_EXCHANGE_FEE, DEFAULT_EXCHANGE_FEE)): vol.Coerce(float),
                vol.Required(CONF_VAT_RATE, default=opts.get(CONF_VAT_RATE, DEFAULT_VAT_RATE)): vol.Coerce(float),
                vol.Required(CONF_DIST_LOW, default=opts.get(CONF_DIST_LOW, DEFAULT_DIST_LOW)): vol.Coerce(float),
                vol.Required(CONF_DIST_MED, default=opts.get(CONF_DIST_MED, DEFAULT_DIST_MED)): vol.Coerce(float),
                vol.Required(CONF_DIST_HIGH, default=opts.get(CONF_DIST_HIGH, DEFAULT_DIST_HIGH)): vol.Coerce(float),
            })
        )
