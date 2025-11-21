# TGE RDN Integration v1.8.2 - Fixing I Price Source

## Summary
Updated the integration to use **Fixing I** prices instead of **Fixing II** prices as the primary data source.

## Changes Made

### 1. Price Column Priority (sensor.py)
Changed the column priority in `_parse_html_table_for_date()` method:

**OLD Priority:**
1. Fixing II (column 7)
2. Weighted average (column 13)
3. Continuous trading (column 4)

**NEW Priority:**
1. **Fixing I (column 2)** - PRIMARY
2. Fixing II (column 7) - Fallback
3. Weighted average (column 13) - Fallback

### 2. Version Updates
- **sensor.py**: v1.8.0 → v1.8.2
- **__init__.py**: v1.8.1 → v1.8.2
- **manifest.json**: v1.8.1 → v1.8.2

### 3. New Attribute
Added `price_source: "Fixing I"` to sensor attributes to clearly indicate the data source.

## Verification

### Test Case: H03 on 2025-11-20
Using URL: `https://tge.pl/energia-elektryczna-rdn?dateShow=20-11-2025`
(Returns data for 2025-11-21)

| Column | Name | H03 Value |
|--------|------|-----------|
| **2** | **Fixing I** | **420.90 PLN/MWh** ✅ |
| 7 | Fixing II | 383.08 PLN/MWh |
| 13 | Weighted Avg | (varies) |

**Result:** Integration now correctly uses **420.90 PLN/MWh** from Fixing I column.

## Code Changes

### sensor.py - Line ~196
```python
# Parse price - try multiple columns
price = None

# Try Fixing I price (column 2) - PRIMARY SOURCE
if len(cells) > 2:
    price_text = cells[2].get_text(strip=True)
    if price_text and price_text != '-':
        price_text = price_text.replace(',', '.').replace(' ', '')
        try:
            price = float(price_text)
        except ValueError:
            pass

# If no Fixing I, try Fixing II price (column 7)
if price is None and len(cells) > 7:
    price_text = cells[7].get_text(strip=True)
    if price_text and price_text != '-':
        price_text = price_text.replace(',', '.').replace(' ', '')
        try:
            price = float(price_text)
        except ValueError:
            pass

# If still no price, try weighted average from all trading (column 13)
if price is None and len(cells) > 13:
    price_text = cells[13].get_text(strip=True)
    if price_text and price_text != '-':
        price_text = price_text.replace(',', '.').replace(' ', '')
        try:
            price = float(price_text)
        except ValueError:
            pass
```

## TGE Table Structure

The TGE RDN table has the following structure:

### Header Row 0 (Main Categories)
- Column 2-3: **Fixing I** (colspan=2)
- Column 4-5: Notowania ciągłe (colspan=2)
- Column 6-10: **Fixing II** (colspan=5)
- Column 11-16: Łącznie notowania (colspan=6)

### Header Row 1 (Specific Columns)
- **Column 2**: Kurs [PLN/MWh] - **Fixing I Price** ← **NOW USED**
- Column 3: Wolumen [MW]
- Column 4: Kurs (średnioważony) [PLN/MWh] - Continuous
- Column 5: Wolumen [MW]
- Column 6: Kurs jednolity [EUR/MWh] - Fixing II
- **Column 7**: Kurs jednolity [PLN/MWh] - **Fixing II Price** ← Previously used
- Column 8-10: Fixing II volumes
- Column 11-16: Combined trading statistics

## Impact

### For End Users
- **More accurate prices**: Fixing I represents the main auction clearing price
- **Better price predictions**: Fixing I is the primary reference price used in energy markets
- **Transparency**: New `price_source` attribute shows data origin

### For Integration
- All existing functionality preserved
- Fallback mechanism ensures reliability (uses Fixing II if Fixing I unavailable)
- No breaking changes to API or configuration

## Testing

✅ Direct parsing test: All 24 hours use Fixing I
✅ H03 verification: 420.90 PLN/MWh (correct)
✅ No Python errors
✅ Version updated across all files
✅ New attribute added

## Files Modified
1. `custom_components/tge_rdn/sensor.py`
2. `custom_components/tge_rdn/__init__.py`
3. `custom_components/tge_rdn/manifest.json`

## Migration Notes
Users updating from v1.8.0 or v1.8.1 will automatically get the corrected prices. No configuration changes needed.

**Note**: Price values will change because they now reflect Fixing I instead of Fixing II. This is expected and correct behavior.

---
**Version**: 1.8.2  
**Date**: 2025-11-21  
**Change Type**: Bug Fix / Data Source Correction
