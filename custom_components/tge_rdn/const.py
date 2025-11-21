"""Constants for TGE RDN integration."""

DOMAIN = "tge_rdn"
DEFAULT_NAME = "TGE RDN"

# Price units
UNIT_PLN_MWH = "PLN/MWh"
UNIT_PLN_KWH = "PLN/kWh"
UNIT_EUR_MWH = "EUR/MWh"
UNIT_EUR_KWH = "EUR/kWh"

# Configuration
CONF_UNIT = "unit"
DEFAULT_UNIT = UNIT_PLN_KWH

CONF_EXCHANGE_FEE = "exchange_fee"
CONF_VAT_RATE = "vat_rate"
CONF_DIST_LOW = "dist_low"
CONF_DIST_MED = "dist_med"
CONF_DIST_HIGH = "dist_high"

DEFAULT_EXCHANGE_FEE = 2.0
DEFAULT_VAT_RATE = 0.23
DEFAULT_DIST_LOW = 80.0
DEFAULT_DIST_MED = 120.0
DEFAULT_DIST_HIGH = 160.0

# Update intervals (seconds)
UPDATE_INTERVAL_CURRENT = 300      # 5 min
UPDATE_INTERVAL_NEXT_DAY = 600     # 10 min
UPDATE_INTERVAL_FREQUENT = 900     # 15 min
UPDATE_INTERVAL_NORMAL = 3600      # 1 hour

# TGE DATA SOURCE
TGE_PAGE_URL = "https://tge.pl/energia-elektryczna-rdn"
