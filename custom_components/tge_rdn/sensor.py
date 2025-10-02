"""TGE RDN sensor platform - All fixes applied."""
import logging
import asyncio
import io
import re
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
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up TGE RDN sensors based on a config entry."""

    # Check if required libraries are available
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

    # Current price sensor
    entities.append(TGERDNSensor(coordinator, entry, "current_price"))

    # Next hour price sensor
    entities.append(TGERDNSensor(coordinator, entry, "next_hour_price"))

    # Daily average price sensor
    entities.append(TGERDNSensor(coordinator, entry, "daily_average"))

    async_add_entities(entities, True)

class TGERDNDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching TGE RDN data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self.entry = entry

        # Determine update interval based on time
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

        # After midnight (00:10) - fetch today's data
        if now.time() >= time(0, 10) and now.time() <= time(0, 30):
            return UPDATE_INTERVAL_CURRENT

        # At 15:00 - fetch tomorrow's data
        elif now.time() >= time(15, 0) and now.time() <= time(15, 30):
            return UPDATE_INTERVAL_NEXT_DAY

        # Other hours - check every hour
        else:
            return 3600

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from TGE."""
        if not REQUIRED_LIBRARIES_AVAILABLE:
            raise UpdateFailed(f"Required libraries not available: {IMPORT_ERROR}")

        try:
            now = datetime.now()

            # Fetch data for today
            today_data = await self._fetch_day_data(now)

            # Fetch data for tomorrow if available
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
        """Parse Excel data from TGE RDN file - FIXED BytesIO and validation."""
        try:
            # FIXED: Check if downloaded file is valid Excel (not HTML error page)
            if len(file_content) < 1000 or file_content.startswith(b'<'):
                _LOGGER.warning(f"Downloaded file for {date.date()} is not a valid Excel file (probably HTML error page)")
                raise ValueError(f"Downloaded file for {date.date()} is not a valid Excel file")

            # FIXED: Use BytesIO and specify engine to avoid deprecation warning
            excel_file = io.BytesIO(file_content)
            df = pd.read_excel(excel_file, sheet_name="WYNIKI", header=None, engine="openpyxl")

            # Parse hourly data
            hourly_data = []
            time_column = 8   # Column I
            price_column = 10 # Column K

            for index, row in df.iterrows():
                time_value = row[time_column]
                price_value = row[price_column]

                if pd.notna(time_value) and isinstance(time_value, str):
                    # Format: "01-10-25_H01"
                    if re.match(r'\d{2}-\d{2}-\d{2}_H\d{2}', str(time_value)):
                        if pd.notna(price_value) and isinstance(price_value, (int, float)) and price_value > 0:
                            hour = int(time_value.split('_H')[1])

                            # Create datetime for specific hour
                            hour_datetime = date.replace(
                                hour=hour-1,  # TGE uses 1-24, Python 0-23
                                minute=0,
                                second=0,
                                microsecond=0
                            )

                            hourly_data.append({
                                'time': hour_datetime.isoformat(),
                                'hour': hour,
                                'price': float(price_value)
                            })

            # Sort by hour
            hourly_data.sort(key=lambda x: x['hour'])

            # Calculate statistics
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
    """TGE RDN sensor - FIXED Template handling."""

    def __init__(self, coordinator: TGERDNDataUpdateCoordinator, entry: ConfigEntry, sensor_type: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._sensor_type = sensor_type
        self._attr_name = f"{DEFAULT_NAME} {sensor_type.replace('_', ' ').title()}"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{sensor_type}"

        # Configuration from entry
        self._unit = entry.options.get(CONF_UNIT, DEFAULT_UNIT)
        self._template_str = entry.options.get(CONF_TEMPLATE, DEFAULT_TEMPLATE)

        # Fees/tariffs and VAT (PLN/MWh)
        self._exchange_fee = entry.options.get(CONF_EXCHANGE_FEE, DEFAULT_EXCHANGE_FEE)
        self._vat_rate = entry.options.get(CONF_VAT_RATE, DEFAULT_VAT_RATE)
        self._dist_low = entry.options.get(CONF_DIST_LOW, DEFAULT_DIST_LOW)
        self._dist_med = entry.options.get(CONF_DIST_MED, DEFAULT_DIST_MED)
        self._dist_high = entry.options.get(CONF_DIST_HIGH, DEFAULT_DIST_HIGH)

        # FIXED: Template creation with proper hass reference
        self._template = None
        if self._template_str != DEFAULT_TEMPLATE:
            try:
                self._template = Template(self._template_str, coordinator.hass)
            except Exception as err:
                _LOGGER.error(f"Error creating template '{self._template_str}': {err}")
                self._template = None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return REQUIRED_LIBRARIES_AVAILABLE and super().available

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self._unit

    def _get_distribution_rate(self, when) -> float:
        """Return distribution rate [PLN/MWh] based on local time and season."""
        try:
            local = when.astimezone() if hasattr(when, 'astimezone') else when
        except Exception:
            local = when

        month = local.month
        hour = local.hour  # 0-23

        # Determine season: summer (April-September) vs winter (October-March)
        is_summer = month in (4, 5, 6, 7, 8, 9)

        # Map hours to tariff bands
        if is_summer:
            # Summer: morning peak (7-13), evening peak (19-22), off-peak (13-19 and 22-7)
            if 7 <= hour < 13:
                return self._dist_med  # morning peak
            elif 19 <= hour < 22:
                return self._dist_high  # evening peak
            else:
                return self._dist_low  # off-peak hours
        else:
            # Winter: morning peak (7-13), evening peak (16-21), off-peak (13-16 and 21-7)
            if 7 <= hour < 13:
                return self._dist_med  # morning peak
            elif 16 <= hour < 21:
                return self._dist_high  # evening peak
            else:
                return self._dist_low  # off-peak hours

    def _compute_total_price(self, base_pln_mwh: float, when) -> float:
        """
        Compute total price using formula: 
        total_gross = (cena_TGE × (1 + VAT)) + exchange_fee + distribution_rate
        """
        dist_rate = self._get_distribution_rate(when)

        # VAT applied only to TGE price
        tge_with_vat = float(base_pln_mwh) * (1.0 + float(self._vat_rate))

        # Add fees without VAT
        total_gross = tge_with_vat + float(self._exchange_fee) + float(dist_rate)

        return total_gross

    def _convert_units(self, value: float) -> float:
        """Convert price units."""
        # Input value already in PLN/MWh gross
        if self._unit == UNIT_PLN_KWH:
            return value / 1000  # MWh to kWh
        elif self._unit == UNIT_EUR_MWH:
            # EUR/PLN rate - simplified to 4.3
            return value / 4.3
        elif self._unit == UNIT_EUR_KWH:
            return value / 4.3 / 1000

        return value  # PLN/MWh - default

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

            # FIXED: Template application with proper render method
            if self._template:
                try:
                    template_variables = {
                        'value': value,
                        'now': datetime.now(),
                        'this': self
                    }
                    result = self._template.render(template_variables)
                    return float(result)
                except Exception as err:
                    _LOGGER.error(f"Error applying template '{self._template_str}': {err}")
                    return value

            return value

        except Exception as err:
            _LOGGER.error(f"Error calculating sensor value: {err}")
            return None

    def _calculate_value(self) -> Optional[float]:
        """Calculate sensor value based on type."""
        data = self.coordinator.data
        now = datetime.now()

        if self._sensor_type == "current_price":
            return self._get_total_current_price(data, now)

        elif self._sensor_type == "next_hour_price":
            return self._get_total_next_hour_price(data, now)

        elif self._sensor_type == "daily_average":
            return self._get_total_daily_average(data, now)

        return None

    def _get_total_current_price(self, data: Dict[str, Any], now: datetime) -> Optional[float]:
        """Get current hour price with all fees and VAT."""
        today_data = data.get("today")
        if not today_data or not today_data.get("hourly_data"):
            return None

        current_hour = now.hour + 1  # TGE uses 1-24

        for item in today_data["hourly_data"]:
            if item["hour"] == current_hour:
                total_pln_mwh = self._compute_total_price(item["price"], now)
                return self._convert_units(total_pln_mwh)

        return None

    def _get_total_next_hour_price(self, data: Dict[str, Any], now: datetime) -> Optional[float]:
        """Get next hour price with all fees and VAT."""
        next_hour = now.hour + 2  # Next hour in TGE system

        # If next hour is tomorrow
        if next_hour > 24:
            tomorrow_data = data.get("tomorrow")
            if not tomorrow_data or not tomorrow_data.get("hourly_data"):
                return None

            next_day_time = now + timedelta(hours=1)
            for item in tomorrow_data["hourly_data"]:
                if item["hour"] == next_hour - 24:
                    total_pln_mwh = self._compute_total_price(item["price"], next_day_time)
                    return self._convert_units(total_pln_mwh)
        else:
            today_data = data.get("today")
            if not today_data or not today_data.get("hourly_data"):
                return None

            next_hour_time = now + timedelta(hours=1)
            for item in today_data["hourly_data"]:
                if item["hour"] == next_hour:
                    total_pln_mwh = self._compute_total_price(item["price"], next_hour_time)
                    return self._convert_units(total_pln_mwh)

        return None

    def _get_total_daily_average(self, data: Dict[str, Any], now: datetime) -> Optional[float]:
        """Get daily average price with all fees and VAT."""
        today_data = data.get("today")
        if not today_data:
            return None

        # Calculate average of gross prices for all hours
        total_prices = []
        for item in today_data.get('hourly_data', []):
            # Construct datetime for specific hour
            hour_dt = now.replace(
                hour=(item['hour']-1) % 24, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            total_price = self._compute_total_price(item['price'], hour_dt)
            total_prices.append(total_price)

        if not total_prices:
            return None

        average_total = sum(total_prices) / len(total_prices)
        return self._convert_units(average_total)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not REQUIRED_LIBRARIES_AVAILABLE:
            return {"error": "Required libraries not available"}

        if not self.coordinator.data:
            return {}

        # Calculations for current hour
        now = datetime.now()
        base_price = None
        today_data = self.coordinator.data.get("today")

        if today_data and today_data.get("hourly_data"):
            current_hour = now.hour + 1
            for item in today_data["hourly_data"]:
                if item["hour"] == current_hour:
                    base_price = item["price"]
                    break

        dist_rate = self._get_distribution_rate(now)

        # Calculate price components
        if base_price is not None:
            tge_with_vat = base_price * (1.0 + self._vat_rate)
            total_gross = tge_with_vat + self._exchange_fee + dist_rate
        else:
            tge_with_vat = None
            total_gross = None

        data = self.coordinator.data
        tomorrow_data = data.get("tomorrow")

        attributes = {
            "last_update": data.get("last_update"),
            "unit_raw": UNIT_PLN_MWH,
            "unit_converted": self._unit,
            "libraries_status": "available" if REQUIRED_LIBRARIES_AVAILABLE else "missing",
            "pricing_formula": "(TGE_price × (1 + VAT)) + exchange_fee + distribution_rate",
            "template_status": "active" if self._template else "inactive",
            "template_string": self._template_str if self._template_str != DEFAULT_TEMPLATE else None,
            "components": {
                "base_energy_pln_mwh": base_price,
                "tge_with_vat_pln_mwh": tge_with_vat,
                "exchange_fee_pln_mwh": self._exchange_fee,
                "distribution_pln_mwh": dist_rate,
                "vat_rate": self._vat_rate,
                "total_gross_pln_mwh": total_gross
            }
        }

        if today_data:
            # Calculate gross prices for all hours today
            prices_today_gross = []
            for item in today_data.get("hourly_data", []):
                # Construct datetime for hour
                hour_dt = now.replace(
                    hour=(item['hour']-1) % 24, 
                    minute=0, 
                    second=0, 
                    microsecond=0
                )
                gross_price_pln_mwh = self._compute_total_price(item['price'], hour_dt)
                gross_price_converted = self._convert_units(gross_price_pln_mwh)

                prices_today_gross.append({
                    'time': item['time'],
                    'hour': item['hour'],
                    'price_tge_net': item['price'],
                    'price_gross': gross_price_converted,
                    'price_gross_pln_mwh': gross_price_pln_mwh
                })

            # Calculate gross statistics for today
            gross_prices = [p['price_gross'] for p in prices_today_gross]

            attributes.update({
                "today_average": today_data.get("average_price"),
                "today_min": today_data.get("min_price"),
                "today_max": today_data.get("max_price"),
                "today_hours": today_data.get("total_hours"),
                "prices_today": today_data.get("hourly_data", []),  # Original TGE prices
                "prices_today_gross": prices_today_gross,  # Gross prices with VAT and distribution
                "today_average_gross": sum(gross_prices) / len(gross_prices) if gross_prices else None,
                "today_min_gross": min(gross_prices) if gross_prices else None,
                "today_max_gross": max(gross_prices) if gross_prices else None,
            })

        if tomorrow_data:
            # Calculate gross prices for all hours tomorrow
            prices_tomorrow_gross = []
            tomorrow_date = now + timedelta(days=1)
            for item in tomorrow_data.get("hourly_data", []):
                # Construct datetime for tomorrow's hour
                hour_dt = tomorrow_date.replace(
                    hour=(item['hour']-1) % 24, 
                    minute=0, 
                    second=0, 
                    microsecond=0
                )
                gross_price_pln_mwh = self._compute_total_price(item['price'], hour_dt)
                gross_price_converted = self._convert_units(gross_price_pln_mwh)

                prices_tomorrow_gross.append({
                    'time': item['time'],
                    'hour': item['hour'],
                    'price_tge_net': item['price'],
                    'price_gross': gross_price_converted,
                    'price_gross_pln_mwh': gross_price_pln_mwh
                })

            # Calculate gross statistics for tomorrow
            gross_prices_tomorrow = [p['price_gross'] for p in prices_tomorrow_gross]

            attributes.update({
                "tomorrow_average": tomorrow_data.get("average_price"),
                "tomorrow_min": tomorrow_data.get("min_price"),
                "tomorrow_max": tomorrow_data.get("max_price"),
                "tomorrow_hours": tomorrow_data.get("total_hours"),
                "prices_tomorrow": tomorrow_data.get("hourly_data", []),  # Original TGE prices
                "prices_tomorrow_gross": prices_tomorrow_gross,  # Gross prices with VAT and distribution
                "tomorrow_average_gross": sum(gross_prices_tomorrow) / len(gross_prices_tomorrow) if gross_prices_tomorrow else None,
                "tomorrow_min_gross": min(gross_prices_tomorrow) if gross_prices_tomorrow else None,
                "tomorrow_max_gross": max(gross_prices_tomorrow) if gross_prices_tomorrow else None,
            })

        return attributes
