"""TGE RDN sensor platform - WITH GUARANTEED HOURLY UPDATES."""
import logging
import asyncio
import io
import re
from datetime import datetime, timedelta, time, date
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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.event import async_track_time_interval
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

    _LOGGER.info("🚀 TGE RDN Integration starting up...")

    coordinator = TGERDNDataUpdateCoordinator(hass, entry)

    # IMMEDIATE FETCH on startup - try to get both today and tomorrow data
    _LOGGER.info("📡 Performing immediate data fetch on startup (ignoring schedule)...")
    await coordinator.async_config_entry_first_refresh()

    entities = []

    # Current price sensor
    entities.append(TGERDNSensor(coordinator, entry, "current_price"))

    # Next hour price sensor
    entities.append(TGERDNSensor(coordinator, entry, "next_hour_price"))

    # Daily average price sensor
    entities.append(TGERDNSensor(coordinator, entry, "daily_average"))

    async_add_entities(entities, True)

    # Set up hourly update scheduler
    async_track_time_interval(
        hass, 
        coordinator.hourly_update_callback,
        timedelta(minutes=5)  # Check every 5 minutes for hour changes
    )

    # Log startup summary
    if coordinator.data:
        today_available = coordinator.data.get("today") is not None
        tomorrow_available = coordinator.data.get("tomorrow") is not None
        _LOGGER.info(f"✅ TGE RDN Integration ready! Today: {'✅' if today_available else '❌'}, Tomorrow: {'✅' if tomorrow_available else '❌'}")
    else:
        _LOGGER.warning("⚠️ TGE RDN Integration started but no data available yet")

class TGERDNDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching TGE RDN data - WITH GUARANTEED HOURLY UPDATES."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize with hour tracking."""
        self.hass = hass
        self.entry = entry
        self.last_tomorrow_check = None
        self.tomorrow_data_available = False
        self.startup_fetch_completed = False
        self.last_hour_updated = datetime.now().hour
        self.hourly_callback_unsub = None

        # Initial update interval
        update_interval = self._get_update_interval()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    @callback
    async def hourly_update_callback(self, now: datetime) -> None:
        """Called every 5 minutes to check for hour changes."""
        current_hour = now.hour
        current_minute = now.minute

        # Check if we crossed an hour boundary
        if self.last_hour_updated != current_hour:
            _LOGGER.info(f"⏰ Hour boundary detected: {self.last_hour_updated}:XX → {current_hour}:XX - forcing update")
            self.last_hour_updated = current_hour

            # Force immediate update for new hour
            await self.async_request_refresh()

        # Also update at specific aligned times
        elif current_minute in (0, 5) and current_minute != getattr(self, '_last_aligned_minute', None):
            _LOGGER.debug(f"⏰ Aligned time update: {current_hour}:{current_minute:02d}")
            self._last_aligned_minute = current_minute
            await self.async_request_refresh()

    def _get_update_interval(self) -> int:
        """Get update interval based on current time."""
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

        # 14:00-16:00: Tomorrow's data publication window - CHECK FREQUENTLY EVERY DAY
        elif time(14, 0) <= current_time <= time(16, 0):
            _LOGGER.debug("Afternoon window - tomorrow's data publication time (DAILY)")
            return UPDATE_INTERVAL_NEXT_DAY  # 10 minutes

        # 13:30-14:00: Pre-check for tomorrow data EVERY DAY
        elif time(13, 30) <= current_time <= time(14, 0):
            _LOGGER.debug("Pre-tomorrow window - preparing for tomorrow's data (DAILY)")
            return UPDATE_INTERVAL_FREQUENT  # 15 minutes

        # Other hours - normal interval with hour alignment
        else:
            _LOGGER.debug("Normal hours - hour-aligned interval")
            return 1800  # 30 minutes

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh with IMMEDIATE FETCH of both days."""
        _LOGGER.info("🔄 Starting first refresh with immediate fetch...")

        try:
            # Force fetch both days immediately on startup - EVERY DAY
            data = await self._force_fetch_both_days()

            if data:
                self.data = data
                self.startup_fetch_completed = True

                today_status = "✅ Available" if data.get("today") else "❌ Not available"  
                tomorrow_status = "✅ Available" if data.get("tomorrow") else "❌ Not available"
                _LOGGER.info(f"🎯 Immediate fetch complete: Today {today_status}, Tomorrow {tomorrow_status}")
            else:
                _LOGGER.warning("⚠️ Immediate fetch returned no data")

        except Exception as err:
            _LOGGER.error(f"❌ Error during immediate fetch: {err}")
            # Don't fail completely, continue with normal operation

        # Continue with normal first refresh
        await super().async_config_entry_first_refresh()

    async def _force_fetch_both_days(self) -> Dict[str, Any]:
        """Force fetch both today and tomorrow data immediately."""
        now = datetime.now()
        _LOGGER.info(f"🚀 FORCE FETCH: Getting both today and tomorrow data (TGE publishes DAILY including {now.strftime('%A')})")

        try:
            # Always try to fetch today's data
            _LOGGER.info(f"📡 FORCE FETCH: Getting today's data ({now.date()})...")
            today_data = await self._fetch_day_data(now, "today")

            # Always try to fetch tomorrow's data - TGE PUBLISHES DAILY!
            tomorrow = now + timedelta(days=1)
            _LOGGER.info(f"📡 FORCE FETCH: Getting tomorrow's data ({tomorrow.date()} - {tomorrow.strftime('%A')})...")
            tomorrow_data = await self._fetch_day_data(tomorrow, "tomorrow")

            # Update tomorrow data status
            if tomorrow_data:
                _LOGGER.info(f"🎉 FORCE FETCH: Tomorrow's data ({tomorrow.strftime('%A')}) is available!")
                self.tomorrow_data_available = True
                self.last_tomorrow_check = now
            else:
                _LOGGER.info(f"📅 FORCE FETCH: Tomorrow's data ({tomorrow.strftime('%A')}) not available yet")
                self.tomorrow_data_available = False

            result = {
                "today": today_data,
                "tomorrow": tomorrow_data,
                "last_update": now,
                "startup_fetch": True,
                "tomorrow_data_status": {
                    "available": self.tomorrow_data_available,
                    "last_check": self.last_tomorrow_check,
                    "expected_time": "14:00-15:30 DAILY (including weekends)",
                    "force_fetched": True,
                    "tomorrow_day": tomorrow.strftime('%A')
                }
            }

            return result

        except Exception as err:
            _LOGGER.error(f"❌ FORCE FETCH failed: {err}")
            return {}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from TGE - PRESERVE EXISTING TOMORROW DATA."""
        if not REQUIRED_LIBRARIES_AVAILABLE:
            raise UpdateFailed(f"Required libraries not available: {IMPORT_ERROR}")

        try:
            now = datetime.now()
            update_reason = "scheduled"

            # Check if this is an hour boundary update
            if self.last_hour_updated != now.hour:
                update_reason = f"hour_change ({self.last_hour_updated} → {now.hour})"
                self.last_hour_updated = now.hour

            _LOGGER.info(f"🔄 Regular update cycle at {now.strftime('%H:%M:%S')} on {now.strftime('%A')} ({update_reason})")

            # Always fetch today's data
            _LOGGER.debug("📡 Fetching today's data")
            today_data = await self._fetch_day_data(now, "today")

            # Handle tomorrow data - PRESERVE EXISTING OR FETCH NEW
            tomorrow_data = await self._handle_tomorrow_data(now)

            tomorrow = now + timedelta(days=1)
            result = {
                "today": today_data,
                "tomorrow": tomorrow_data,
                "last_update": now,
                "startup_fetch": False,
                "update_reason": update_reason,
                "tomorrow_data_status": {
                    "available": tomorrow_data is not None,
                    "last_check": self.last_tomorrow_check,
                    "expected_time": "14:00-15:30 DAILY (including weekends)",
                    "force_fetched": False,
                    "tomorrow_day": tomorrow.strftime('%A')
                }
            }

            # Log summary
            today_status = "✅ Available" if today_data else "❌ Not available"
            tomorrow_status = "✅ Available" if tomorrow_data else "❌ Not available"
            _LOGGER.info(f"✅ Regular update complete: Today {today_status}, Tomorrow {tomorrow_status}")

            return result

        except Exception as err:
            _LOGGER.error(f"❌ Error in regular update: {err}")
            raise UpdateFailed(f"Error communicating with TGE API: {err}")

    async def _handle_tomorrow_data(self, now: datetime) -> Optional[Dict[str, Any]]:
        """Handle tomorrow data - preserve existing or fetch new."""

        # Check if we should try to fetch new tomorrow data
        should_fetch_tomorrow = self._should_fetch_tomorrow_data(now)

        if should_fetch_tomorrow:
            # Try to fetch new tomorrow data
            tomorrow = now + timedelta(days=1)
            _LOGGER.info(f"📡 Attempting to fetch tomorrow's data ({tomorrow.date()} - {tomorrow.strftime('%A')}) at {now.strftime('%H:%M:%S')}")

            new_tomorrow_data = await self._fetch_day_data(tomorrow, "tomorrow")

            if new_tomorrow_data:
                if not self.tomorrow_data_available:
                    _LOGGER.info(f"✅ Tomorrow's data ({tomorrow.strftime('%A')}) became available at {now.strftime('%H:%M:%S')}")
                self.tomorrow_data_available = True
                self.last_tomorrow_check = now
                return new_tomorrow_data
            else:
                # Failed to fetch - preserve existing if we have it
                if self.data and self.data.get("tomorrow"):
                    _LOGGER.debug(f"📅 Failed to fetch new tomorrow data, preserving existing")
                    return self.data.get("tomorrow")
                else:
                    if now.hour >= 14:  # Only log if we expect data to be available
                        _LOGGER.info(f"📅 Tomorrow's data ({tomorrow.strftime('%A')}) not yet available at {now.strftime('%H:%M:%S')}")
                    self.tomorrow_data_available = False
                    return None
        else:
            # Not fetching new data - preserve existing if we have it
            if self.data and self.data.get("tomorrow"):
                _LOGGER.debug("📅 Preserving existing tomorrow data (outside fetch window)")
                return self.data.get("tomorrow")
            else:
                _LOGGER.debug("⏭️ Skipping tomorrow's data fetch (outside publication hours)")
                return None

    def _should_fetch_tomorrow_data(self, now: datetime) -> bool:
        """Determine if we should fetch tomorrow's data."""
        current_time = now.time()

        # Before 13:30 - don't fetch (too early)
        if current_time < time(13, 30):
            return False

        # 13:30-18:00 - ACTIVE FETCH WINDOW - always try
        if time(13, 30) <= current_time <= time(18, 0):
            return True

        # 18:00-22:00 - EXTENDED WINDOW - only if we don't have data yet  
        if time(18, 0) < current_time < time(22, 0):
            return not self.tomorrow_data_available

        # After 22:00 - too late, don't fetch
        return False

    async def _fetch_day_data(self, date: datetime, day_type: str) -> Optional[Dict[str, Any]]:
        """Fetch data for specific day."""
        try:
            url = TGE_URL_PATTERN.format(
                year=date.year,
                month=date.month,
                day=date.day
            )

            _LOGGER.debug(f"🌐 Fetching {day_type} data ({date.strftime('%A')}) from URL: {url}")

            response = await self.hass.async_add_executor_job(
                self._download_file, url
            )

            if response is None:
                _LOGGER.debug(f"🚫 No HTTP response for {day_type} ({date.date()} - {date.strftime('%A')})")
                return None

            result = await self.hass.async_add_executor_job(
                self._parse_excel_data, response, date
            )

            if result:
                hours_count = len(result.get("hourly_data", []))
                avg_price = result.get("average_price", 0)
                negative_hours = result.get("negative_hours", 0)

                if negative_hours > 0:
                    _LOGGER.info(f"✅ {day_type.title()} data ({date.strftime('%A')}) loaded: {hours_count} hours, avg {avg_price:.2f} PLN/MWh, ⚠️ {negative_hours} negative price hours")
                else:
                    _LOGGER.info(f"✅ {day_type.title()} data ({date.strftime('%A')}) loaded: {hours_count} hours, avg {avg_price:.2f} PLN/MWh")

            return result

        except DataNotAvailableError as dna:
            _LOGGER.info(f"📅 {day_type.title()} data ({date.strftime('%A')}) not published yet: {dna}")
            return None
        except Exception as err:
            _LOGGER.error(f"❌ Unexpected error fetching {day_type} data ({date.strftime('%A')}): {err}")
            return None

    def _download_file(self, url: str) -> Optional[bytes]:
        """Download Excel file with timeout handling."""
        try:
            _LOGGER.debug(f"🌐 HTTP GET: {url}")
            response = requests.get(url, timeout=30)
            _LOGGER.debug(f"📊 HTTP response: {response.status_code}, {len(response.content)} bytes")
            response.raise_for_status()
            return response.content
        except requests.RequestException as err:
            _LOGGER.debug(f"🚫 HTTP request failed: {err}")
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
            negative_hours = 0
            time_column = 8   # Column I
            price_column = 10 # Column K

            for index, row in df.iterrows():
                time_value = row[time_column] if len(row) > time_column else None
                price_value = row[price_column] if len(row) > price_column else None

                if pd.notna(time_value) and isinstance(time_value, str):
                    # Format: "01-10-25_H01"  
                    if re.match(r'\d{2}-\d{2}-\d{2}_H\d{2}', str(time_value)):
                        # Accept any numeric price value (including negative and zero)
                        if pd.notna(price_value) and isinstance(price_value, (int, float)):
                            hour = int(time_value.split('_H')[1])
                            price = float(price_value)

                            # Track negative prices
                            if price < 0:
                                negative_hours += 1
                                _LOGGER.debug(f"Negative price detected: Hour {hour}, Price {price:.2f} PLN/MWh")

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
                                'price': price,  # Keep original price (including negative and zero)
                                'is_negative': price < 0
                            })

            # Sort by hour
            hourly_data.sort(key=lambda x: x['hour'])

            if not hourly_data:
                raise DataNotAvailableError("Excel file contains no valid price data")

            # Calculate statistics (using original prices including negative)
            prices = [item['price'] for item in hourly_data]
            positive_prices = [p for p in prices if p >= 0]  # For positive-only stats
            average_price = sum(prices) / len(prices) if prices else 0

            return {
                "date": date.date().isoformat(),
                "hourly_data": hourly_data,
                "average_price": average_price,
                "min_price": min(prices) if prices else 0,
                "max_price": max(prices) if prices else 0,
                "total_hours": len(hourly_data),
                "negative_hours": negative_hours,
                "positive_average": sum(positive_prices) / len(positive_prices) if positive_prices else 0,
                "has_negative_prices": negative_hours > 0
            }

        except DataNotAvailableError:
            # Re-raise custom exception to be handled in _fetch_day_data
            raise
        except Exception as err:
            # Real parsing errors (this shouldn't happen with valid Excel files)
            _LOGGER.error(f"❌ Unexpected error parsing Excel data for {date.date()}: {err}")
            raise

