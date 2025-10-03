"""Constants for TGE RDN integration."""

DOMAIN = "tge_rdn"
DEFAULT_NAME = "TGE RDN"

# Update intervals - IMPROVED TIMING
UPDATE_INTERVAL_CURRENT = 300   # 5 minutes after midnight (faster for today data)
UPDATE_INTERVAL_NEXT_DAY = 600  # 10 minutes during tomorrow data window (14:00-16:00)
UPDATE_INTERVAL_FREQUENT = 900  # 15 minutes during frequent check periods  
UPDATE_INTERVAL_NORMAL = 3600   # 1 hour during normal periods

# TGE URL pattern - FIXED based on actual TGE structure
TGE_URL_PATTERN = "https://www.tge.pl/pub/TGE/Wyniki%2015/RDN/Raport_RDN_dzie_dostawy_delivery_day_{year}_{month:02d}_{day:02d}.xlsx"

# Units
UNIT_PLN_MWH = "PLN/MWh"
UNIT_PLN_KWH = "PLN/kWh"
UNIT_EUR_MWH = "EUR/MWh"
UNIT_EUR_KWH = "EUR/kWh"

# Configuration
CONF_UNIT = "unit"

# Defaults
DEFAULT_UNIT = UNIT_PLN_MWH

# Fees and taxes
CONF_EXCHANGE_FEE = "exchange_fee_pln_mwh"  # PLN/MWh
CONF_VAT_RATE = "vat_rate"                  # e.g. 0.23 for 23%
CONF_DIST_LOW = "distribution_low_pln_mwh"   # off-peak hours PLN/MWh
CONF_DIST_MED = "distribution_mid_pln_mwh"   # morning peak PLN/MWh
CONF_DIST_HIGH = "distribution_high_pln_mwh" # evening peak PLN/MWh

DEFAULT_EXCHANGE_FEE = 0.0
DEFAULT_VAT_RATE = 0.23
DEFAULT_DIST_LOW = 0.0
DEFAULT_DIST_MED = 0.0
DEFAULT_DIST_HIGH = 0.0

# Required libraries for checks
REQUIRED_LIBRARIES = [
    "pandas>=1.5.0",
    "requests>=2.28.0", 
    "openpyxl>=3.0.9"
]
