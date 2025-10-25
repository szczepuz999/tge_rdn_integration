"""TGE RDN sensor platform v1.7.4 - DST Support."""
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
    from bs4 import BeautifulSoup
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
    TGE_PAGE_URL,
    UNIT_PLN_MWH,
    UNIT_PLN_KWH,
    UNIT_EUR_MWH,
    UNIT_EUR_KWH,
    CONF_UNIT,
    DEFAULT_UNIT,
    CONF_EXCHANGE_FEE,
    DEFAULT_EXCHANGE_FEE,
    CONF_VAT_RATE,
    DEFAULT_VAT_RATE,
    CONF_DIST_LOW,
    DEFAULT_DIST_LOW,
    CONF_DIST_MED,
    DEFAULT_DIST_MED,
    CONF_DIST_HIGH,
    DEFAULT_DIST_HIGH,
    UPDATE_INTERVAL_CURRENT,
    UPDATE_INTERVAL_NEXT_DAY,
    UPDATE_INTERVAL_FREQUENT,
)

_LOGGER = logging.getLogger(__name__)


class DataNotAvailableError(Exception):
    """Custom exception for missing data."""
    pass


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors from config entry."""

    if not REQUIRED_LIBRARIES_AVAILABLE:
        _LOGGER.error(f"Missing libraries: {IMPORT_ERROR}")
        raise Exception(f"Missing libraries: {IMPORT_ERROR}")

    _LOGGER.info("🚀 TGE RDN v1.7.4 - Starting integration...")
    _LOGGER.info("📄 Source: https://tge.pl/RDN_instrumenty_15")
    _LOGGER.info("✅ DST Change Support Enabled")

    coordinator = TGERDNDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entities = [
        TGERDNSensor(coordinator, entry, "current_price"),
        TGERDNSensor(coordinator, entry, "next_hour_price"),
        TGERDNSensor(coordinator, entry, "daily_average"),
    ]

    async_add_entities(entities, True)
    async_track_time_interval(hass, coordinator.hourly_update_callback, timedelta(minutes=5))

    if coordinator.data:
        today_ok = coordinator.data.get("today") is not None
        tomorrow_ok = coordinator.data.get("tomorrow") is not None
        _LOGGER.info(f"✅ TGE RDN v1.7.4 ready! Today: {'✅' if today_ok else '❌'}, Tomorrow: {'✅' if tomorrow_ok else '❌'}")


class TGERDNDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator for TGE RDN data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.hass = hass
        self.entry = entry
        self.tomorrow_data_available = False
        self.last_tomorrow_check = None
        self.last_hour_updated = datetime.now().hour

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self._get_update_interval()),
        )

    @callback
    async def hourly_update_callback(self, now: datetime) -> None:
        """Check for hour changes."""
        current_hour = now.hour
        if self.last_hour_updated != current_hour:
            _LOGGER.info(f"⏰ Hour boundary: {self.last_hour_updated}:XX → {current_hour}:XX")
            self.last_hour_updated = current_hour
            await self.async_request_refresh()

    def _get_update_interval(self) -> int:
        """Get update interval based on time."""
        now = datetime.now()
        current_time = now.time()

        if time(0, 5) <= current_time <= time(1, 0):
            return UPDATE_INTERVAL_CURRENT
        elif time(11, 0) <= current_time <= time(12, 0):
            return UPDATE_INTERVAL_FREQUENT
        elif time(12, 0) <= current_time <= time(16, 0):
            return UPDATE_INTERVAL_NEXT_DAY
        else:
            return 1800

    def _find_excel_url_for_date(self, target_date: datetime) -> Optional[str]:
        """Parse TGE page to find Excel file - handles ALL variations."""
        try:
            date_str = target_date.strftime("%Y_%m_%d")
            _LOGGER.debug(f"🔍 Parsing TGE page for: {date_str}")

            response = requests.get(TGE_PAGE_URL, timeout=30)
            if response.status_code != 200:
                _LOGGER.warning(f"Failed to access TGE page: HTTP {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            all_links = soup.find_all('a', href=True)
            _LOGGER.debug(f"📝 Found {len(all_links)} links")

            found_urls = []
            for link in all_links:
                href = link['href']
                if not href.endswith('.xlsx'):
                    continue
                if date_str not in href:
                    continue
                if 'Raport_RDN_dzie_dostawy_delivery_day' not in href:
                    continue

                url = href if href.startswith('http') else f"https://tge.pl{href}"
                found_urls.append(url)

            if found_urls:
                _LOGGER.info(f"✅ Found {len(found_urls)} file(s):")
                for url in found_urls:
                    _LOGGER.info(f"   📄 {url.split('/')[-1]}")

                selected = found_urls[0]
                _LOGGER.info(f"👉 Selected: {selected}")
                return selected
            else:
                _LOGGER.debug(f"No file for {target_date.date()}")
                return None
        except Exception as e:
            _LOGGER.error(f"Error parsing TGE page: {e}")
            return None

    async def async_config_entry_first_refresh(self) -> None:
        """First refresh with immediate fetch."""
        try:
            now = datetime.now()
            _LOGGER.info(f"📡 Initial fetch for {now.date()}")

            today_data = await self._fetch_day_data(now, "today")
            tomorrow = now + timedelta(days=1)
            tomorrow_data = await self._fetch_day_data(tomorrow, "tomorrow")

            if tomorrow_data:
                self.tomorrow_data_available = True
                self.last_tomorrow_check = now

            self.data = {
                "today": today_data,
                "tomorrow": tomorrow_data,
                "last_update": now,
            }
        except Exception as err:
            _LOGGER.error(f"Error during initial fetch: {err}")

        await super().async_config_entry_first_refresh()

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from TGE."""
        if not REQUIRED_LIBRARIES_AVAILABLE:
            raise UpdateFailed(f"Libraries not available: {IMPORT_ERROR}")

        try:
            now = datetime.now()
            today_data = await self._fetch_day_data(now, "today")
            tomorrow_data = await self._handle_tomorrow_data(now)

            return {
                "today": today_data,
                "tomorrow": tomorrow_data,
                "last_update": now,
            }
        except Exception as err:
            _LOGGER.error(f"Update error: {err}")
            raise UpdateFailed(str(err))

    async def _handle_tomorrow_data(self, now: datetime) -> Optional[Dict[str, Any]]:
        """Handle tomorrow data with preservation."""
        current_time = now.time()

        should_fetch = (
            time(12, 0) <= current_time <= time(16, 0) or
            (time(16, 0) < current_time < time(22, 0) and not self.tomorrow_data_available)
        )

        if should_fetch:
            tomorrow = now + timedelta(days=1)
            new_data = await self._fetch_day_data(tomorrow, "tomorrow")

            if new_data:
                if not self.tomorrow_data_available:
                    _LOGGER.info(f"🎉 Tomorrow data available!")
                self.tomorrow_data_available = True
                self.last_tomorrow_check = now
                return new_data
            elif self.data and self.data.get("tomorrow"):
                return self.data.get("tomorrow")
            else:
                if current_time.hour >= 12:
                    _LOGGER.info(f"Tomorrow data not yet available")
                return None
        elif self.data and self.data.get("tomorrow"):
            return self.data.get("tomorrow")

        return None

    async def _fetch_day_data(
        self, date: datetime, day_type: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch data for specific date."""
        try:
            url = await self.hass.async_add_executor_job(
                self._find_excel_url_for_date, date
            )

            if not url:
                _LOGGER.debug(f"No file for {day_type} ({date.date()})")
                return None

            _LOGGER.debug(f"📥 Downloading {day_type}...")
            content = await self.hass.async_add_executor_job(
                self._download_file, url
            )

            if not content:
                return None

            result = await self.hass.async_add_executor_job(
                self._parse_excel_data, content, date
            )

            if result:
                hours = len(result.get('hourly_data', []))
                avg = result.get('average_price', 0)
                _LOGGER.info(f"✅ {day_type.title()} ({date.date()}): {hours}h, avg {avg:.2f}")

            return result
        except DataNotAvailableError:
            return None
        except Exception as err:
            _LOGGER.error(f"Error fetching {day_type}: {err}")
            return None

    def _download_file(self, url: str) -> Optional[bytes]:
        """Download file from URL."""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200 and len(response.content) > 100:
                return response.content
            else:
                _LOGGER.warning(f"Download failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            _LOGGER.error(f"Download error: {e}")
            return None

    def _parse_excel_data(self, file_content: bytes, date: datetime) -> Dict[str, Any]:
        """Parse Excel file - HANDLES DST CHANGES."""
        try:
            # Validate file
            if len(file_content) < 100 or not file_content.startswith(b'PK'):
                raise DataNotAvailableError("Invalid Excel file")

            # Read Excel
            excel_file = io.BytesIO(file_content)
            df = pd.read_excel(
                excel_file,
                sheet_name="WYNIKI",
                header=None,
                engine="openpyxl"
            )

            # Parse hourly data
            hourly_data = []
            negative_hours = 0

            for index, row in df.iterrows():
                time_value = row[8] if len(row) > 8 else None
                price_value = row[10] if len(row) > 10 else None

                if pd.notna(time_value) and isinstance(time_value, str):
                    # Match format: 26-10-25_H02 or 26-10-25_H02a (DST!)
                    if re.match(r'\d{2}-\d{2}-\d{2}_H\d{2}[a-z]?', str(time_value)):
                        if pd.notna(price_value) and isinstance(price_value, (int, float)):
                            # Extract hour, handle DST change (e.g., 'H02a')
                            hour_str = time_value.split('_H')[1]
                            # Remove any letters (like 'a' in 'H02a')
                            hour_str_clean = ''.join(c for c in hour_str if c.isdigit())
                            hour = int(hour_str_clean)

                            price = float(price_value)

                            if price < 0:
                                negative_hours += 1

                            hour_datetime = date.replace(
                                hour=hour - 1,
                                minute=0,
                                second=0,
                                microsecond=0
                            )

                            hourly_data.append({
                                'time': hour_datetime.isoformat(),
                                'hour': hour,
                                'price': price,
                                'is_negative': price < 0
                            })

            # Sort by hour
            hourly_data.sort(key=lambda x: x['hour'])

            if not hourly_data:
                raise DataNotAvailableError("No valid price data")

            # Calculate statistics
            prices = [item['price'] for item in hourly_data]

            return {
                "date": date.date().isoformat(),
                "hourly_data": hourly_data,
                "average_price": sum(prices) / len(prices) if prices else 0,
                "min_price": min(prices) if prices else 0,
                "max_price": max(prices) if prices else 0,
                "total_hours": len(hourly_data),
                "negative_hours": negative_hours,
            }

        except DataNotAvailableError:
            raise
        except Exception as err:
            _LOGGER.error(f"Error parsing Excel for {date.date()}: {err}")
            raise


class TGERDNSensor(CoordinatorEntity, SensorEntity):
    """TGE RDN sensor."""

    def __init__(self, coord, entry: ConfigEntry, sensor_type: str) -> None:
        """Initialize sensor."""
        super().__init__(coord)
        self._coord = coord
        self._entry = entry
        self._sensor_type = sensor_type
        self._attr_name = f"{DEFAULT_NAME} {sensor_type.replace('_', ' ').title()}"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{sensor_type}"
        self._last_hour = None

        self._unit = entry.options.get(CONF_UNIT, DEFAULT_UNIT)
        self._fee = entry.options.get(CONF_EXCHANGE_FEE, DEFAULT_EXCHANGE_FEE)
        self._vat = entry.options.get(CONF_VAT_RATE, DEFAULT_VAT_RATE)
        self._dl = entry.options.get(CONF_DIST_LOW, DEFAULT_DIST_LOW)
        self._dm = entry.options.get(CONF_DIST_MED, DEFAULT_DIST_MED)
        self._dh = entry.options.get(CONF_DIST_HIGH, DEFAULT_DIST_HIGH)

    @property
    def available(self) -> bool:
        """Return if available."""
        return REQUIRED_LIBRARIES_AVAILABLE and super().available

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit."""
        return self._unit

    @property
    def state(self) -> Optional[float]:
        """Return state."""
        if not REQUIRED_LIBRARIES_AVAILABLE or not self.coordinator.data:
            return None
        try:
            h = datetime.now().hour
            if self._sensor_type == "current_price" and self._last_hour and self._last_hour != h:
                _LOGGER.info(f"⏰ Current price: {self._last_hour}:XX → {h}:XX")
            self._last_hour = h
            return self._calc()
        except Exception as err:
            _LOGGER.error(f"Error: {err}")
            return None

    def _get_dist(self, when) -> float:
        """Distribution rate."""
        try:
            local = when.astimezone() if hasattr(when, 'astimezone') else when
        except:
            local = when

        m, h, wd = local.month, local.hour, local.weekday()

        if wd in (5, 6) or self._is_holiday(local.date()):
            return self._dl

        summer = m in (4, 5, 6, 7, 8, 9)
        if summer:
            if 7 <= h < 13: return self._dm
            elif 19 <= h < 22: return self._dh
            else: return self._dl
        else:
            if 7 <= h < 13: return self._dm
            elif 16 <= h < 21: return self._dh
            else: return self._dl

    def _is_holiday(self, d: date) -> bool:
        """Check if Polish holiday."""
        fixed = [(1,1),(1,6),(5,1),(5,3),(8,15),(11,1),(11,11),(12,25),(12,26)]
        if (d.month, d.day) in fixed:
            return True

        easter = self._easter(d.year)
        moveable = [easter, easter+timedelta(1), easter+timedelta(49), easter+timedelta(60)]
        return d in moveable

    def _easter(self, y: int) -> date:
        """Calculate Easter."""
        a=y%19; b=y//100; c=y%100; d=b//4; e=b%4
        f=(b+8)//25; g=(b-f+1)//3; h=(19*a+b-d-g+15)%30
        i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7
        m=(a+11*h+22*l)//451; mon=(h+l-7*m+114)//31
        day=((h+l-7*m+114)%31)+1
        return date(y, mon, day)

    def _calc(self) -> Optional[float]:
        """Calculate value."""
        d = self.coordinator.data
        n = datetime.now()

        if self._sensor_type == "current_price":
            td = d.get("today")
            if not td or not td.get("hourly_data"):
                return None
            h = n.hour + 1
            for x in td["hourly_data"]:
                if x["hour"] == h:
                    price = max(0, x["price"])
                    ewv = price * (1 + self._vat)
                    total = ewv + self._fee + self._get_dist(n)
                    if self._unit == "PLN/kWh": return total / 1000
                    elif self._unit == "EUR/MWh": return total / 4.3
                    elif self._unit == "EUR/kWh": return total / 4300
                    return total
            return None

        elif self._sensor_type == "next_hour_price":
            nh = n.hour + 2
            if nh > 24:
                tm = d.get("tomorrow")
                if not tm: return None
                for x in tm.get("hourly_data", []):
                    if x["hour"] == nh - 24:
                        price = max(0, x["price"])
                        ewv = price * (1 + self._vat)
                        total = ewv + self._fee + self._get_dist(n + timedelta(hours=1))
                        if self._unit == "PLN/kWh": return total / 1000
                        elif self._unit == "EUR/MWh": return total / 4.3
                        elif self._unit == "EUR/kWh": return total / 4300
                        return total
            else:
                td = d.get("today")
                if not td: return None
                for x in td.get("hourly_data", []):
                    if x["hour"] == nh:
                        price = max(0, x["price"])
                        ewv = price * (1 + self._vat)
                        total = ewv + self._fee + self._get_dist(n + timedelta(hours=1))
                        if self._unit == "PLN/kWh": return total / 1000
                        elif self._unit == "EUR/MWh": return total / 4.3
                        elif self._unit == "EUR/kWh": return total / 4300
                        return total
            return None

        elif self._sensor_type == "daily_average":
            td = d.get("today")
            if not td: return None
            tots = []
            for x in td.get("hourly_data", []):
                hdt = n.replace(hour=(x["hour"]-1)%24, minute=0, second=0, microsecond=0)
                price = max(0, x["price"])
                ewv = price * (1 + self._vat)
                total = ewv + self._fee + self._get_dist(hdt)
                tots.append(total)
            if not tots: return None
            avg = sum(tots) / len(tots)
            if self._unit == "PLN/kWh": return avg / 1000
            elif self._unit == "EUR/MWh": return avg / 4.3
            elif self._unit == "EUR/kWh": return avg / 4300
            return avg

        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return attributes."""
        if not REQUIRED_LIBRARIES_AVAILABLE or not self.coordinator.data:
            return {}

        data = self.coordinator.data

        attrs = {
            "version": "1.7.4",
            "source": TGE_PAGE_URL,
            "dst_support": True,
            "last_update": data.get("last_update"),
            "unit": self._unit,
        }

        if data.get("today"):
            today = data["today"]
            attrs["today"] = {
                "date": today.get("date"),
                "hours": today.get("total_hours"),
                "average": today.get("average_price"),
            }
            attrs["prices_today_gross"] = []
            for h in today.get("hourly_data", []):
                price_eff = max(0, h["price"])
                ewv = price_eff * (1 + self._vat)
                total = ewv + self._fee + self._get_dist(
                    datetime.fromisoformat(h["time"]) if isinstance(h["time"], str) else h["time"]
                )
                attrs["prices_today_gross"].append({
                    "hour": h["hour"],
                    "time": h["time"],
                    "price_tge": h["price"],
                    "price_gross_pln_mwh": total,
                    "price_gross": total / 1000 if self._unit == "PLN/kWh" else total,
                })

        if data.get("tomorrow"):
            tomorrow = data["tomorrow"]
            attrs["tomorrow"] = {
                "date": tomorrow.get("date"),
                "hours": tomorrow.get("total_hours"),
                "average": tomorrow.get("average_price"),
            }
            attrs["prices_tomorrow_gross"] = []
            for h in tomorrow.get("hourly_data", []):
                price_eff = max(0, h["price"])
                ewv = price_eff * (1 + self._vat)
                total = ewv + self._fee + self._get_dist(
                    datetime.fromisoformat(h["time"]) if isinstance(h["time"], str) else h["time"]
                )
                attrs["prices_tomorrow_gross"].append({
                    "hour": h["hour"],
                    "time": h["time"],
                    "price_tge": h["price"],
                    "price_gross_pln_mwh": total,
                    "price_gross": total / 1000 if self._unit == "PLN/kWh" else total,
                })

        return attrs