class TGERDNSensor(CoordinatorEntity, SensorEntity):
    """TGE RDN sensor with GUARANTEED HOURLY UPDATES & POLISH HOLIDAYS."""

    def __init__(self, coordinator: TGERDNDataUpdateCoordinator, entry: ConfigEntry, sensor_type: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._sensor_type = sensor_type
        self._attr_name = f"{DEFAULT_NAME} {sensor_type.replace('_', ' ').title()}"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{sensor_type}"
        self._last_state_hour = None  # Track when state was last calculated

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

    @property
    def should_poll(self) -> bool:
        """Return if polling is needed - Enable polling for guaranteed updates."""
        return True

    @property
    def state(self) -> Optional[float]:
        """Return the state of the sensor with hour tracking."""
        if not REQUIRED_LIBRARIES_AVAILABLE:
            return None

        if not self.coordinator.data:
            return None

        try:
            current_hour = datetime.now().hour

            # Log hour changes for current price sensor
            if (self._sensor_type == "current_price" and 
                self._last_state_hour is not None and 
                self._last_state_hour != current_hour):
                _LOGGER.info(f"⏰ Current price sensor: Hour changed {self._last_state_hour} → {current_hour}")

            self._last_state_hour = current_hour

            value = self._calculate_value()
            return value

        except Exception as err:
            _LOGGER.error(f"Error calculating sensor value: {err}")
            return None

    def _get_distribution_rate(self, when) -> float:
        """Return distribution rate [PLN/MWh] based on local time, season and POLISH HOLIDAYS."""
        try:
            local = when.astimezone() if hasattr(when, 'astimezone') else when
        except Exception:
            local = when

        month = local.month
        day = local.day
        hour = local.hour  # 0-23
        weekday = local.weekday()  # 0=Monday, 6=Sunday

        # Check if it's weekend (Saturday=5, Sunday=6)
        is_weekend = weekday in (5, 6)

        # Check if it's a Polish national holiday
        is_polish_holiday = self._is_polish_holiday(local.date())

        # Weekend or holiday = lowest rate all day
        if is_weekend or is_polish_holiday:
            if is_polish_holiday:
                _LOGGER.debug(f"🇵🇱 Polish holiday detected: {local.date()} - using lowest distribution rate")
            return self._dist_low

        # Weekday - normal tariff bands
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

    def _is_polish_holiday(self, date) -> bool:
        """Check if date is a Polish national holiday."""
        year = date.year
        month = date.month
        day = date.day

        # Fixed holidays
        fixed_holidays = [
            (1, 1),   # New Year's Day - Nowy Rok
            (1, 6),   # Epiphany - Święto Trzech Króli
            (5, 1),   # May Day - Święto Pracy
            (5, 3),   # Constitution Day - Święto Konstytucji 3 Maja
            (8, 15),  # Assumption Day - Wniebowzięcie NMP
            (11, 1),  # All Saints Day - Wszystkich Świętych
            (11, 11), # Independence Day - Święto Niepodległości
            (12, 25), # Christmas Day - Boże Narodzenie
            (12, 26), # Boxing Day - Drugi Dzień Świąt Bożego Narodzenia
        ]

        if (month, day) in fixed_holidays:
            return True

        # Calculate Easter Sunday for moveable holidays
        easter_date = self._calculate_easter(year)

        # Moveable holidays relative to Easter
        moveable_holidays = [
            easter_date,  # Easter Sunday - Wielkanoc
            easter_date + timedelta(days=1),   # Easter Monday - Poniedziałek Wielkanocny
            easter_date + timedelta(days=49),  # Whit Sunday - Zielone Świątki
            easter_date + timedelta(days=60),  # Corpus Christi - Boże Ciało
        ]

        return date in moveable_holidays

    def _calculate_easter(self, year: int):
        """Calculate Easter Sunday for given year using Gregorian algorithm."""
        # Gregorian calendar Easter calculation
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1

        return date(year, month, day)

    def _compute_total_price(self, base_pln_mwh: float, when, debug_info: bool = False) -> Dict[str, Any]:
        """
        Compute total price with PROSUMER NEGATIVE PRICE HANDLING.

        PROSUMER LOGIC: If TGE price < 0, energy cost = 0, but still pay distribution & fees
        Formula: total_gross = (max(0, cena_TGE) × (1 + VAT)) + exchange_fee + distribution_rate
        """
        dist_rate = self._get_distribution_rate(when)

        # Check if this is weekend/holiday for logging
        is_weekend = when.weekday() in (5, 6)
        is_polish_holiday = self._is_polish_holiday(when.date())

        # PROSUMER NEGATIVE PRICE HANDLING
        is_negative = base_pln_mwh < 0
        effective_energy_price = max(0, base_pln_mwh)  # Negative becomes 0 for prosumers

        # VAT applied only to effective energy price (0 if negative)
        energy_with_vat = float(effective_energy_price) * (1.0 + float(self._vat_rate))

        # Add fees and distribution (always applied, even for negative TGE prices)
        total_gross = energy_with_vat + float(self._exchange_fee) + float(dist_rate)

        if debug_info or is_negative or is_polish_holiday:
            if is_negative:
                _LOGGER.debug(f"Negative price handling: TGE={base_pln_mwh:.2f} → Energy=0, Distribution={dist_rate:.2f}, Total={total_gross:.2f} PLN/MWh")
            if is_polish_holiday:
                _LOGGER.debug(f"🇵🇱 Polish holiday pricing: Distribution={dist_rate:.2f} PLN/MWh (lowest rate)")

        return {
            "total_gross": total_gross,
            "original_tge_price": base_pln_mwh,
            "effective_energy_price": effective_energy_price,
            "is_negative_hour": is_negative,
            "is_weekend": is_weekend,
            "is_polish_holiday": is_polish_holiday,
            "energy_with_vat": energy_with_vat,
            "distribution": dist_rate,
            "exchange_fee": self._exchange_fee,
            "vat_rate": self._vat_rate
        }

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
        """Get current hour price with all fees and VAT - NEGATIVE PRICE HANDLING."""
        today_data = data.get("today")
        if not today_data or not today_data.get("hourly_data"):
            return None

        current_hour = now.hour + 1  # TGE uses 1-24

        for item in today_data["hourly_data"]:
            if item["hour"] == current_hour:
                price_calc = self._compute_total_price(item["price"], now)
                return self._convert_units(price_calc["total_gross"])

        return None

    def _get_total_next_hour_price(self, data: Dict[str, Any], now: datetime) -> Optional[float]:
        """Get next hour price with all fees and VAT - NEGATIVE PRICE HANDLING."""
        next_hour = now.hour + 2  # Next hour in TGE system

        # If next hour is tomorrow
        if next_hour > 24:
            tomorrow_data = data.get("tomorrow")
            if not tomorrow_data or not tomorrow_data.get("hourly_data"):
                return None

            next_day_time = now + timedelta(hours=1)
            for item in tomorrow_data["hourly_data"]:
                if item["hour"] == next_hour - 24:
                    price_calc = self._compute_total_price(item["price"], next_day_time)
                    return self._convert_units(price_calc["total_gross"])
        else:
            today_data = data.get("today")
            if not today_data or not today_data.get("hourly_data"):
                return None

            next_hour_time = now + timedelta(hours=1)
            for item in today_data["hourly_data"]:
                if item["hour"] == next_hour:
                    price_calc = self._compute_total_price(item["price"], next_hour_time)
                    return self._convert_units(price_calc["total_gross"])

        return None

    def _get_total_daily_average(self, data: Dict[str, Any], now: datetime) -> Optional[float]:
        """Get daily average price with all fees and VAT - NEGATIVE PRICE HANDLING."""
        today_data = data.get("today")
        if not today_data:
            return None

        # Calculate average of gross prices for all hours (with negative price handling)
        total_prices = []
        for item in today_data.get('hourly_data', []):
            # Construct datetime for specific hour
            hour_dt = now.replace(
                hour=(item['hour']-1) % 24, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            price_calc = self._compute_total_price(item['price'], hour_dt)
            total_prices.append(price_calc["total_gross"])

        if not total_prices:
            return None

        average_total = sum(total_prices) / len(total_prices)
        return self._convert_units(average_total)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes - WITH GUARANTEED HOURLY UPDATES INFO."""
        if not REQUIRED_LIBRARIES_AVAILABLE:
            return {"error": "Required libraries not available"}

        if not self.coordinator.data:
            return {}

        # Calculations for current hour
        now = datetime.now()
        base_price = None
        current_price_calc = None
        today_data = self.coordinator.data.get("today")

        # Check today and tomorrow for holidays/weekends
        today_is_weekend = now.weekday() in (5, 6)
        today_is_holiday = self._is_polish_holiday(now.date())

        tomorrow = now + timedelta(days=1)
        tomorrow_is_weekend = tomorrow.weekday() in (5, 6)
        tomorrow_is_holiday = self._is_polish_holiday(tomorrow.date())

        if today_data and today_data.get("hourly_data"):
            current_hour = now.hour + 1
            for item in today_data["hourly_data"]:
                if item["hour"] == current_hour:
                    base_price = item["price"]
                    current_price_calc = self._compute_total_price(item["price"], now, debug_info=True)
                    break

        data = self.coordinator.data
        tomorrow_data = data.get("tomorrow")
        tomorrow_status = data.get("tomorrow_data_status", {})
        startup_fetch = data.get("startup_fetch", False)
        update_reason = data.get("update_reason", "unknown")

        # Check for negative prices in today/tomorrow data
        today_negative_info = {}
        tomorrow_negative_info = {}

        if today_data:
            today_negative_info = {
                "has_negative_prices": today_data.get("has_negative_prices", False),
                "negative_hours": today_data.get("negative_hours", 0),
                "total_hours": today_data.get("total_hours", 0),
                "positive_average": today_data.get("positive_average", 0)
            }

        if tomorrow_data:
            tomorrow_negative_info = {
                "has_negative_prices": tomorrow_data.get("has_negative_prices", False),
                "negative_hours": tomorrow_data.get("negative_hours", 0),
                "total_hours": tomorrow_data.get("total_hours", 0),
                "positive_average": tomorrow_data.get("positive_average", 0)
            }

        attributes = {
            "last_update": data.get("last_update"),
            "last_update_reason": update_reason,
            "unit_raw": UNIT_PLN_MWH,
            "unit_converted": self._unit,
            "libraries_status": "available" if REQUIRED_LIBRARIES_AVAILABLE else "missing",
            "pricing_formula": "max(0, TGE_price) × (1 + VAT) + exchange_fee + distribution_rate",
            "negative_price_handling": "Prosumer: negative TGE price → 0 energy cost, still pay distribution",
            "polish_holidays_support": "Weekends and Polish holidays use lowest distribution rate 24h",
            "hourly_updates": "Guaranteed updates at hour boundaries (XX:00) for current price",
            "startup_immediate_fetch": startup_fetch,
            "tge_publishes_daily": "TGE publishes data EVERY DAY including weekends",
            "data_status": {
                "today_available": today_data is not None,
                "tomorrow_available": tomorrow_data is not None,
                "today_hours": len(today_data.get("hourly_data", [])) if today_data else 0,
                "tomorrow_hours": len(tomorrow_data.get("hourly_data", [])) if tomorrow_data else 0,
                "tomorrow_expected_time": tomorrow_status.get("expected_time", "14:00-15:30 DAILY (including weekends)"),
                "tomorrow_last_check": tomorrow_status.get("last_check"),
                "tomorrow_force_fetched": tomorrow_status.get("force_fetched", False),
                "tomorrow_day": tomorrow_status.get("tomorrow_day", "Unknown"),
                "today_negative": today_negative_info,
                "tomorrow_negative": tomorrow_negative_info,
                "today_is_weekend": today_is_weekend,
                "today_is_polish_holiday": today_is_holiday,
                "tomorrow_is_weekend": tomorrow_is_weekend,
                "tomorrow_is_polish_holiday": tomorrow_is_holiday,
                "current_hour": now.hour,
                "last_state_hour": self._last_state_hour,
            },
            "current_hour_components": current_price_calc if current_price_calc else {
                "error": "Current hour data not available"
            }
        }

        if today_data:
            # Calculate gross prices for all hours today WITH NEGATIVE PRICE HANDLING & HOLIDAYS
            prices_today_gross = []
            for item in today_data.get("hourly_data", []):
                # Construct datetime for hour
                hour_dt = now.replace(
                    hour=(item['hour']-1) % 24, 
                    minute=0, 
                    second=0, 
                    microsecond=0
                )
                price_calc = self._compute_total_price(item['price'], hour_dt)
                gross_price_converted = self._convert_units(price_calc["total_gross"])

                prices_today_gross.append({
                    'time': item['time'],
                    'hour': item['hour'],
                    'price_tge_original': item['price'],  # Original TGE (can be negative)
                    'price_energy_effective': price_calc["effective_energy_price"],  # Energy price used (0 if negative)
                    'is_negative_hour': price_calc["is_negative_hour"],
                    'is_weekend': price_calc["is_weekend"],
                    'is_polish_holiday': price_calc["is_polish_holiday"],
                    'price_gross': gross_price_converted,
                    'price_gross_pln_mwh': price_calc["total_gross"],
                    'components': {
                        'energy_with_vat': price_calc["energy_with_vat"],
                        'exchange_fee': price_calc["exchange_fee"],
                        'distribution': price_calc["distribution"]
                    }
                })

            # Calculate gross statistics for today
            gross_prices = [p['price_gross'] for p in prices_today_gross]

            attributes.update({
                "today_average": today_data.get("average_price"),
                "today_min": today_data.get("min_price"),
                "today_max": today_data.get("max_price"),
                "today_hours": today_data.get("total_hours"),
                "prices_today": today_data.get("hourly_data", []),  # Original TGE prices
                "prices_today_gross": prices_today_gross,  # Prosumer gross prices with holidays handling
                "today_average_gross": sum(gross_prices) / len(gross_prices) if gross_prices else None,
                "today_min_gross": min(gross_prices) if gross_prices else None,
                "today_max_gross": max(gross_prices) if gross_prices else None,
            })

        if tomorrow_data:
            # Calculate gross prices for all hours tomorrow WITH NEGATIVE PRICE HANDLING & HOLIDAYS
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
                price_calc = self._compute_total_price(item['price'], hour_dt)
                gross_price_converted = self._convert_units(price_calc["total_gross"])

                prices_tomorrow_gross.append({
                    'time': item['time'],
                    'hour': item['hour'],
                    'price_tge_original': item['price'],  # Original TGE (can be negative)
                    'price_energy_effective': price_calc["effective_energy_price"],  # Energy price used (0 if negative)
                    'is_negative_hour': price_calc["is_negative_hour"],
                    'is_weekend': price_calc["is_weekend"],
                    'is_polish_holiday': price_calc["is_polish_holiday"],
                    'price_gross': gross_price_converted,
                    'price_gross_pln_mwh': price_calc["total_gross"],
                    'components': {
                        'energy_with_vat': price_calc["energy_with_vat"],
                        'exchange_fee': price_calc["exchange_fee"],
                        'distribution': price_calc["distribution"]
                    }
                })

            # Calculate gross statistics for tomorrow
            gross_prices_tomorrow = [p['price_gross'] for p in prices_tomorrow_gross]

            attributes.update({
                "tomorrow_average": tomorrow_data.get("average_price"),
                "tomorrow_min": tomorrow_data.get("min_price"),
                "tomorrow_max": tomorrow_data.get("max_price"),
                "tomorrow_hours": tomorrow_data.get("total_hours"),
                "prices_tomorrow": tomorrow_data.get("hourly_data", []),  # Original TGE prices
                "prices_tomorrow_gross": prices_tomorrow_gross,  # Prosumer gross prices with holidays handling
                "tomorrow_average_gross": sum(gross_prices_tomorrow) / len(gross_prices_tomorrow) if gross_prices_tomorrow else None,
                "tomorrow_min_gross": min(gross_prices_tomorrow) if gross_prices_tomorrow else None,
                "tomorrow_max_gross": max(gross_prices_tomorrow) if gross_prices_tomorrow else None,
            })

        return attributes
