# Migration Guide: v1.7.4 → v1.8.0

## Overview

Version 1.8.0 changes the data source from Excel file downloads to direct HTML table parsing. This makes the integration lighter, faster, and more reliable.

## What Changed

### Data Source
- **Before (v1.7.4)**: Downloaded Excel files from `https://tge.pl/RDN_instrumenty_15`
- **After (v1.8.0)**: Parses HTML table from `https://tge.pl/energia-elektryczna-rdn`

### Dependencies
- **Removed**: `pandas` and `openpyxl` (no longer needed for Excel parsing)
- **Kept**: `requests` and `beautifulsoup4` (for web scraping)

### Code Changes
- Removed `_find_excel_url_for_date()` method
- Removed `_download_file()` method
- Removed `_parse_excel_data()` method
- Added `_parse_html_table_for_date()` method that directly parses the web table

## What Stayed the Same

### ✅ All Functionality Preserved
- Same three sensors (current price, next hour price, daily average)
- Same attributes structure
- Same price calculations (VAT, fees, distribution)
- Same DST support (handles 23-25 hour days)
- Same Polish holidays support
- Same update intervals
- Same configuration options

### ✅ No User Action Required
- No configuration changes needed
- All existing automations will continue to work
- All existing dashboards will continue to work
- Sensor entity IDs remain unchanged

## Benefits of v1.8.0

1. **Lighter**: Removed heavy dependencies (pandas, openpyxl)
2. **Faster**: Direct table parsing instead of file download + parsing
3. **More Reliable**: Less prone to file format changes
4. **Simpler**: Cleaner code with fewer dependencies

## Testing

The integration has been tested with:
- Current day data parsing ✅
- Next day data parsing ✅
- Price calculations with VAT and fees ✅
- DST marker detection ✅
- All 24 hours properly parsed ✅

## Verification After Update

After updating to v1.8.0, verify:

1. Check the sensors are updating:
   ```
   sensor.tge_rdn_current_price
   sensor.tge_rdn_next_hour_price
   sensor.tge_rdn_daily_average
   ```

2. Check the attributes contain data:
   - `prices_today_gross`
   - `prices_tomorrow_gross` (after 12:00)

3. Check the logs for successful data fetching:
   ```
   ✅ TGE RDN v1.8.0 ready!
   ✅ Today (2025-11-22): 24h, avg XXX.XX
   ```

## Rollback (if needed)

If you need to rollback to v1.7.4:

1. Reinstall v1.7.4 from HACS or manually
2. Restart Home Assistant
3. The old Excel-based parsing will resume

## Support

If you encounter any issues:
- Check Home Assistant logs for errors
- Report issues at: https://github.com/szczepuz999/tge_rdn_integration/issues
- Include log entries and version information
