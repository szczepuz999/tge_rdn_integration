# TGE RDN Energy Prices Integration v1.7.1

[![GitHub Release](https://img.shields.io/badge/release-v1.7.1-blue.svg)](https://github.com/szczepuz999/tge_rdn_integration/releases)
[![HACS](https://img.shields.io/badge/HACS-Default-green.svg)](https://github.com/hacs/integration)

Integracja Home Assistant do pobierania cen energii z TGE RDN (Towarowa Giełda Energii - Rynek Dnia Następnego).

## ✅ Wersja 1.7.1 - FIXED v1.7.0!

- 🔧 **FIXED**: Parsuje stronę TGE zamiast katalogu (katalog jest zablokowany)
- 📄 **SOURCE PAGE**: https://tge.pl/RDN_instrumenty_15
- 🔍 **HANDLES VARIATIONS**: _2, ost, _final i inne warianty nazw
- 📊 **ENHANCED LOGGING**: Loguje WSZYSTKIE znalezione URLe

## 🔍 JAK DZIAŁA v1.7.1:

### Problem z v1.7.0:
- ❌ Próbowało parsować katalog: `https://www.tge.pl/pub/TGE/A_SDAC%202025/RDN/`
- ❌ **Katalog jest zablokowany** - HTTP 403 Forbidden

### Rozwiązanie v1.7.1:
✅ **Parsuje stronę TGE**: `https://tge.pl/RDN_instrumenty_15`

**Kroki:**
1. Pobiera HTML strony TGE RDN
2. Parsuje używając BeautifulSoup
3. Szuka linków które:
   - Kończą się na `.xlsx`
   - Zawierają datę `YYYY_MM_DD` (np. `2025_10_17`)
   - Zawierają `Raport_RDN_dzie_dostawy_delivery_day`
4. **Obsługuje wszystkie warianty** nazw automatycznie!
5. **Loguje dokładne URLe** które znalazło

### Przykładowe warianty które obsługuje:
```
✅ ...delivery_day_2025_10_17_2.xlsx      ← _2
✅ ...delivery_day_2025_10_16ost.xlsx     ← ost
✅ ...delivery_day_2025_10_15.xlsx        ← standardowa
✅ ...delivery_day_2025_10_14_final.xlsx  ← _final
```

**WSZYSTKIE warianty są automatycznie wykrywane!**

### Example Logs v1.7.1:
```
2025-10-17 12:10:00 - 🔍 Parsing TGE page for date: 2025_10_17
2025-10-17 12:10:01 - 📝 Found 127 total links on page
2025-10-17 12:10:01 - ✅ Found 1 file(s) for 2025-10-17:
2025-10-17 12:10:01 -    📄 Filename: Raport_RDN_dzie_dostawy_delivery_day_2025_10_17_2.xlsx
2025-10-17 12:10:01 -    🔗 Full URL: https://tge.pl/pub/TGE/A_SDAC%202025/RDN/Raport_RDN_dzie_dostawy_delivery_day_2025_10_17_2.xlsx
2025-10-17 12:10:01 - 👉 Selected URL: https://tge.pl/pub/TGE/.../_2.xlsx
2025-10-17 12:10:02 - 📥 Downloading today data...
2025-10-17 12:10:03 - ✅ Today (2025-10-17): 24h, avg 350.50 PLN/MWh
```

## ⏰ ALL FEATURES FROM v1.5.1 PRESERVED:

- ✅ **Earlier tomorrow check** (v1.5.1) - od 12:00
- ✅ **Guaranteed hourly updates** (v1.5.0) - o pełnych godzinach
- ✅ **Polish holidays** (v1.4.0) - weekendy i święta
- ✅ **Tomorrow preservation** (v1.3.3) - nie gubi danych
- ✅ **Negative prices** (v1.3.0) - prosumencka logika

## 🚀 Instalacja

### Metoda 1: HACS (zalecane)
1. Otwórz HACS
2. Dodaj custom repository: `https://github.com/szczepuz999/tge_rdn_integration`
3. Zainstaluj "TGE RDN Energy Prices"
4. Restart Home Assistant

### Metoda 2: Manualna
```bash
# 1. Stop HA
sudo systemctl stop home-assistant

# 2. Remove old
rm -rf /config/custom_components/tge_rdn/

# 3. Install v1.7.1
cd /config
unzip tge_rdn_v1.7.1.zip
cp -r custom_components/tge_rdn custom_components/

# 4. Start HA
sudo systemctl restart home-assistant

# 5. Add integration
Configuration → Integrations → + Add → "TGE RDN"
```

## ⚙️ Konfiguracja

- **Jednostka ceny**: PLN/kWh (zalecane)
- **Opłata giełdowa**: 2.0 PLN/MWh
- **VAT**: 0.23 (23%)
- **Dystrybucja pozostałe**: 80.0 PLN/MWh
- **Dystrybucja szczyt rano**: 120.0 PLN/MWh
- **Dystrybucja szczyt wieczór**: 160.0 PLN/MWh

## 📊 Sensory

- `sensor.tge_rdn_current_price` - Aktualna cena
- `sensor.tge_rdn_next_hour_price` - Następna godzina
- `sensor.tge_rdn_daily_average` - Średnia dzienna

## 📈 Atrybuty

```yaml
page_parsing: "Parses TGE page to find Excel file links"
last_update: "2025-10-17 12:00:00"
unit: "PLN/kWh"
version: "1.7.1"
source_page: "https://tge.pl/RDN_instrumenty_15"
```

## 🧪 Test Script

Sprawdź PRZED instalacją:

```bash
# 1. Wypakuj
unzip tge_rdn_v1.7.1.zip

# 2. Zainstaluj zależności
pip3 install requests beautifulsoup4

# 3. Test
cd tge_v171
python3 test_tge_parsing.py
```

## 🐛 Debugging

```bash
tail -f /config/home-assistant.log | grep TGE
```

Szukaj:
- `✅ Found X file(s) for YYYY-MM-DD`
- `📄 Filename: ...`
- `🔗 Full URL: https://...`
- `👉 Selected URL: ...`
- `✅ Today/Tomorrow: Xh, avg Y`

## 📊 Changelog

- **v1.7.1**: 🔧 Fixed - parses TGE page (not directory which is blocked)
- **v1.7.0**: ❌ Broken - tried to parse blocked directory
- **v1.6.1**: ❌ Broken
- **v1.6.0**: ❌ Broken
- **v1.5.1**: ⏰ Earlier tomorrow check - LAST WORKING before v1.7.1!
- **v1.5.0**: ⏰ Guaranteed hourly updates
- **v1.4.0**: 🇵🇱 Polish holidays
- **v1.3.3**: 🛠️ Tomorrow preservation
- **v1.3.0**: 💰 Negative prices

## 🎯 Requirements

- Home Assistant >= 2023.1
- Python: pandas, requests, openpyxl, beautifulsoup4

## 📄 Licencja

MIT License

## 🐛 Issues

https://github.com/szczepuz999/tge_rdn_integration/issues

---

**Teraz integracja prawidłowo parsuje stronę TGE i znajduje pliki! 🎉**
