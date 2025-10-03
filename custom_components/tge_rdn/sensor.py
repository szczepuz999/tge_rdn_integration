"""TGE RDN sensor platform - IMPROVED TOMORROW DATA FETCHING."""
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
    DEFAULT_UNIT,
    UPDATE_INTERVAL_CURRENT,
    UPDATE_INTERVAL_NEXT_DAY,
    UPDATE_INTERVAL_FREQUENT,
    UPDATE_INTERVAL_NORMAL,
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

class DataNotAvailableError(Exception):
    """Custom exception for when TGE data is not yet available."""
    pass

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
    """Class to manage fetching TGE RDN data with IMPROVED TIMING."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self.entry = entry
        self.last_tomorrow_check = None
        self.tomorrow_data_available = False

        # Determine update interval based on time
        update_interval = self._get_update_interval()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    def _get_update_interval(self) -> int:
        """Get update interval based on current time - IMPROVED LOGIC."""
        now = datetime.now()
        current_time = now.time()

        _LOGGER.debug(f"Determining update interval for time: {current_time}")

        # 00:05-01:00: Quick checks for today's data  
        if time(0, 5) <= current_time <= time(1, 0):
            _LOGGER.debug("Early morning window - checking today's data frequently")
            return UPDATE_INTERVAL_CURRENT  # 5 minutes

        # 11:00-12:00: Today's data should be published, check frequently
        elif time(11, 0) <= current_time <= time(12, 0):
            _LOGGER.debug("Morning window - today's data publication time")
            return UPDATE_INTERVAL_FREQUENT  # 15 minutes

        # 14:00-16:00: Tomorrow's data publication window - CHECK FREQUENTLY
        elif time(14, 0) <= current_time <= time(16, 0):
            _LOGGER.debug("Afternoon window - tomorrow's data publication time")
            return UPDATE_INTERVAL_NEXT_DAY  # 10 minutes

        # 13:30-14:00: Pre-check for tomorrow data
        elif time(13, 30) <= current_time <= time(14, 0):
            _LOGGER.debug("Pre-tomorrow window - preparing for tomorrow's data")
            return UPDATE_INTERVAL_FREQUENT  # 15 minutes

        # Other hours - normal interval
        else:
            _LOGGER.debug("Normal hours - standard interval")
            return UPDATE_INTERVAL_NORMAL  # 1 hour

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from TGE with IMPROVED TOMORROW DATA LOGIC."""
        if not REQUIRED_LIBRARIES_AVAILABLE:
            raise UpdateFailed(f"Required libraries not available: {IMPORT_ERROR}")

        try:
            now = datetime.now()
            _LOGGER.info(f"Starting TGE data update at {now.strftime('%H:%M:%S')}")

            # Always fetch today's data
            _LOGGER.debug("Fetching today's data")
            today_data = await self._fetch_day_data(now, "today")

            # Determine if we should fetch tomorrow's data
            should_fetch_tomorrow = self._should_fetch_tomorrow_data(now)

            tomorrow_data = None
            if should_fetch_tomorrow:
                tomorrow = now + timedelta(days=1)
                _LOGGER.info(f"Attempting to fetch tomorrow's data ({tomorrow.date()}) at {now.strftime('%H:%M:%S')}")
                tomorrow_data = await self._fetch_day_data(tomorrow, "tomorrow")

                # Update tomorrow data status
                if tomorrow_data:
                    if not self.tomorrow_data_available:
                        _LOGGER.info(f"✅ Tomorrow's data became available at {now.strftime('%H:%M:%S')}")
                    self.tomorrow_data_available = True
                    self.last_tomorrow_check = now
                else:
                    if now.hour >= 14:  # Only log if we expect data to be available
                        _LOGGER.info(f"Tomorrow's data not yet available at {now.strftime('%H:%M:%S')}")
                    self.tomorrow_data_available = False
            else:
                _LOGGER.debug("Skipping tomorrow's data fetch (outside publication hours)")

            result = {
                "today": today_data,
                "tomorrow": tomorrow_data,
                "last_update": now,
                "tomorrow_data_status": {
                    "available": self.tomorrow_data_available,
                    "last_check": self.last_tomorrow_check,
                    "expected_time": "14:00-15:30"
                }
            }

            # Log summary
            today_status = "✅ Available" if today_data else "❌ Not available"
            tomorrow_status = "✅ Available" if tomorrow_data else "❌ Not available"
            _LOGGER.info(f"Data update complete: Today {today_status}, Tomorrow {tomorrow_status}")

            return result

        except Exception as err:
            _LOGGER.error(f"Error in data update: {err}")
            raise UpdateFailed(f"Error communicating with TGE API: {err}")

    def _should_fetch_tomorrow_data(self, now: datetime) -> bool:
        """Determine if we should fetch tomorrow's data based on time and status."""
        current_time = now.time()

        # Before 13:30 - don't check (too early)
        if current_time < time(13, 30):
            return False

        # After 18:00 - only if we don't have data yet
        if current_time > time(18, 0):
            return not self.tomorrow_data_available

        # 13:30-18:00 - always check during publication window
        return True

    async def _fetch_day_data(self, date: datetime, day_type: str) -> Optional[Dict[str, Any]]:
        """Fetch data for specific day with enhanced logging."""
        try:
            url = TGE_URL_PATTERN.format(
                year=date.year,
                month=date.month,
                day=date.day
            )

            _LOGGER.debug(f"Fetching {day_type} data from URL: {url}")

            response = await self.hass.async_add_executor_job(
                self._download_file, url
            )

            if response is None:
                _LOGGER.debug(f"No HTTP response for {day_type} ({date.date()})")
                return None

            result = await self.hass.async_add_executor_job(
                self._parse_excel_data, response, date
            )

            if result:
                hours_count = len(result.get("hourly_data", []))
                avg_price = result.get("average_price", 0)
                _LOGGER.info(f"✅ {day_type.title()} data loaded: {hours_count} hours, avg {avg_price:.2f} PLN/MWh")

            return result

        except DataNotAvailableError as dna:
            # This is expected when TGE hasn't published data yet
            if day_type == "tomorrow":
                _LOGGER.debug(f"Tomorrow's TGE data not yet published: {dna}")
            else:
                _LOGGER.info(f"TGE data not yet available for {day_type}: {dna}")
            return None
        except Exception as err:
            _LOGGER.error(f"Unexpected error fetching {day_type} data: {err}")
            return None

    def _download_file(self, url: str) -> Optional[bytes]:
        """Download Excel file with timeout handling."""
        try:
            _LOGGER.debug(f"HTTP GET: {url}")
            response = requests.get(url, timeout=30)
            _LOGGER.debug(f"HTTP response: {response.status_code}, {len(response.content)} bytes")
            response.raise_for_status()
            return response.content
        except requests.RequestException as err:
            _LOGGER.debug(f"HTTP request failed: {err}")
            return None

    def _parse_excel_data(self, file_content: bytes, date: datetime) -> Dict[str, Any]:
        """Parse Excel data from TGE RDN file with proper validation."""

        def validate_excel_file(content: bytes) -> None:
            """Validate if content is a valid Excel file."""
            if len(content) < 100:
                raise DataNotAvailableError(f"File too small ({len(content)} bytes)")

            # Check for HTML content (various ways)
            content_lower = content[:1000].lower()
            html_indicators = [b'<html', b'<!doctype', b'<head>', b'<body>', b'<title>', b'<meta', b'<div', b'<p>']
            for indicator in html_indicators:
                if indicator in content_lower:
                    raise DataNotAvailableError(f"Server returned HTML instead of Excel (contains {indicator.decode()})")

            # Check for ZIP signature (Excel files are ZIP archives)
            if not content.startswith(b'PK'):
                raise DataNotAvailableError(f"File doesn't have Excel format (starts with: {content[:10]})")

            # Check for error indicators
            error_indicators = [b'404', b'not found', b'error', b'exception', b'access denied', b'forbidden']
            for indicator in error_indicators:
                if indicator in content_lower:
                    raise DataNotAvailableError(f"Server returned error page (contains '{indicator.decode()}')")

        try:
            # Validate file before processing
            validate_excel_file(file_content)

            # Use BytesIO and specify engine
            excel_file = io.BytesIO(file_content)
            df = pd.read_excel(excel_file, sheet_name="WYNIKI", header=None, engine="openpyxl")

            # Parse hourly data
            hourly_data = []
            time_column = 8   # Column I
            price_column = 10 # Column K

            for index, row in df.iterrows():
                time_value = row[time_column] if len(row) > time_column else None
                price_value = row[price_column] if len(row) > price_column else None

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

            if not hourly_data:
                raise DataNotAvailableError("Excel file contains no valid price data")

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

        except DataNotAvailableError:
            # Re-raise custom exception to be handled in _fetch_day_data
            raise
        except Exception as err:
            # Real parsing errors (this shouldn't happen with valid Excel files)
            _LOGGER.error(f"Unexpected error parsing Excel data for {date.date()}: {err}")
            raise

