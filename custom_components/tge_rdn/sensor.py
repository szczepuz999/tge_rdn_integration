"""TGE RDN sensor platform."""
import logging
import asyncio
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any

try:
    import pandas as pd
    import requests
    import openpyxl
    REQUIRED_LIBRARIES_AVAILABLE = True
except ImportError as err:
    REQUIRED_LIBRARIES_AVAILABLE = False
    IMPORT_ERROR = str(err)

import re
import voluptuous as vol

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    TGE_URL_PATTERN,
    UNIT_PLN_MWH,
    UNIT_PLN_KWH,
    UNIT_EUR_MWH,
    UNIT_EUR_KWH,
    CONF_UNIT,
    CONF_TEMPLATE,
    DEFAULT_UNIT,
    DEFAULT_TEMPLATE,
    UPDATE_INTERVAL_CURRENT,
    UPDATE_INTERVAL_NEXT_DAY,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up TGE RDN sensors based on a config entry."""

    # Sprawdź czy wymagane biblioteki są dostępne
    if not REQUIRED_LIBRARIES_AVAILABLE:
        _LOGGER.error(
            "Required libraries not available for TGE RDN integration: %s. "
            "Home Assistant will attempt to install them automatically. "
            "Please restart Home Assistant after installation completes.",
            IMPORT_ERROR
        )
        raise Exception(f"Missing required libraries: {IMPORT_ERROR}")

    coordinator = TGERDNDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entities = []

    # Sensor ceny aktualnej
    entities.append(TGERDNSensor(coordinator, entry, "current_price"))

    # Sensor następnej godziny
    entities.append(TGERDNSensor(coordinator, entry, "next_hour_price"))

    # Sensor średniej ceny dziennej
    entities.append(TGERDNSensor(coordinator, entry, "daily_average"))

    async_add_entities(entities, True)


class TGERDNDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching TGE RDN data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self.entry = entry

        # Określ interwał aktualizacji na podstawie godziny
        update_interval = self._get_update_interval()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    def _get_update_interval(self) -> int:
        """Get update interval based on current time."""
        now = datetime.now()

        # Po północy (00:10) - pobierz dane na dziś
        if now.time() >= time(0, 10) and now.time() <= time(0, 30):
            return UPDATE_INTERVAL_CURRENT

        # O 15:00 - pobierz dane na jutro
        elif now.time() >= time(15, 0) and now.time() <= time(15, 30):
            return UPDATE_INTERVAL_NEXT_DAY

        # W innych godzinach - sprawdzaj co godzinę
        else:
            return 3600

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from TGE."""
        if not REQUIRED_LIBRARIES_AVAILABLE:
            raise UpdateFailed(f"Required libraries not available: {IMPORT_ERROR}")

        try:
            now = datetime.now()

            # Pobierz dane dla dzisiaj
            today_data = await self._fetch_day_data(now)

            # Pobierz dane dla jutra jeśli są dostępne
            tomorrow = now + timedelta(days=1)
            tomorrow_data = await self._fetch_day_data(tomorrow)

            return {
                "today": today_data,
                "tomorrow": tomorrow_data,
                "last_update": now,
            }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with TGE API: {err}")

    async def _fetch_day_data(self, date: datetime) -> Optional[Dict[str, Any]]:
        """Fetch data for specific day."""
        try:
            url = TGE_URL_PATTERN.format(
                year=date.year,
                month=date.month,
                day=date.day
            )

            _LOGGER.debug(f"Fetching data from: {url}")

            response = await self.hass.async_add_executor_job(
                self._download_file, url
            )

            if response is None:
                _LOGGER.warning(f"No data available for {date.date()}")
                return None

            return await self.hass.async_add_executor_job(
                self._parse_excel_data, response, date
            )

        except Exception as err:
            _LOGGER.error(f"Error fetching data for {date.date()}: {err}")
            return None

    def _download_file(self, url: str) -> Optional[bytes]:
        """Download Excel file."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except requests.RequestException as err:
            _LOGGER.error(f"Error downloading file: {err}")
            return None

    def _parse_excel_data(self, file_content: bytes, date: datetime) -> Dict[str, Any]:
        """Parse Excel data from TGE RDN file."""
        try:
            # Wczytaj Excel z bytes
            excel_file = pd.ExcelFile(file_content)
            df = pd.read_excel(excel_file, sheet_name="WYNIKI", header=None)

            # Parsuj dane godzinowe
            hourly_data = []
            time_column = 8  # Kolumna I
            price_column = 10  # Kolumna K

            for index, row in df.iterrows():
                time_value = row[time_column]
                price_value = row[price_column]

                if pd.notna(time_value) and isinstance(time_value, str):
                    # Format: "01-10-25_H01"
                    if re.match(r'\d{2}-\d{2}-\d{2}_H\d{2}', str(time_value)):
                        if pd.notna(price_value) and isinstance(price_value, (int, float)) and price_value > 0:
                            hour = int(time_value.split('_H')[1])

                            # Utwórz datetime dla konkretnej godziny
                            hour_datetime = date.replace(
                                hour=hour-1,  # TGE używa 1-24, Python 0-23
                                minute=0,
                                second=0,
                                microsecond=0
                            )

                            hourly_data.append({
                                'time': hour_datetime.isoformat(),
                                'hour': hour,
                                'price': float(price_value)
                            })

            # Sortuj według godziny
            hourly_data.sort(key=lambda x: x['hour'])

            # Oblicz średnią
            prices = [item['price'] for item in hourly_data]
            average_price = sum(prices) / len(prices) if prices else 0

            return {
                "date": date.date().isoformat(),
                "hourly_data": hourly_data,
                "average_price": average_price,
                "min_price": min(prices) if prices else 0,
                "max_price": max(prices) if prices else 0,
                "total_hours": len(hourly_data)
            }

        except Exception as err:
            _LOGGER.error(f"Error parsing Excel data: {err}")
            raise


class TGERDNSensor(CoordinatorEntity, SensorEntity):
    """TGE RDN sensor."""

    def __init__(self, coordinator: TGERDNDataUpdateCoordinator, entry: ConfigEntry, sensor_type: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_type = sensor_type
        self._attr_name = f"{DEFAULT_NAME} {sensor_type.replace('_', ' ').title()}"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{sensor_type}"

        # Konfiguracja z entry
        self._unit = entry.options.get(CONF_UNIT, DEFAULT_UNIT)
        self._template_str = entry.options.get(CONF_TEMPLATE, DEFAULT_TEMPLATE)

        if self._template_str != DEFAULT_TEMPLATE:
            self._template = Template(self._template_str, self.hass)
        else:
            self._template = None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return REQUIRED_LIBRARIES_AVAILABLE and super().available

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self._unit

    @property
    def state(self) -> Optional[float]:
        """Return the state of the sensor."""
        if not REQUIRED_LIBRARIES_AVAILABLE:
            return None

        if not self.coordinator.data:
            return None

        try:
            value = self._calculate_value()

            if value is None:
                return None

            # Konwersja jednostek
            converted_value = self._convert_units(value)

            # Zastosuj template jeśli jest ustawiony
            if self._template:
                try:
                    result = self._template.async_render(value=converted_value)
                    return float(result)
                except Exception as err:
                    _LOGGER.error(f"Error applying template: {err}")
                    return converted_value

            return converted_value

        except Exception as err:
            _LOGGER.error(f"Error calculating sensor value: {err}")
            return None

    def _calculate_value(self) -> Optional[float]:
        """Calculate sensor value based on type."""
        data = self.coordinator.data
        now = datetime.now()

        if self._sensor_type == "current_price":
            return self._get_current_price(data, now)

        elif self._sensor_type == "next_hour_price":
            return self._get_next_hour_price(data, now)

        elif self._sensor_type == "daily_average":
            return self._get_daily_average(data, now)

        return None

    def _get_current_price(self, data: Dict[str, Any], now: datetime) -> Optional[float]:
        """Get current hour price."""
        today_data = data.get("today")
        if not today_data or not today_data.get("hourly_data"):
            return None

        current_hour = now.hour + 1  # TGE używa 1-24

        for item in today_data["hourly_data"]:
            if item["hour"] == current_hour:
                return item["price"]

        return None

    def _get_next_hour_price(self, data: Dict[str, Any], now: datetime) -> Optional[float]:
        """Get next hour price."""
        next_hour = now.hour + 2  # Następna godzina w systemie TGE

        # Jeśli następna godzina to jutro
        if next_hour > 24:
            tomorrow_data = data.get("tomorrow")
            if not tomorrow_data or not tomorrow_data.get("hourly_data"):
                return None

            for item in tomorrow_data["hourly_data"]:
                if item["hour"] == next_hour - 24:
                    return item["price"]
        else:
            today_data = data.get("today")
            if not today_data or not today_data.get("hourly_data"):
                return None

            for item in today_data["hourly_data"]:
                if item["hour"] == next_hour:
                    return item["price"]

        return None

    def _get_daily_average(self, data: Dict[str, Any], now: datetime) -> Optional[float]:
        """Get daily average price."""
        today_data = data.get("today")
        if not today_data:
            return None

        return today_data.get("average_price")

    def _convert_units(self, value: float) -> float:
        """Convert price units."""
        # Domyślnie dane są w PLN/MWh
        if self._unit == UNIT_PLN_KWH:
            return value / 1000  # MWh na kWh
        elif self._unit == UNIT_EUR_MWH:
            # Tutaj powinien być kurs EUR/PLN - dla uproszczenia używam 4.3
            return value / 4.3
        elif self._unit == UNIT_EUR_KWH:
            return value / 4.3 / 1000

        return value  # PLN/MWh - domyślnie

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not REQUIRED_LIBRARIES_AVAILABLE:
            return {"error": "Required libraries not available"}

        if not self.coordinator.data:
            return {}

        data = self.coordinator.data
        today_data = data.get("today")
        tomorrow_data = data.get("tomorrow")

        attributes = {
            "last_update": data.get("last_update"),
            "unit_raw": UNIT_PLN_MWH,
            "unit_converted": self._unit,
            "libraries_status": "available" if REQUIRED_LIBRARIES_AVAILABLE else "missing"
        }

        if today_data:
            attributes.update({
                "today_average": today_data.get("average_price"),
                "today_min": today_data.get("min_price"),
                "today_max": today_data.get("max_price"),
                "today_hours": today_data.get("total_hours"),
                "prices_today": today_data.get("hourly_data", [])
            })

        if tomorrow_data:
            attributes.update({
                "tomorrow_average": tomorrow_data.get("average_price"),
                "tomorrow_min": tomorrow_data.get("min_price"),
                "tomorrow_max": tomorrow_data.get("max_price"),
                "tomorrow_hours": tomorrow_data.get("total_hours"),
                "prices_tomorrow": tomorrow_data.get("hourly_data", [])
            })

        return attributes
