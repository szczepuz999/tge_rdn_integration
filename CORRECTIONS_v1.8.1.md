# TGE RDN Integration v1.8.1 - Corrections Applied ✅

## Date: November 21, 2025

---

## Issues Fixed

### Issue 1: Incorrect Date in URL ❌ → ✅
**Problem:** The integration was fetching data from the base URL without date specification, which always showed tomorrow's data.

**Solution:** Added date parameter to URL with correct logic:
- URL shows prices for **next day** after the dateShow parameter
- To get data for date X, request `?dateShow=X-1` (previous day)
- Example: For Nov 21 data → request `?dateShow=20-11-2025`

**Code Change:**
```python
# Before (v1.8.0)
response = requests.get(TGE_PAGE_URL, timeout=30, headers={...})

# After (v1.8.1)
previous_day = target_date - timedelta(days=1)
date_param = previous_day.strftime("%d-%m-%Y")
url_with_date = f"{TGE_PAGE_URL}?dateShow={date_param}"
response = requests.get(url_with_date, timeout=30, headers={...})
```

### Issue 2: Missing is_working_day Attribute ❌ → ✅
**Problem:** No way to determine if current day is a normal working day.

**Solution:** Added `is_working_day` attribute to `sensor.tge_rdn_current_price`:
- Returns `true` for normal working days (Mon-Fri, not holidays)
- Returns `false` for weekends (Sat-Sun) or Polish national holidays

**Code Change:**
```python
# New method added
def _is_working_day(self) -> bool:
    """Check if today is a normal working day (not weekend or holiday)."""
    today = datetime.now().date()
    if today.weekday() in (5, 6):  # Weekend
        return False
    if self._is_holiday(today):  # Polish holiday
        return False
    return True

# Added to attributes
attrs = {
    "version": "1.8.1",
    "source": TGE_PAGE_URL,
    "dst_support": True,
    "last_update": data.get("last_update"),
    "unit": self._unit,
    "is_working_day": self._is_working_day(),  # NEW
}
```

---

## Files Modified

1. ✅ `custom_components/tge_rdn/sensor.py`
   - Fixed URL construction with date parameter
   - Added `_is_working_day()` method
   - Added `is_working_day` to attributes
   - Updated version to 1.8.1

2. ✅ `custom_components/tge_rdn/__init__.py`
   - Updated version to 1.8.1

3. ✅ `custom_components/tge_rdn/manifest.json`
   - Updated version to 1.8.1

---

## Testing Results ✅

### Test 1: Today's Data (Nov 21, 2025)
```
URL: https://tge.pl/energia-elektryczna-rdn?dateShow=20-11-2025
✅ Successfully fetched 24 hours of data
   Average: 628.67 PLN/MWh
   Min: 383.08 PLN/MWh
   Max: 1069.67 PLN/MWh
   
First 3 hours:
   H01: 432.72 PLN/MWh
   H02: 399.56 PLN/MWh
   H03: 383.08 PLN/MWh
```

### Test 2: Tomorrow's Data (Nov 22, 2025)
```
URL: https://tge.pl/energia-elektryczna-rdn?dateShow=21-11-2025
✅ Successfully fetched 24 hours of data
   Average: 593.32 PLN/MWh
   Min: 460.00 PLN/MWh
   Max: 998.36 PLN/MWh
```

### Test 3: Working Day Detection
```
Date: 2025-11-21 (Friday)
Weekend: False
Holiday: False
✅ is_working_day: True
```

---

## How the Date Parameter Works

The TGE website shows prices for the **next day** after the `dateShow` parameter:

| What you want | URL parameter needed |
|---------------|---------------------|
| Nov 20 data   | `?dateShow=19-11-2025` |
| Nov 21 data   | `?dateShow=20-11-2025` |
| Nov 22 data   | `?dateShow=21-11-2025` |

**Pattern:** To get data for day X, request `dateShow=X-1` (previous day)

This is handled automatically in the code:
```python
previous_day = target_date - timedelta(days=1)
date_param = previous_day.strftime("%d-%m-%Y")
url_with_date = f"{TGE_PAGE_URL}?dateShow={date_param}"
```

---

## New Attribute: is_working_day

Available on `sensor.tge_rdn_current_price`:

```yaml
sensor.tge_rdn_current_price:
  state: 0.7234
  attributes:
    version: "1.8.1"
    source: "https://tge.pl/energia-elektryczna-rdn"
    is_working_day: true  # ← NEW!
    unit: "PLN/kWh"
    today:
      date: "2025-11-21"
      hours: 24
      average: 628.67
```

### Usage in Automations

```yaml
# Example: Different tariff on working days vs weekends
automation:
  - alias: "Energy tariff based on day type"
    trigger:
      platform: time_pattern
      hours: "*"
    condition:
      - condition: template
        value_template: >
          {{ state_attr('sensor.tge_rdn_current_price', 'is_working_day') }}
    action:
      # Apply working day tariff
      - service: notify.mobile_app
        data:
          message: "Working day - higher distribution rates apply"
```

---

## Polish Holidays Detected

The integration automatically detects these Polish national holidays:

**Fixed holidays:**
- January 1 - New Year
- January 6 - Epiphany
- May 1 - Labour Day
- May 3 - Constitution Day
- August 15 - Assumption
- November 1 - All Saints
- November 11 - Independence Day
- December 25 - Christmas
- December 26 - Second Day of Christmas

**Moveable holidays (based on Easter):**
- Easter Sunday
- Easter Monday
- Corpus Christi (60 days after Easter)
- Pentecost (49 days after Easter)

---

## Version History

### v1.8.1 (November 21, 2025)
- ✅ Fixed URL to use date-specific parameter
- ✅ Added `is_working_day` attribute
- ✅ Corrected today/tomorrow data fetching

### v1.8.0 (November 21, 2025)
- ✅ Changed from Excel files to HTML table parsing
- ✅ Removed pandas and openpyxl dependencies
- ✅ Lighter and faster integration

### v1.7.4 (Previous)
- Excel file download and parsing
- DST support

---

## Summary

**Status:** ✅ **All Issues Fixed and Tested**

**Changes:**
1. ✅ Fixed date parameter in URL (request next day to get current day data)
2. ✅ Added `is_working_day` attribute for working day detection
3. ✅ Updated version to 1.8.1

**Testing:**
- ✅ Today's data (Nov 21) fetches correctly
- ✅ Working day detection works correctly
- ✅ No code errors

**User Impact:**
- Users will now get correct today/tomorrow data
- New attribute available for automations
- No configuration changes needed

---

**Version:** 1.8.1  
**Ready for deployment:** ✅ YES
