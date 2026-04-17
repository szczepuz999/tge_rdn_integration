---
description: "Use when adding a new seller, distributor, or tariff to the TGE RDN integration. Walks through tariffs.json, translations, and test creation."
---

# Add Tariff Wizard

You are adding a new seller, distributor, or tariff to the TGE RDN Home Assistant integration.

## Step 1 — Gather Information

Ask the user:
1. **What are you adding?** (new seller, new distributor, new tariff for existing seller/distributor)
2. **Name** of the seller/distributor/tariff (Polish name as used officially)
3. **Tariff type** — which standard does it follow? (G11, G12, G12w, G12n, G13, G13s, G14, dynamic, or a new type)
4. **Zone schedule** — for each zone, what hours apply? Do they differ by season (summer Apr–Sep / winter Oct–Mar)? By workday vs weekend/holiday?
5. **Rates** — distribution rate per zone (PLN/MWh), or seller energy price per zone (PLN/kWh)
6. **Fixed monthly fees** (if distributor): opłata sieciowa stała, abonamentowa, mocowa, przejściowa
7. **Seller fees** (if seller): exchange_fee, vat_rate, trade_fee, is_dynamic

If the user doesn't know exact values, use 0.0 as placeholder and add a `TODO` comment.

## Step 2 — Edit tariffs.json

Open `custom_components/tge_rdn/tariffs.json` and add the new entry.

**For a seller tariff**, add under the seller's `tariffs` array:
```json
{
  "name": "<TARIFF_NAME>",
  "exchange_fee": <float>,
  "vat_rate": 0.23,
  "trade_fee": <float>,
  "is_dynamic": <true|false>
}
```

**For a distributor tariff**, add under the distributor's `tariffs` array with full zone schedule:
```json
{
  "name": "<TARIFF_NAME>",
  "zones": {
    "<zone_name>": {
      "rate": <float PLN/MWh>,
      "schedule": [
        { "hours": [<0-23 integers>], "days": "<workdays|weekends|holidays|all>", "season": "<summer|winter|all>" }
      ]
    },
    "<fallback_zone>": {
      "rate": <float>,
      "schedule": [{ "default": true }]
    }
  },
  "fixed_fees": {
    "fixed_transmission_fee": <float>,
    "transitional_fee": <float>,
    "subscription_fee": <float>,
    "capacity_fee": <float>
  }
}
```

Rules:
- Zone schedule rules are evaluated top-to-bottom, first match wins
- Every tariff MUST have exactly one zone with `{ "default": true }` as fallback
- Hours are 0–23 integers (hour H = period H:00–H:59)
- Seasons: `"summer"` = Apr 1 – Sep 30, `"winter"` = Oct 1 – Mar 31, `"all"` = year-round
- Days: `"workdays"` = Mon–Fri (excluding holidays), `"weekends"` = Sat–Sun, `"holidays"` = Polish public holidays, `"all"` = every day

## Step 3 — Update Translations

Add Polish and English display names for the new tariff in both files:
- `custom_components/tge_rdn/translations/pl.json`
- `custom_components/tge_rdn/translations/en.json`

## Step 4 — Write Tests

Create or extend a test file in `tests/` using `unittest.TestCase`. Required test cases:

```python
class TestNewTariff(unittest.TestCase):
    def test_zone_assignment_normal_workday(self):
        """Zone resolves correctly during a regular workday hour."""

    def test_zone_assignment_boundary_hours(self):
        """Zone resolves correctly at every boundary hour (e.g., 05:59→06:00, 21:59→22:00)."""

    def test_zone_assignment_weekend(self):
        """Weekends use correct zone (especially for G12w-type tariffs)."""

    def test_zone_assignment_holiday(self):
        """Polish public holidays use correct zone."""

    def test_zone_assignment_summer_vs_winter(self):
        """Seasonal schedule differences are applied correctly."""

    def test_default_zone_fallback(self):
        """Unmatched hours fall through to the default zone."""
```

## Step 5 — Verify

1. Confirm `tariffs.json` is valid JSON (no trailing commas, proper encoding)
2. Confirm the config flow can list the new seller/distributor and its tariffs
3. Confirm all new tests pass
