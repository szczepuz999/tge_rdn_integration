"""TGE RDN integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TGE RDN from a config entry."""

    # Sprawdź dostępność wymaganych bibliotek
    try:
        import pandas
        import requests
        import openpyxl
        _LOGGER.info("All required libraries are available")
    except ImportError as err:
        _LOGGER.error(
            "Required libraries for TGE RDN integration are not available: %s. "
            "Home Assistant will attempt to install them automatically. "
            "Please wait and restart Home Assistant after installation completes.",
            err
        )
        raise ConfigEntryNotReady(f"Missing required libraries: {err}")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(
        entry, PLATFORMS
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
