# TGE RDN Energy Prices Integration v1.8.0

[![HACS][hacs-badge]][hacs-url]
[![GitHub Release][release-badge]][release-url]
[![License][license-badge]][license-url]

Home Assistant integration for TGE RDN (Polish energy exchange) electricity prices.

## Features

- ✅ **Web Table Parsing** - Directly parses price table from https://tge.pl/energia-elektryczna-rdn
- ✅ **No Excel Downloads** - Fast, efficient HTML table parsing with BeautifulSoup
- ✅ **Complete Attributes** - ALL prices with full breakdown
- ✅ **Polish Holidays Support** - Automatic detection of weekends and holidays
- ✅ **DST Change Support** - Handles day with 25 hours (autumn) and 23 hours (spring)
- ✅ **Negative Prices** - Prosumer logic: negative energy = 0 PLN, distribution still applies
- ✅ **Hourly Updates** - Guaranteed updates at full hours
- ✅ **Tomorrow Prices** - Available from 12:00 PM daily

## Installation

### Via HACS (recommended)

1. Open HACS
2. Go to Integrations
3. Click "Explore & Download Repositories"
4. Search for "TGE RDN"
5. Install and restart Home Assistant

### Manual Installation

```bash
cd /config/custom_components
git clone https://github.com/szczepuz999/tge_rdn_integration.git tge_rdn
sudo systemctl restart home-assistant
```

## Configuration

1. Go to Settings → Devices & Services → Create Automation
2. Search for "TGE RDN"
3. Configure pricing parameters:
   - **Price Unit**: PLN/kWh (default), PLN/MWh, EUR/kWh, EUR/MWh
   - **Exchange Fee**: 2.0 PLN/MWh
   - **VAT Rate**: 0.23 (23%)
   - **Distribution Rates**:
     - Off-peak: 80 PLN/MWh
     - Morning peak: 120 PLN/MWh
     - Evening peak: 160 PLN/MWh

## Sensors

- `sensor.tge_rdn_current_price` - Current hour price
- `sensor.tge_rdn_next_hour_price` - Next hour price
- `sensor.tge_rdn_daily_average` - Daily average price

## Attributes

Each sensor includes comprehensive attributes:

```yaml
today:
  date: "2025-10-25"
  average_price: 350.50
  min_price: 250.00
  max_price: 450.00
  total_hours: 24
  negative_hours: 0

prices_today_gross:
  - time: "2025-10-25T00:00:00"
    hour: 1
    price: 320.50
    price_gross: 0.450  # In configured unit
    components:
      energy_with_vat: 396.22
      exchange_fee: 2.0
      distribution: 80.0

# + Similar for tomorrow
tomorrow: {...}
prices_tomorrow_gross: [...]
```

## Special Cases

### DST Change Days

On days when clocks change (26 October, 31 March):
- **Autumn (Oct 26)**: 25 hours (H02 and H02a)
- **Spring (Mar 31)**: 23 hours (H03 missing)

The integration automatically handles both cases.

## Changelog

### v1.8.0 (2025-11-21)
- **BREAKING**: Changed data source from Excel files to web table
- **NEW**: Direct HTML table parsing from https://tge.pl/energia-elektryczna-rdn
- **REMOVED**: pandas and openpyxl dependencies (lighter, faster)
- **IMPROVED**: More reliable data fetching
- Maintains all existing functionality (DST support, holidays, etc.)
- All sensors and attributes work exactly as before

### v1.7.4 (2025-10-25)
- **NEW**: DST change support (H02a handling)
- Handles days with 25 hours (autumn) and 23 hours (spring)
- Enhanced error logging

### v1.7.3 (2025-10-17)
- Complete attributes from v1.5.1 restored
- TGE page parsing (not blocked directory)
- Polish holidays + weekends support
- prices_today_gross and prices_tomorrow_gross

### v1.5.1
- Earlier tomorrow check from 12:00
- Guaranteed hourly updates

### Previous versions
- Negative prices handling
- Polish holidays detection
- Tomorrow data preservation

## Requirements

- Home Assistant >= 2023.1
- Python packages:
  - requests >= 2.28.0
  - beautifulsoup4 >= 4.11.0

## Usage Examples

### ApexCharts - Compare today vs tomorrow

```yaml
type: custom:apexcharts-card
header:
  title: TGE RDN Prices
series:
  - entity: sensor.tge_rdn_current_price
    name: Today (Gross)
    data_generator: |
      return entity.attributes.prices_today_gross.map((item) => {
        return [new Date(item.time).getTime(), item.price_gross];
      });
  - entity: sensor.tge_rdn_current_price
    name: Tomorrow (Gross)
    data_generator: |
      return entity.attributes.prices_tomorrow_gross.map((item) => {
        return [new Date(item.time).getTime(), item.price_gross];
      });
```

### Automation - Cheap hours

```yaml
automation:
  - trigger:
      platform: time_pattern
      hours: "*"
    condition:
      - condition: template
        value_template: >
          {% set current = state_attr('sensor.tge_rdn_current_price', 'prices_today_gross')
             | selectattr('hour', 'eq', now().hour + 1) | first %}
          {{ current.price_gross < 0.35 if current else false }}
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.water_heater
```

## Support

- 🐛 [Report Issues](https://github.com/szczepuz999/tge_rdn_integration/issues)
- 📚 [Documentation](https://github.com/szczepuz999/tge_rdn_integration)

## License

MIT License - See LICENSE file for details

---

**Developed for Polish Home Assistant users** 🇵🇱

[hacs-badge]: https://img.shields.io/badge/HACS-Default-41BDF5.svg
[hacs-url]: https://github.com/hacs/integration
[release-badge]: https://img.shields.io/github/v/release/szczepuz999/tge_rdn_integration
[release-url]: https://github.com/szczepuz999/tge_rdn_integration/releases
[license-badge]: https://img.shields.io/github/license/szczepuz999/tge_rdn_integration
[license-url]: https://github.com/szczepuz999/tge_rdn_integration/blob/main/LICENSE
