"""Config flow for TGE RDN integration."""
import json
import os
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import *

def load_tariffs():
    """Load tariffs from JSON file (blocking I/O — call via executor)."""
    path = os.path.join(os.path.dirname(__file__), "tariffs.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sellers": [], "distributors": []}

class TGERDNConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow."""
    VERSION = 1

    def __init__(self):
        """Initialize."""
        self.data = {}
        self.tariffs_data = None

    async def async_step_user(self, user_input=None):
        """Step 1: Select Dealer and Distributor."""
        if self.tariffs_data is None:
            self.tariffs_data = await self.hass.async_add_executor_job(load_tariffs)

        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_tariffs()

        sellers = [d["name"] for d in self.tariffs_data.get("sellers", [])]
        distributors = [d["name"] for d in self.tariffs_data.get("distributors", [])]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_DEALER): vol.In(sellers),
                vol.Required(CONF_DISTRIBUTOR): vol.In(distributors),
                vol.Required(CONF_UNIT, default=DEFAULT_UNIT): vol.In(
                    [UNIT_PLN_KWH, UNIT_PLN_MWH, UNIT_EUR_KWH, UNIT_EUR_MWH]
                ),
                vol.Required(CONF_VAT_RATE, default=DEFAULT_VAT_RATE): vol.Coerce(float),
            })
        )

    async def async_step_tariffs(self, user_input=None):
        """Step 2: Select Tariffs."""
        if user_input is not None:
            self.data.update(user_input)
            # Auto-populate fees from JSON for dynamic tariffs
            dealer_tariff_name = self.data.get(CONF_DEALER_TARIFF)
            dealer_name = self.data.get(CONF_DEALER)
            for d in self.tariffs_data.get("sellers", []):
                if d["name"] == dealer_name:
                    for t in d.get("tariffs", []):
                        if t["name"] == dealer_tariff_name:
                            if t.get("is_dynamic", False):
                                self.data[CONF_EXCHANGE_FEE] = t.get("exchange_fee", DEFAULT_EXCHANGE_FEE)
                                self.data[CONF_TRADE_FEE] = t.get("trade_fee", DEFAULT_TRADE_FEE)
                            break
                    break
            await self.async_set_unique_id("tge_rdn_integration")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="TGE RDN Energy Prices", data={}, options=self.data)

        dealer_name = self.data.get(CONF_DEALER)
        dist_name = self.data.get(CONF_DISTRIBUTOR)

        dealer_tariffs = []
        for d in self.tariffs_data.get("sellers", []):
            if d["name"] == dealer_name:
                dealer_tariffs = [t["name"] for t in d.get("tariffs", [])]
                break

        dist_tariffs = []
        for d in self.tariffs_data.get("distributors", []):
            if d["name"] == dist_name:
                dist_tariffs = [t["name"] for t in d.get("tariffs", [])]
                break

        return self.async_show_form(
            step_id="tariffs",
            data_schema=vol.Schema({
                vol.Required(CONF_DEALER_TARIFF): vol.In(dealer_tariffs),
                vol.Required(CONF_DIST_TARIFF): vol.In(dist_tariffs),
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TGERDNOptionsFlow(config_entry)

class TGERDNOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for TGE RDN."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._config_entry = config_entry
        self._data = dict(config_entry.options)
        self._tariffs_data = None

    async def async_step_init(self, user_input=None):
        """Step 1: Select Seller and Distributor."""
        if self._tariffs_data is None:
            self._tariffs_data = await self.hass.async_add_executor_job(load_tariffs)

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_tariffs()

        opts = self._config_entry.options
        sellers = [d["name"] for d in self._tariffs_data.get("sellers", [])]
        distributors = [d["name"] for d in self._tariffs_data.get("distributors", [])]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_DEALER, default=opts.get(CONF_DEALER, sellers[0] if sellers else "")): vol.In(sellers),
                vol.Required(CONF_DISTRIBUTOR, default=opts.get(CONF_DISTRIBUTOR, distributors[0] if distributors else "")): vol.In(distributors),
                vol.Required(CONF_UNIT, default=opts.get(CONF_UNIT, DEFAULT_UNIT)): vol.In(
                    [UNIT_PLN_KWH, UNIT_PLN_MWH, UNIT_EUR_KWH, UNIT_EUR_MWH]
                ),
                vol.Required(CONF_VAT_RATE, default=opts.get(CONF_VAT_RATE, DEFAULT_VAT_RATE)): vol.Coerce(float),
            })
        )

    async def async_step_tariffs(self, user_input=None):
        """Step 2: Select Tariffs."""
        if user_input is not None:
            self._data.update(user_input)
            # Auto-populate fees from JSON for dynamic tariffs
            dealer_tariff_name = self._data.get(CONF_DEALER_TARIFF)
            dealer_name = self._data.get(CONF_DEALER)
            for d in self._tariffs_data.get("sellers", []):
                if d["name"] == dealer_name:
                    for t in d.get("tariffs", []):
                        if t["name"] == dealer_tariff_name:
                            if t.get("is_dynamic", False):
                                self._data[CONF_EXCHANGE_FEE] = t.get("exchange_fee", DEFAULT_EXCHANGE_FEE)
                                self._data[CONF_TRADE_FEE] = t.get("trade_fee", DEFAULT_TRADE_FEE)
                            break
                    break
            return self.async_create_entry(title="", data=self._data)

        opts = self._data
        dealer_name = opts.get(CONF_DEALER)
        dist_name = opts.get(CONF_DISTRIBUTOR)

        dealer_tariffs = []
        for d in self._tariffs_data.get("sellers", []):
            if d["name"] == dealer_name:
                dealer_tariffs = [t["name"] for t in d.get("tariffs", [])]
                break

        dist_tariffs = []
        for d in self._tariffs_data.get("distributors", []):
            if d["name"] == dist_name:
                dist_tariffs = [t["name"] for t in d.get("tariffs", [])]
                break

        return self.async_show_form(
            step_id="tariffs",
            data_schema=vol.Schema({
                vol.Required(CONF_DEALER_TARIFF, default=opts.get(CONF_DEALER_TARIFF, dealer_tariffs[0] if dealer_tariffs else "")): vol.In(dealer_tariffs),
                vol.Required(CONF_DIST_TARIFF, default=opts.get(CONF_DIST_TARIFF, dist_tariffs[0] if dist_tariffs else "")): vol.In(dist_tariffs),
            })
        )
