# Tariffs Schema

This reference documents the structure of `tariffs.json` used by the TGE RDN integration.

## File Location
`custom_components/tge_rdn/tariffs.json`

## Schema Structure
```json
{
  "dealers": [
    {
      "name": "Dealer Name",
      "tariffs": [
        { 
          "name": "Tariff Name (e.g., G11)", 
          "exchange_fee": 2.0, 
          "vat_rate": 0.23, 
          "trade_fee": 0.0 
        }
      ]
    }
  ],
  "distributors": [
    {
      "name": "Distributor Name",
      "tariffs": [
        {
          "name": "Tariff Name",
          "logic": "single | dual_standard | dual_weekend | triple_tauron",
          "dist_low": 120.0,
          "dist_med": 120.0,  // Only used for triple_tauron
          "dist_high": 120.0, // Used for dual and triple
          "fixed_transmission_fee": 5.0,
          "transitional_fee": 0.0,
          "subscription_fee": 2.0,
          "capacity_fee": 10.0
        }
      ]
    }
  ]
}
```

## Logic Types
- `single`: Constant rate (`dist_low`) 24/7.
- `dual_standard`: G12 logic. Low rate 22:00-06:00 and 13:00-15:00. High rate otherwise.
- `dual_weekend`: G12w logic. Same as `dual_standard` + Low rate all weekends and holidays.
- `triple_tauron`: G13 logic. Complex 3-zone peak/off-peak logic varying by season.