class TGERDNSensor(CoordinatorEntity, SensorEntity):
    """TGE RDN sensor without template functionality."""

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

        # Fees/tariffs and VAT (PLN/MWh)
        self._exchange_fee = entry.options.get(CONF_EXCHANGE_FEE, DEFAULT_EXCHANGE_FEE)
        self._vat_rate = entry.options.get(CONF_VAT_RATE, DEFAULT_VAT_RATE)
        self._dist_low = entry.options.get(CONF_DIST_LOW, DEFAULT_DIST_LOW)
        self._dist_med = entry.options.get(CONF_DIST_MED, DEFAULT_DIST_MED)
        self._dist_high = entry.options.get(CONF_DIST_HIGH, DEFAULT_DIST_HIGH)

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
        """Return extra state attributes with ENHANCED TOMORROW INFO."""
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
        tomorrow_status = data.get("tomorrow_data_status", {})

        attributes = {
            "last_update": data.get("last_update"),
            "unit_raw": UNIT_PLN_MWH,
            "unit_converted": self._unit,
            "libraries_status": "available" if REQUIRED_LIBRARIES_AVAILABLE else "missing",
            "pricing_formula": "(TGE_price × (1 + VAT)) + exchange_fee + distribution_rate",
            "data_status": {
                "today_available": today_data is not None,
                "tomorrow_available": tomorrow_data is not None,
                "today_hours": len(today_data.get("hourly_data", [])) if today_data else 0,
                "tomorrow_hours": len(tomorrow_data.get("hourly_data", [])) if tomorrow_data else 0,
                "tomorrow_expected_time": tomorrow_status.get("expected_time", "14:00-15:30"),
                "tomorrow_last_check": tomorrow_status.get("last_check"),
            },
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
