# TGE RDN Energy Prices Integration v1.3.2

[![GitHub Release](https://img.shields.io/github/release/szczepuz999/tge_rdn_integration.svg?style=flat-square)](https://github.com/szczepuz999/tge_rdn_integration/releases)
[![GitHub](https://img.shields.io/github/license/szczepuz999/tge_rdn_integration.svg?style=flat-square)](LICENSE)

Integracja Home Assistant do pobierania cen energii z TGE RDN (Towarowa Giełda Energii - Rynek Dnia Następnego).

## ✅ Wersja 1.3.2 - Co nowego:

- 🚨 **CRITICAL URL FIX** - TGE zmieniło strukturę serwerów, poprawiony URL pattern
- 📡 **TOMORROW DATA FIXED** - teraz pobiera z poprawnego adresu TGE
- 💰 **NEGATIVE PRICES** - zachowana obsługa ujemnych cen dla prosumentów (v1.3.0)
- 🚀 **IMMEDIATE FETCH** - zachowane (v1.1.0)

## 🚨 CRITICAL FIX v1.3.2

### ❌ Problem w poprzednich wersjach:
```
WRONG: /pub/TGE/Wyniki%2015/RDN/
```

### ✅ Fix w v1.3.2:
```
CORRECT: /pub/TGE/A_SDAC%202025/RDN/
```

**TGE zmieniło strukturę serwerów - to dlatego nie pobierało jutrzejszych danych!**

## 💰 PROSUMER NEGATIVE PRICE HANDLING (v1.3.0+)

### ⚡ Jak działa dla prosumentów:
```
Jeśli cena TGE < 0 PLN/MWh:
✅ Energia: 0 PLN (nie ujemna, nie rabat)
✅ Dystrybucja: nadal płacisz (120 PLN/MWh)
✅ Opłaty: nadal płacisz (2 PLN/MWh)
✅ VAT: od 0 PLN energii = 0 PLN
```

### 🧮 Formuła v1.3.0+:
```
Cena_brutto = (max(0, Cena_TGE) × (1 + VAT)) + Opłata_giełdowa + Dystrybucja
```

## 🚀 Immediate Fetch (v1.1.0+)

Przy starcie integracji **natychmiast** pobiera dane z **poprawnego URL**:
```
🚀 TGE RDN Integration starting up...
📡 FORCE FETCH: Getting tomorrow's data (2025-10-05 - Saturday)...
✅ Tomorrow data (Saturday) loaded: 24 hours, avg 325.50 PLN/MWh
✅ TGE RDN Integration ready! Today: ✅, Tomorrow: ✅
```

## 📅 Daily Operation (v1.2.0+)

**TGE publikuje dane codziennie** włączając weekendy:
- **14:00-16:00**: Co 10 minut (jutro) - CODZIENNIE  
- **11:00-12:00**: Co 15 minut (dziś) - CODZIENNIE
- **Startup**: Immediate fetch z poprawnego URL

## 🚀 Instalacja

1. Skopiuj folder `custom_components/tge_rdn/` do `/config/custom_components/`
2. **Uruchom ponownie Home Assistant** ⭐ **TERAZ Z POPRAWNYM URL TGE**
3. Dodaj integrację: **Configuration** → **Integrations** → **+ Add Integration** → **"TGE RDN"**
4. Skonfiguruj stawki w opcjach integracji

## ⚙️ Konfiguracja

### Jednostki cen:
- **PLN/kWh** - Cena w złotych za kilowatogodzinę (zalecane)
- **PLN/MWh** - Cena w złotych za megawatogodzinę
- **EUR/kWh** - Cena w euro za kilowatogodzinę
- **EUR/MWh** - Cena w euro za megawatogodzinę

### Opłaty i podatki:
- **Opłata giełdowa** [PLN/MWh] - np. 2.0 (płacisz zawsze)
- **Stawka VAT** - np. 0.23 dla 23% (od energii, 0 jeśli ujemna)
- **Dystrybucja pozostałe godziny** [PLN/MWh] - płacisz zawsze
- **Dystrybucja szczyt przedpołudniowy** [PLN/MWh] - płacisz zawsze
- **Dystrybucja szczyt popołudniowy** [PLN/MWh] - płacisz zawsze

## 📊 Sensory

Po instalacji otrzymasz 3 sensory:

- `sensor.tge_rdn_current_price` - Aktualna cena brutto (z obsługą ujemnych)
- `sensor.tge_rdn_next_hour_price` - Cena następnej godziny brutto
- `sensor.tge_rdn_daily_average` - Średnia dzienna cena brutto

## 📈 Atrybuty dla wykresów - TERAZ Z JUTRZEJSZYMI DANYMI!

```yaml
data_status:
  today_available: true          # ✅ Dziś dostępne
  tomorrow_available: true       # ✅ JUTRO TERAZ DOSTĘPNE! 
  today_hours: 24               # ✅ Pełne dane dziś
  tomorrow_hours: 24            # ✅ PEŁNE DANE JUTRO!
  tomorrow_expected_time: "14:00-15:30 DAILY"
  tomorrow_last_check: "2025-10-03T18:36:00"  # ✅ Sprawdzone
  tomorrow_force_fetched: true  # ✅ Pobrane przy starcie
  tomorrow_day: "Saturday"      # ✅ Sobota

prices_tomorrow_gross:          # ✅ TERAZ WYPEŁNIONE!
  - time: "2025-10-05T10:00:00"
    hour: 11
    price_tge_original: 325.0
    price_gross: 0.528
    is_negative_hour: false
```

## 🕐 Harmonogram TGE (DAILY) - POPRAWNY URL

- **Dziś**: ~11:05 - pobiera z poprawnego URL ✅
- **Jutro**: ~14:00 - **TERAZ POBIERA Z POPRAWNEGO URL** ✅
- **Weekendy**: ✅ Dane dostępne (v1.2.0+)
- **Startup**: ⭐ OD RAZU z poprawnego URL

## 📄 Licencja

MIT License - zobacz plik LICENSE

## 🐛 Zgłaszanie problemów

https://github.com/szczepuz999/tge_rdn_integration/issues

## 📊 Changelog

- **v1.3.2**: 🚨 CRITICAL URL FIX - TGE server structure change
- **v1.3.1**: 🔧 Tomorrow data parsing fix
- **v1.3.0**: 💰 Negative prices handling for prosumers
- **v1.2.0**: 📅 Weekend data fix (TGE publishes daily)
- **v1.1.0**: 🚀 Immediate fetch on startup
- **v1.0.9**: ⏰ Better tomorrow data timing (14:00)
