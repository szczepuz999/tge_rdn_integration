"""Constants for TGE RDN integration."""

DOMAIN = "tge_rdn"
DEFAULT_NAME = "TGE RDN"

# Aktualizacje
UPDATE_INTERVAL_CURRENT = 600  # 10 minut po północy
UPDATE_INTERVAL_NEXT_DAY = 15 * 60  # 15:00 na następny dzień

# URL pattern
TGE_URL_PATTERN = "https://www.tge.pl/pub/TGE/SDAC%20{year}/RDN/Raport_RDN_dzie_dostawy_delivery_day_{year}_{month:02d}_{day:02d}.xlsx"

# Jednostki
UNIT_PLN_MWH = "PLN/MWh"
UNIT_PLN_KWH = "PLN/kWh"
UNIT_EUR_MWH = "EUR/MWh"
UNIT_EUR_KWH = "EUR/kWh"

# Konfiguracja
CONF_UNIT = "unit"
CONF_TEMPLATE = "template"

# Domyślne wartości
DEFAULT_UNIT = UNIT_PLN_MWH
DEFAULT_TEMPLATE = "{{ value }}"

# Wymagane biblioteki
REQUIRED_LIBRARIES = [
    "pandas>=1.5.0",
    "requests>=2.28.0", 
    "openpyxl>=3.0.9"
]
