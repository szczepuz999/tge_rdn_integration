"""TGE RDN sensor platform - v1.7.1 PARSE TGE PAGE FOR LINKS."""
import logging, io, re
from datetime import datetime, timedelta, time, date
from typing import Dict, List, Optional, Any

try:
    import pandas as pd
    import requests
    import openpyxl
    from bs4 import BeautifulSoup
    LIBS_OK = True
except ImportError as e:
    LIBS_OK = False
    IMPORT_ERR = str(e)

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_time_interval
from .const import *

_LOGGER = logging.getLogger(__name__)

class DataNotAvailableError(Exception):
    pass

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    if not LIBS_OK:
        _LOGGER.error(f"Missing libraries: {IMPORT_ERR}")
        raise Exception(f"Missing libraries: {IMPORT_ERR}")

    _LOGGER.info("🚀 TGE RDN Integration v1.7.1 starting...")
    _LOGGER.info(f"📄 Parsing page: {TGE_PAGE_URL}")

    coord = TGERDNCoordinator(hass, entry)
    await coord.async_config_entry_first_refresh()

    entities = [
        TGERDNSensor(coord, entry, "current_price"),
        TGERDNSensor(coord, entry, "next_hour_price"),
        TGERDNSensor(coord, entry, "daily_average"),
    ]

    async_add_entities(entities, True)
    async_track_time_interval(hass, coord.hourly_callback, timedelta(minutes=5))

    if coord.data:
        today_ok = coord.data.get("today") is not None
        tomorrow_ok = coord.data.get("tomorrow") is not None
        _LOGGER.info(f"✅ TGE RDN v1.7.1 ready! Today: {'✅' if today_ok else '❌'}, Tomorrow: {'✅' if tomorrow_ok else '❌'}")

