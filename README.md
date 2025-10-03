# TGE RDN Energy Prices Integration v1.2.0

[![GitHub Release](https://img.shields.io/github/release/szczepuz999/tge_rdn_integration.svg?style=flat-square)](https://github.com/szczepuz999/tge_rdn_integration/releases)
[![GitHub](https://img.shields.io/github/license/szczepuz999/tge_rdn_integration.svg?style=flat-square)](LICENSE)

Integracja Home Assistant do pobierania cen energii z TGE RDN (Towarowa Giełda Energii - Rynek Dnia Następnego).

## ✅ Wersja 1.2.0 - Co nowego:

- 📅 **CRITICAL FIX: WEEKEND DATA** - TGE publikuje dane CODZIENNIE włączając weekendy!
- 🗓️ **DAILY FETCH** - integracja teraz próbuje pobrać dane każdego dnia
- 🔍 **ENHANCED LOGGING** - logi pokazują dzień tygodnia dla jasności
- 📊 **WEEKEND ATTRIBUTES** - informacje o publikacji codziennej

## 📅 WAŻNE: TGE publikuje dane codziennie

### ❌ BŁĘDNE ZAŁOŻENIE (do v1.1.0):
- Weekendy = brak danych
- Skipowanie pobierania w soboty/niedziele 
- "Expected for weekends" w logach

### ✅ RZECZYWISTOŚĆ (v1.2.0+):
- **TGE publikuje codziennie** włączając soboty i niedziele
- **Dane dostępne 7 dni w tygodniu**
- **Integracja sprawdza każdego dnia**

## 🚀 Enhanced Daily Operation v1.2.0

### Daily Schedule (7 dni w tygodniu):
| Czas | Interwał | Cel |
|------|----------|-----|
| **14:00-16:00** | **10 minut** | **Publikacja jutro** (CODZIENNIE) |
| 13:30-14:00 | 15 minut | Przygotowanie jutro (CODZIENNIE) |
| 11:00-12:00 | 15 minut | Publikacja dziś (CODZIENNIE) |
| 00:05-01:00 | 5 minut | Wczesne dane dziś (CODZIENNIE) |
| Inne godziny | 60 minut | Normalny tryb (CODZIENNIE) |

### Przykładowe logi v1.2.0:
```
🔄 Regular update cycle at 16:36:30 on Friday
📡 Attempting to fetch tomorrow's data (2025-10-05 - Saturday) at 16:36:30
🎉 Tomorrow's data (Saturday) became available at 16:36:30
✅ Tomorrow data (Saturday) loaded: 24 hours, avg 325.50 PLN/MWh
```

## 🚀 Immediate Fetch (zachowane z v1.1.0)

Przy starcie integracji **natychmiast** pobiera dane (dziś + jutro):
```
🚀 TGE RDN Integration starting up...
📡 FORCE FETCH: Getting today's data (2025-10-03)...
📡 FORCE FETCH: Getting tomorrow's data (2025-10-04 - Saturday)...
🎉 FORCE FETCH: Tomorrow's data (Saturday) is available!
✅ TGE RDN Integration ready! Today: ✅, Tomorrow: ✅
```

## 📊 Enhanced Attributes v1.2.0

```yaml
tge_publishes_daily: "TGE publishes data EVERY DAY including weekends"
data_status:
  tomorrow_expected_time: "14:00-15:30 DAILY (including weekends)"
  tomorrow_day: "Saturday"               # Shows day name
  tomorrow_available: true               # Saturday data available!
  tomorrow_hours: 24                     # Full 24 hours
  tomorrow_last_check: "2025-10-03T16:36:30"

prices_tomorrow_gross:                   # ⭐ Saturday data available!
  - time: "2025-10-05T10:00:00"
    hour: 11
    price_tge_net: 325.0
    price_gross: 0.528
    price_gross_pln_mwh: 528.0
```

## 🎯 Korzyści v1.2.0

### ✅ Dokładne dane:
- **Soboty/niedziele** - pełne dane cenowe
- **7 dni w tygodniu** - kompletna automatyzacja
- **Weekend planning** - optymalizacja zużycia

### ✅ Lepsze automatyzacje:
- **Ładowanie EV** w weekendy przy tanich cenach
- **Pompy ciepła** - optymalizacja całotygodniowa  
- **Baterie domowe** - zarządzanie 24/7

### ✅ Clarity w logach:
- **Day names** w każdym komunikacie
- **No more "weekend assumptions"**
- **Clear data availability status**

## 🚀 Instalacja

1. Skopiuj folder `custom_components/tge_rdn/` do `/config/custom_components/`
2. **Uruchom ponownie Home Assistant** ⭐ **DANE 7 DNI W TYGODNIU**
3. Dodaj integrację: **Configuration** → **Integrations** → **+ Add Integration** → **"TGE RDN"**
4. Skonfiguruj stawki w opcjach integracji

## ⚙️ Konfiguracja

### Jednostki cen:
- **PLN/kWh** - Cena w złotych za kilowatogodzinę (zalecane)
- **PLN/MWh** - Cena w złotych za megawatogodzinę
- **EUR/kWh** - Cena w euro za kilowatogodzinę
- **EUR/MWh** - Cena w euro za megawatogodzinę

### Opłaty i podatki:
- **Opłata giełdowa** [PLN/MWh] - np. 2.0
- **Stawka VAT** - np. 0.23 dla 23%
- **Dystrybucja pozostałe godziny** [PLN/MWh] - off-peak
- **Dystrybucja szczyt przedpołudniowy** [PLN/MWh] - 7:00-13:00  
- **Dystrybucja szczyt popołudniowy** [PLN/MWh] - 16:00-21:00 (zima) / 19:00-22:00 (lato)

## 📊 Sensory

Po instalacji otrzymasz 3 sensory:

- `sensor.tge_rdn_current_price` - Aktualna cena brutto
- `sensor.tge_rdn_next_hour_price` - Cena następnej godziny brutto  
- `sensor.tge_rdn_daily_average` - Średnia dzienna cena brutto

## 🧮 Wzór kalkulacji

```
Cena_brutto = (Cena_TGE × (1 + VAT)) + Opłata_giełdowa + Dystrybucja
```

## 📈 Atrybuty dla wykresów

```yaml
prices_tomorrow_gross:   # ⭐ Dostępne 7 dni w tygodniu!
  - time: "2025-10-05T10:00:00"  # Saturday data
    hour: 11
    price_tge_net: 325.0
    price_gross: 0.528
    price_gross_pln_mwh: 528.0
```

## 🕐 Harmonogram TGE (DAILY)

- **Dziś**: ~11:05 (publikacja przez TGE) - **CODZIENNIE**
- **Jutro**: ~14:00 (publikacja przez TGE) - **CODZIENNIE** 
- **Weekendy**: ✅ **DANE DOSTĘPNE** (poprawka v1.2.0)
- **Startup**: ⭐ **OD RAZU** niezależnie od godziny i dnia

## 📄 Licencja

MIT License - zobacz plik LICENSE

## 🐛 Zgłaszanie problemów

https://github.com/szczepuz999/tge_rdn_integration/issues
