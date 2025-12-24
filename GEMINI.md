# GEMINI.md

## Project Overview

This project is a custom component for Home Assistant that integrates with the Polish energy exchange (TGE RDN) to provide real-time electricity prices. It scrapes the TGE website to fetch the data, calculates prices based on user-defined fees and distribution rates, and exposes them as sensors in Home-Assistant.

The integration is designed to be installed via the Home Assistant Community Store (HACS).

**Key Technologies:**

*   Python
*   Home Assistant SDK
*   `requests` for HTTP requests
*   `BeautifulSoup` for HTML parsing

**Architecture:**

*   The integration follows the standard Home Assistant custom component structure.
*   A `DataUpdateCoordinator` is used to fetch and cache the data from the TGE website.
*   The main logic is in `sensor.py`, which defines the `TGERDNSensor` entity for dynamic prices and `TGEFixedFeeSensor` for constant monthly fees.
*   The configuration flow is handled by `config_flow.py`.
*   Constants are defined in `const.py`.

## Building and Running

This is a Home Assistant custom component and is not intended to be run as a standalone application.

**Installation:**

The recommended installation method is via [HACS](https://hacs.xyz/).

1.  Open HACS in your Home Assistant instance.
2.  Go to "Integrations" and click "Explore & Download Repositories".
3.  Search for "TGE RDN" and install it.
4.  Restart Home Assistant.

**Configuration:**

After installation, the integration can be configured through the Home Assistant UI:

1.  Go to "Settings" -> "Devices & Services".
2.  Click "Add Integration" and search for "TGE RDN".
3.  Configure the price unit, exchange fee, VAT rate, distribution rates, and fixed monthly fees (transmission, transitional, subscription, capacity, trade).

## Localization

The integration supports English and Polish. Entity names and configuration fields are localized based on the Home Assistant language setting.

## Development Conventions

*   The code follows the standard Python and Home Assistant coding conventions.
*   The project uses `voluptuous` for configuration schema validation.
*   Logging is used to provide information about the integration's status and errors.
*   The integration is designed to be resilient to data availability issues and network errors.
