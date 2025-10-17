# TGE RDN v1.7.3 - Complete Attributes + TGE Page Parsing

✅ **ALL attributes from v1.5.1** (prices_today_gross, prices_tomorrow_gross, etc.)
✅ **TGE page parsing** (not blocked directory)
✅ **Polish holidays + weekends** support

## Installation

```bash
cd /config
unzip tge_rdn_v1.7.3_COMPLETE.zip
cp -r custom_components/tge_rdn custom_components/
sudo systemctl restart home-assistant
```

## Key Attributes

- `prices_today_gross` - Array of 24 hourly prices with full breakdown
- `prices_tomorrow_gross` - Array of 24 tomorrow hourly prices
- Complete components: energy_with_vat, exchange_fee, distribution
- Polish holidays and weekends automatically detected

## Changes from v1.5.1

- ✅ Parses https://tge.pl/RDN_instrumenty_15 (not blocked directory)
- ✅ Handles ALL filename variations (_2, ost, _final, etc.)
- ✅ ALL ATTRIBUTES PRESERVED from v1.5.1

## Version 1.7.3

Based on working v1.5.1 with TGE page parsing added.
