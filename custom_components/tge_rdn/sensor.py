"""TGE RDN sensor - v1.6.1 COMPLETE."""
import logging, io, re
from datetime import datetime, timedelta, time, date
from typing import Dict, List, Optional, Any

try:
    import pandas as pd
    import requests
    import openpyxl
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
        raise Exception(f"Missing libraries: {IMPORT_ERR}")
    _LOGGER.info("🚀 TGE RDN starting...")
    coord = TGERDNCoordinator(hass, entry)
    await coord.async_config_entry_first_refresh()
    async_add_entities([
        TGERDNSensor(coord, entry, "current_price"),
        TGERDNSensor(coord, entry, "next_hour_price"),
        TGERDNSensor(coord, entry, "daily_average"),
    ], True)
    async_track_time_interval(hass, coord.hourly_callback, timedelta(minutes=5))

class TGERDNCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self.tomorrow_available = False
        self.last_hour = datetime.now().hour
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=self._get_interval()))

    @callback
    async def hourly_callback(self, now):
        if self.last_hour != now.hour:
            _LOGGER.info(f"⏰ Hour {self.last_hour} → {now.hour}")
            self.last_hour = now.hour
            await self.async_request_refresh()

    def _get_interval(self):
        t = datetime.now().time()
        if time(0,5) <= t <= time(1,0): return 300
        elif time(11,0) <= t <= time(12,0): return 900
        elif time(12,0) <= t <= time(16,0): return 600
        else: return 1800

    def _gen_urls(self, dt):
        y,m,d = dt.year, dt.month, dt.day
        b = f"https://tge.pl/pub/TGE/A_SDAC%20{y}/RDN/Raport_RDN_dzie_dostawy_delivery_day_{y}_{m:02d}_{d:02d}"
        return [f"{b}.xlsx", f"{b}_2.xlsx", f"{b}_3.xlsx", f"{b}_4.xlsx", 
                f"{b}ost.xlsx", f"{b}_ost.xlsx", f"{b}_final.xlsx", f"{b}_v2.xlsx", f"{b}_v3.xlsx"]

    async def async_config_entry_first_refresh(self):
        try:
            now = datetime.now()
            today_data = await self._fetch(now, "today")
            tomorrow_data = await self._fetch(now + timedelta(days=1), "tomorrow")
            self.data = {"today": today_data, "tomorrow": tomorrow_data, "last_update": now}
        except Exception as e:
            _LOGGER.error(f"Fetch error: {e}")
        await super().async_config_entry_first_refresh()

    async def _async_update_data(self):
        if not LIBS_OK:
            raise UpdateFailed(f"Libs: {IMPORT_ERR}")
        try:
            now = datetime.now()
            today = await self._fetch(now, "today")
            tomorrow = await self._fetch_tomorrow(now)
            return {"today": today, "tomorrow": tomorrow, "last_update": now}
        except Exception as e:
            raise UpdateFailed(str(e))

    async def _fetch_tomorrow(self, now):
        t = now.time()
        should = time(12,0) <= t <= time(16,0) or (time(16,0) < t < time(22,0) and not self.tomorrow_available)
        if should:
            data = await self._fetch(now + timedelta(days=1), "tomorrow")
            if data:
                self.tomorrow_available = True
                return data
            elif self.data and self.data.get("tomorrow"):
                return self.data.get("tomorrow")
        elif self.data and self.data.get("tomorrow"):
            return self.data.get("tomorrow")
        return None

    async def _fetch(self, dt, typ):
        try:
            content = await self.hass.async_add_executor_job(self._download, dt)
            if not content:
                return None
            result = await self.hass.async_add_executor_job(self._parse, content, dt)
            if result:
                _LOGGER.info(f"✅ {typ} loaded: {len(result.get('hourly_data',[]))}h")
            return result
        except DataNotAvailableError:
            return None
        except Exception as e:
            _LOGGER.error(f"Error {typ}: {e}")
            return None

    def _download(self, dt):
        urls = self._gen_urls(dt)
        for i, url in enumerate(urls, 1):
            try:
                r = requests.get(url, timeout=30)
                if r.status_code == 200 and len(r.content) > 100:
                    _LOGGER.info(f"✅ Found at attempt {i}/9: {url.split('/')[-1]}")
                    return r.content
            except:
                continue
        _LOGGER.warning(f"⚠️ All 9 attempts failed for {dt.date()}")
        return None

    def _parse(self, content, dt):
        if len(content) < 100 or not content.startswith(b'PK'):
            raise DataNotAvailableError("Invalid")
        df = pd.read_excel(io.BytesIO(content), sheet_name="WYNIKI", header=None, engine="openpyxl")
        hourly = []
        for _, row in df.iterrows():
            tv = row[8] if len(row) > 8 else None
            pv = row[10] if len(row) > 10 else None
            if pd.notna(tv) and isinstance(tv, str) and re.match(r'\d{2}-\d{2}-\d{2}_H\d{2}', str(tv)):
                if pd.notna(pv) and isinstance(pv, (int, float)):
                    h = int(tv.split('_H')[1])
                    p = float(pv)
                    hdt = dt.replace(hour=h-1, minute=0, second=0, microsecond=0)
                    hourly.append({'time': hdt.isoformat(), 'hour': h, 'price': p, 'is_negative': p < 0})
        hourly.sort(key=lambda x: x['hour'])
        if not hourly:
            raise DataNotAvailableError("No data")
        prices = [x['price'] for x in hourly]
        return {
            "date": dt.date().isoformat(),
            "hourly_data": hourly,
            "average_price": sum(prices) / len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "total_hours": len(hourly),
            "negative_hours": sum(1 for p in prices if p < 0),
        }

class TGERDNSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coord, entry, stype):
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
    def available(self):
        return LIBS_OK and super().available

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def should_poll(self):
        return True

    @property
    def state(self):
        if not LIBS_OK or not self.coordinator.data:
            return None
        try:
            h = datetime.now().hour
            if self._stype == "current_price" and self._last_hour and self._last_hour != h:
                _LOGGER.info(f"⏰ Price: {self._last_hour} → {h}")
            self._last_hour = h
            return self._calc()
        except:
            return None

    def _get_dist(self, when):
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

    def _is_holiday(self, d):
        fixed = [(1,1),(1,6),(5,1),(5,3),(8,15),(11,1),(11,11),(12,25),(12,26)]
        if (d.month, d.day) in fixed:
            return True
        e = self._easter(d.year)
        return d in [e, e+timedelta(1), e+timedelta(49), e+timedelta(60)]

    def _easter(self, y):
        a = y % 19
        b = y // 100
        c = y % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19*a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2*e + 2*i - h - k) % 7
        m = (a + 11*h + 22*l) // 451
        mon = (h + l - 7*m + 114) // 31
        day = ((h + l - 7*m + 114) % 31) + 1
        return date(y, mon, day)

    def _total_price(self, base, when):
        dist = self._get_dist(when)
        eff = max(0, base)
        ewv = float(eff) * (1.0 + float(self._vat))
        tot = ewv + float(self._fee) + float(dist)
        return {"total_gross": tot, "orig": base, "eff": eff, "neg": base < 0, "dist": dist}

    def _conv(self, val):
        if self._unit == UNIT_PLN_KWH: return val / 1000
        elif self._unit == UNIT_EUR_MWH: return val / 4.3
        elif self._unit == UNIT_EUR_KWH: return val / 4.3 / 1000
        return val

    def _calc(self):
        d = self.coordinator.data
        n = datetime.now()
        if self._stype == "current_price":
            return self._curr(d, n)
        elif self._stype == "next_hour_price":
            return self._next(d, n)
        elif self._stype == "daily_average":
            return self._avg(d, n)
        return None

    def _curr(self, d, n):
        td = d.get("today")
        if not td or not td.get("hourly_data"):
            return None
        h = n.hour + 1
        for x in td["hourly_data"]:
            if x["hour"] == h:
                c = self._total_price(x["price"], n)
                return self._conv(c["total_gross"])
        return None

    def _next(self, d, n):
        nh = n.hour + 2
        if nh > 24:
            tm = d.get("tomorrow")
            if not tm:
                return None
            nt = n + timedelta(hours=1)
            for x in tm.get("hourly_data", []):
                if x["hour"] == nh - 24:
                    c = self._total_price(x["price"], nt)
                    return self._conv(c["total_gross"])
        else:
            td = d.get("today")
            if not td:
                return None
            nt = n + timedelta(hours=1)
            for x in td.get("hourly_data", []):
                if x["hour"] == nh:
                    c = self._total_price(x["price"], nt)
                    return self._conv(c["total_gross"])
        return None

    def _avg(self, d, n):
        td = d.get("today")
        if not td:
            return None
        tots = []
        for x in td.get('hourly_data', []):
            hdt = n.replace(hour=(x['hour']-1) % 24, minute=0, second=0, microsecond=0)
            c = self._total_price(x['price'], hdt)
            tots.append(c["total_gross"])
        if not tots:
            return None
        return self._conv(sum(tots) / len(tots))

    @property
    def extra_state_attributes(self):
        if not LIBS_OK or not self.coordinator.data:
            return {}
        return {
            "smart_url_finding": "9 variations: _2, ost, _final, etc.",
            "last_update": self.coordinator.data.get("last_update"),
            "unit": self._unit,
            "version": "1.6.1",
        }
