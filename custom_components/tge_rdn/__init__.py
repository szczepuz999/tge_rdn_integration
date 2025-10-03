"""TGE RDN integration."""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

def _check_libraries():
    """Check required libraries synchronously outside event loop."""
    try:
        import pandas  # noqa: F401
        import requests  # noqa: F401
        import openpyxl  # noqa: F401
        _LOGGER.info("All required libraries for TGE RDN are available")
        return True
    except ImportError as err:
        _LOGGER.error(
            "Required libraries for TGE RDN integration are not available: %s. "
            "Home Assistant will attempt to install them automatically. "
            "Please wait and restart Home Assistant after installation completes.",
            err,
        )
        raise ConfigEntryNotReady(f"Missing required libraries: {err}")

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TGE RDN from a config entry."""
    # Check libraries in executor to avoid blocking event loop
    await hass.async_add_executor_job(_check_libraries)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload TGE RDN config entry."""
    unload_results = []
    for platform in PLATFORMS:
        result = await hass.config_entries.async_forward_entry_unload(entry, platform)
        unload_results.append(result)

    if all(unload_results):
        hass.data[DOMAIN].pop(entry.entry_id)

    return all(unload_results)