class TGERDNCoordinator(DataUpdateCoordinator):
    """Coordinator - PARSES TGE PAGE for Excel file links."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self.tomorrow_available = False
        self.last_tomorrow_check = None
        self.last_hour = datetime.now().hour

        super().__init__(
            hass, _LOGGER, name=DOMAIN,
            update_interval=timedelta(seconds=self._get_interval())
        )

    @callback
    async def hourly_callback(self, now: datetime):
        if self.last_hour != now.hour:
            _LOGGER.info(f"⏰ Hour boundary: {self.last_hour}:XX → {now.hour}:XX")
            self.last_hour = now.hour
            await self.async_request_refresh()

    def _get_interval(self) -> int:
        t = datetime.now().time()
        if time(0,5) <= t <= time(1,0):
            return UPDATE_INTERVAL_CURRENT
        elif time(11,0) <= t <= time(12,0):
            return UPDATE_INTERVAL_FREQUENT
        elif time(12,0) <= t <= time(16,0):
            return UPDATE_INTERVAL_NEXT_DAY
        else:
            return 1800

    def _find_excel_url_for_date(self, target_date: datetime) -> Optional[str]:
        """
        Parse TGE page (https://tge.pl/RDN_instrumenty_15) to find Excel file.

        Looks for links containing:
        - "Raport_RDN_dzie_dostawy_delivery_day"
        - Target date in format YYYY_MM_DD (e.g., 2025_10_17)
        - Ending with .xlsx

        Handles variations: _2, ost, _final, etc.
        """
        try:
            date_str = target_date.strftime("%Y_%m_%d")  # e.g., 2025_10_17

            _LOGGER.debug(f"🔍 Parsing TGE page for date: {date_str}")

            # Get TGE page
            response = requests.get(TGE_PAGE_URL, timeout=30)

            if response.status_code != 200:
                _LOGGER.warning(f"Failed to access TGE page: HTTP {response.status_code}")
                return None

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            all_links = soup.find_all('a', href=True)

            _LOGGER.debug(f"📝 Found {len(all_links)} total links on page")

            # Find matching Excel files
            found_urls = []
            for link in all_links:
                href = link['href']

                # Must end with .xlsx
                if not href.endswith('.xlsx'):
                    continue

                # Must contain the date
                if date_str not in href:
                    continue

                # Must be RDN report
                if 'Raport_RDN_dzie_dostawy_delivery_day' not in href:
                    continue

                # Build complete URL
                if href.startswith('http'):
                    url = href
                else:
                    # Handle relative URLs
                    if href.startswith('/'):
                        url = 'https://tge.pl' + href
                    else:
                        url = 'https://tge.pl/' + href

                found_urls.append(url)

            if found_urls:
                # Log ALL found URLs with details
                _LOGGER.info(f"✅ Found {len(found_urls)} file(s) for {target_date.date()}:")
                for url in found_urls:
                    filename = url.split('/')[-1]
                    _LOGGER.info(f"   📄 Filename: {filename}")
                    _LOGGER.info(f"   🔗 Full URL: {url}")

                # Return first one (usually the correct one)
                selected_url = found_urls[0]
                _LOGGER.info(f"👉 Selected URL: {selected_url}")
                return selected_url
            else:
                _LOGGER.debug(f"📅 No Excel file found for {target_date.date()}")
                return None

        except Exception as e:
            _LOGGER.error(f"❌ Error parsing TGE page: {e}")
            return None

    async def async_config_entry_first_refresh(self):
        """First refresh - immediate fetch."""
        try:
            now = datetime.now()
            _LOGGER.info(f"📡 Initial fetch for {now.date()} and {(now + timedelta(days=1)).date()}")

            today_data = await self._fetch(now, "today")
            tomorrow_data = await self._fetch(now + timedelta(days=1), "tomorrow")

            if tomorrow_data:
                self.tomorrow_available = True
                self.last_tomorrow_check = now

            self.data = {
                "today": today_data,
                "tomorrow": tomorrow_data,
                "last_update": now,
            }
        except Exception as e:
            _LOGGER.error(f"❌ Initial fetch error: {e}")

        await super().async_config_entry_first_refresh()

    async def _async_update_data(self) -> Dict[str, Any]:
        """Regular update cycle."""
        if not LIBS_OK:
            raise UpdateFailed(f"Libraries unavailable: {IMPORT_ERR}")

        try:
            now = datetime.now()

            today_data = await self._fetch(now, "today")
            tomorrow_data = await self._fetch_tomorrow(now)

            return {
                "today": today_data,
                "tomorrow": tomorrow_data,
                "last_update": now,
            }
        except Exception as e:
            _LOGGER.error(f"❌ Update error: {e}")
            raise UpdateFailed(str(e))

    async def _fetch_tomorrow(self, now: datetime) -> Optional[Dict[str, Any]]:
        """Fetch tomorrow with preservation."""
        t = now.time()

        should_fetch = time(12,0) <= t <= time(16,0) or (
            time(16,0) < t < time(22,0) and not self.tomorrow_available
        )

        if should_fetch:
            tomorrow = now + timedelta(days=1)
            data = await self._fetch(tomorrow, "tomorrow")

            if data:
                if not self.tomorrow_available:
                    _LOGGER.info(f"🎉 Tomorrow data ({tomorrow.date()}) now available!")
                self.tomorrow_available = True
                self.last_tomorrow_check = now
                return data
            elif self.data and self.data.get("tomorrow"):
                _LOGGER.debug("📅 Preserving existing tomorrow data")
                return self.data.get("tomorrow")
            else:
                if t.hour >= 12:
                    _LOGGER.info(f"📅 Tomorrow data ({tomorrow.date()}) not yet available")
                return None
        elif self.data and self.data.get("tomorrow"):
            return self.data.get("tomorrow")

        return None

    async def _fetch(self, target_date: datetime, day_type: str) -> Optional[Dict[str, Any]]:
        """Fetch data for specific date."""
        try:
            # Find URL by parsing TGE page
            url = await self.hass.async_add_executor_job(
                self._find_excel_url_for_date, target_date
            )

            if not url:
                _LOGGER.debug(f"🚫 No file found for {day_type} ({target_date.date()})")
                return None

            # Download file
            _LOGGER.debug(f"📥 Downloading {day_type} data...")
            content = await self.hass.async_add_executor_job(
                self._download_file, url
            )

            if not content:
                return None

            # Parse Excel
            result = await self.hass.async_add_executor_job(
                self._parse_excel, content, target_date
            )

            if result:
                hours = len(result.get('hourly_data', []))
                avg = result.get('average_price', 0)
                neg = result.get('negative_hours', 0)

                if neg > 0:
                    _LOGGER.info(f"✅ {day_type.title()} ({target_date.date()}): {hours}h, avg {avg:.2f} PLN/MWh, ⚠️ {neg} negative")
                else:
                    _LOGGER.info(f"✅ {day_type.title()} ({target_date.date()}): {hours}h, avg {avg:.2f} PLN/MWh")

            return result

        except DataNotAvailableError:
            return None
        except Exception as e:
            _LOGGER.error(f"❌ Error fetching {day_type} ({target_date.date()}): {e}")
            return None

    def _download_file(self, url: str) -> Optional[bytes]:
        """Download file from URL."""
        try:
            response = requests.get(url, timeout=30)

            if response.status_code == 200 and len(response.content) > 100:
                _LOGGER.debug(f"✅ Downloaded {len(response.content):,} bytes")
                return response.content
            else:
                _LOGGER.warning(f"❌ Download failed: HTTP {response.status_code}")
                return None
        except requests.RequestException as e:
            _LOGGER.error(f"❌ Download error: {e}")
            return None

    def _parse_excel(self, content: bytes, target_date: datetime) -> Dict[str, Any]:
        """Parse Excel file."""
        if len(content) < 100 or not content.startswith(b'PK'):
            raise DataNotAvailableError("Invalid file format")

        df = pd.read_excel(io.BytesIO(content), sheet_name="WYNIKI", header=None, engine="openpyxl")

        hourly = []
        negative_count = 0

        for _, row in df.iterrows():
            time_val = row[8] if len(row) > 8 else None
            price_val = row[10] if len(row) > 10 else None

            if pd.notna(time_val) and isinstance(time_val, str):
                if re.match(r'\d{2}-\d{2}-\d{2}_H\d{2}', str(time_val)):
                    if pd.notna(price_val) and isinstance(price_val, (int, float)):
                        hour = int(time_val.split('_H')[1])
                        price = float(price_val)

                        if price < 0:
                            negative_count += 1

                        hour_dt = target_date.replace(hour=hour-1, minute=0, second=0, microsecond=0)

                        hourly.append({
                            'time': hour_dt.isoformat(),
                            'hour': hour,
                            'price': price,
                            'is_negative': price < 0
                        })

        hourly.sort(key=lambda x: x['hour'])

        if not hourly:
            raise DataNotAvailableError("No valid hourly data")

        prices = [x['price'] for x in hourly]

        return {
            "date": target_date.date().isoformat(),
            "hourly_data": hourly,
            "average_price": sum(prices) / len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "total_hours": len(hourly),
            "negative_hours": negative_count,
        }


class TGERDNSensor(CoordinatorEntity, SensorEntity):
    """TGE RDN sensor - all features from v1.5.1 preserved."""

    def __init__(self, coord, entry: ConfigEntry, stype: str):
        super().__init__(coord)
        self._coord = coord
        self._entry = entry
        self._stype = stype
        self._attr_name = f"{DEFAULT_NAME} {stype.replace('_', ' ').title()}"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{stype}"
        self._last_hour = None

        self._unit = entry.options.get(CONF_UNIT, DEFAULT_UNIT)
        self._fee = entry.options.get(CONF_EXCHANGE_FEE, DEFAULT_EXCHANGE_FEE)
        self._vat = entry.options.get(CONF_VAT_RATE, DEFAULT_VAT_RATE)
        self._dl = entry.options.get(CONF_DIST_LOW, DEFAULT_DIST_LOW)
        self._dm = entry.options.get(CONF_DIST_MED, DEFAULT_DIST_MED)
        self._dh = entry.options.get(CONF_DIST_HIGH, DEFAULT_DIST_HIGH)

    @property
    def available(self) -> bool:
        return LIBS_OK and super().available

    @property
    def native_unit_of_measurement(self) -> str:
        return self._unit

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def state(self) -> Optional[float]:
        if not LIBS_OK or not self.coordinator.data:
            return None
        try:
            h = datetime.now().hour
            if self._stype == "current_price" and self._last_hour and self._last_hour != h:
                _LOGGER.info(f"⏰ Current price sensor: {self._last_hour}:XX → {h}:XX")
            self._last_hour = h
            return self._calc()
        except Exception as e:
            _LOGGER.error(f"Error calculating value: {e}")
            return None

    def _get_dist(self, when) -> float:
        """Distribution rate with Polish holidays."""
        try:
            local = when.astimezone() if hasattr(when, 'astimezone') else when
        except:
            local = when

        m, h, wd = local.month, local.hour, local.weekday()

        if wd in (5,6) or self._is_holiday(local.date()):
            return self._dl

        summer = m in (4,5,6,7,8,9)
        if summer:
            if 7 <= h < 13: return self._dm
            elif 19 <= h < 22: return self._dh
            else: return self._dl
        else:
            if 7 <= h < 13: return self._dm
            elif 16 <= h < 21: return self._dh
            else: return self._dl

    def _is_holiday(self, d: date) -> bool:
        """Polish holidays."""
        fixed = [(1,1),(1,6),(5,1),(5,3),(8,15),(11,1),(11,11),(12,25),(12,26)]
        if (d.month, d.day) in fixed:
            return True

        easter = self._easter(d.year)
        moveable = [easter, easter+timedelta(1), easter+timedelta(49), easter+timedelta(60)]
        return d in moveable

    def _easter(self, y: int) -> date:
        """Easter calculation."""
        a=y%19; b=y//100; c=y%100; d=b//4; e=b%4
        f=(b+8)//25; g=(b-f+1)//3; h=(19*a+b-d-g+15)%30
        i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7
        m=(a+11*h+22*l)//451; mon=(h+l-7*m+114)//31
        day=((h+l-7*m+114)%31)+1
        return date(y, mon, day)

    def _total_price(self, base: float, when) -> Dict[str, Any]:
        """Total price with prosumer logic."""
        dist = self._get_dist(when)
        eff = max(0, base)
        ewv = float(eff) * (1.0 + float(self._vat))
        tot = ewv + float(self._fee) + float(dist)
        return {"total": tot, "orig": base, "eff": eff, "neg": base<0, "dist": dist}

    def _conv(self, val: float) -> float:
        """Unit conversion."""
        if self._unit == UNIT_PLN_KWH: return val / 1000
        elif self._unit == UNIT_EUR_MWH: return val / 4.3
        elif self._unit == UNIT_EUR_KWH: return val / 4.3 / 1000
        return val

    def _calc(self) -> Optional[float]:
        d = self.coordinator.data
        n = datetime.now()

        if self._stype == "current_price":
            return self._curr(d, n)
        elif self._stype == "next_hour_price":
            return self._next(d, n)
        elif self._stype == "daily_average":
            return self._avg(d, n)
        return None

    def _curr(self, d, n) -> Optional[float]:
        td = d.get("today")
        if not td or not td.get("hourly_data"):
            return None
        h = n.hour + 1
        for x in td["hourly_data"]:
            if x["hour"] == h:
                c = self._total_price(x["price"], n)
                return self._conv(c["total"])
        return None

    def _next(self, d, n) -> Optional[float]:
        nh = n.hour + 2
        if nh > 24:
            tm = d.get("tomorrow")
            if not tm: return None
            nt = n + timedelta(hours=1)
            for x in tm.get("hourly_data", []):
                if x["hour"] == nh - 24:
                    c = self._total_price(x["price"], nt)
                    return self._conv(c["total"])
        else:
            td = d.get("today")
            if not td: return None
            nt = n + timedelta(hours=1)
            for x in td.get("hourly_data", []):
                if x["hour"] == nh:
                    c = self._total_price(x["price"], nt)
                    return self._conv(c["total"])
        return None

    def _avg(self, d, n) -> Optional[float]:
        td = d.get("today")
        if not td: return None

        tots = []
        for x in td.get('hourly_data', []):
            hdt = n.replace(hour=(x['hour']-1)%24, minute=0, second=0, microsecond=0)
            c = self._total_price(x['price'], hdt)
            tots.append(c["total"])

        if not tots: return None
        return self._conv(sum(tots) / len(tots))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if not LIBS_OK or not self.coordinator.data:
            return {}

        return {
            "page_parsing": "Parses TGE page to find Excel file links",
            "last_update": self.coordinator.data.get("last_update"),
            "unit": self._unit,
            "version": "1.7.1",
            "source_page": TGE_PAGE_URL,
        }
