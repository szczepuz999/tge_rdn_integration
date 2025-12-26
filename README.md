# TGE RDN Integration for Home Assistant

This project is a custom component for Home Assistant that integrates with the Polish energy exchange (TGE RDN) to provide real-time electricity prices. It scrapes the TGE website to fetch the data, calculates prices based on user-defined fees and distribution rates, and exposes them as sensors in Home Assistant.

**Version:** 1.8.6

## Features

*   **Real-time Prices:** Fetches hourly electricity prices from [TGE.pl](https://tge.pl/energia-elektryczna-rdn).
*   **Dynamic Calculations:** Calculates final cost including VAT, exchange fees, and time-based distribution rates (peak/off-peak).
*   **Constant Fees:** Supports fixed monthly fees (transmission, transitional, subscription, capacity, trade).
*   **Localization:** Fully localized in English and Polish (including configuration dialogs and entity names).
*   **Reliable Data:** Uses "Fixing I" prices as the primary source, with fallback to "Fixing II" and weighted averages.
*   **Smart Features:**
    *   **Tomorrow's Prices:** Available from ~12:30 PM.
    *   **Holiday Support:** Automatic detection of Polish national holidays for correct tariff application.
    *   **DST Support:** Correctly handles 23h and 25h days during clock changes.
    *   **Working Day Detection:** Exposes an `is_working_day` attribute for automation logic.

## Installation

The recommended installation method is via [HACS](https://hacs.xyz/).

1.  Open HACS in your Home Assistant instance.
2.  Go to "Integrations" and click "Explore & Download Repositories".
3.  Search for "TGE RDN" and install it.
4.  Restart Home Assistant.

## Configuration

After installation, configure the integration via the UI:

1.  Go to **Settings** -> **Devices & Services**.
2.  Click **Add Integration** and search for **TGE RDN**.
3.  Configure the following parameters:
    *   **Price Unit:** PLN/kWh, PLN/MWh, EUR/kWh, or EUR/MWh.
    *   **Exchange Fee:** Additional fee per MWh (default: 2.0 PLN).
    *   **VAT Rate:** Your applicable VAT rate (default: 0.23 for 23%).
    *   **Distribution Rates:**
        *   **Off-peak:** Night/weekend rate.
        *   **Morning Peak:** Rate for morning peak hours.
        *   **Evening Peak:** Rate for evening peak hours.
    *   **Fixed Monthly Fees:**
        *   Fixed Transmission Fee
        *   Transitional Fee
        *   Subscription Fee
        *   Capacity Fee
        *   Trade Fee

## Entities provided

The integration provides the following sensors:

*   `sensor.tge_rdn_current_price` (Aktualna cena): The total cost for the current hour.
*   `sensor.tge_rdn_next_hour_price` (Cena w następnej godzinie): The total cost for the next hour.
*   `sensor.tge_rdn_daily_average` (Średnia dzienna): The average price for the current day.
*   `sensor.tge_rdn_fixed_transmission_fee` (Stała opłata przesyłowa)
*   `sensor.tge_rdn_transitional_fee` (Opłata przejściowa)
*   `sensor.tge_rdn_subscription_fee` (Opłata abonamentowa)
*   `sensor.tge_rdn_capacity_fee` (Opłata mocowa)
*   `sensor.tge_rdn_trade_fee` (Opłata handlowa)

## Technical Details

*   **Architecture:** Standard Home Assistant custom component using a `DataUpdateCoordinator`.
*   **Dependencies:** `requests`, `beautifulsoup4` (no heavy libraries like pandas).
*   **Data Source:** Parses the HTML table directly from TGE.
*   **Update Interval:**
    *   00:05 - 01:00: Every 5 minutes (to catch late updates).
    *   11:00 - 12:00: Every 15 minutes.
    *   12:00 - 16:00: Every 10 minutes (to fetch tomorrow's prices ASAP).
    *   Otherwise: Every hour.

## Recent Changes

### v1.8.5
*   **Localization:** fixed entity names language

### v1.8.4
*   **Localization:** Added Polish entity names.
*   **Fixed Fees:** Added support for constant monthly fees (transmission, transitional, subscription, capacity, trade).

### v1.8.2
*   **Data Source:** Switched to "Fixing I" as the primary price source for better accuracy.
*   **Attribute:** Added `price_source` attribute to sensors.

### v1.8.1
*   **Fix:** Corrected date parameter handling in URL to ensure accurate daily data.
*   **Feature:** Added `is_working_day` attribute to current price sensor.

### v1.8.0
*   **Major Overhaul:** Switched from downloading Excel files to direct HTML parsing.
*   **Performance:** Removed `pandas` and `openpyxl` dependencies, significantly reducing size and memory usage.

## Credits

Created by @szczepuz999.