# TGE RDN Energy Prices Integration v1.4.0

[![GitHub Release](https://img.shields.io/github/release/szczepuz999/tge_rdn_integration.svg?style=flat-square)](https://github.com/szczepuz999/tge_rdn_integration/releases)
[![GitHub](https://img.shields.io/github/license/szczepuz999/tge_rdn_integration.svg?style=flat-square)](LICENSE)

Integracja Home Assistant do pobierania cen energii z TGE RDN (Towarowa Giełda Energii - Rynek Dnia Następnego).

## ✅ Wersja 1.4.0 - Co nowego:

- 🇵🇱 **POLISH HOLIDAYS SUPPORT** - weekendy i święta państwowe = najniższa stawka dystrybucji 24h
- 📅 **WEEKEND DETECTION** - automatyczne rozpoznawanie sobót i niedziel  
- 🎉 **MOVEABLE HOLIDAYS** - Wielkanoc, Boże Ciało itp. obliczane automatycznie
- 💰 **NEGATIVE PRICES** - zachowana obsługa ujemnych cen dla prosumentów (v1.3.0)
- 🛠️ **TOMORROW DATA PRESERVATION** - naprawiono gubienie jutrzejszych danych (v1.3.3)
- 📡 **CORRECT TGE URL** - poprawiony URL pattern dla nowej struktury TGE (v1.3.2)

## 🇵🇱 POLISH HOLIDAYS & WEEKENDS

### ⚡ Jak działa:
```
Weekend lub Święto Państwowe:
✅ Dystrybucja: Najniższa stawka przez cały dzień (24h)
✅ Wszystkie godziny traktowane jako "off-peak"

Dzień roboczy:
✅ Normalne taryfowanie: szczyt przedpołudniowy, wieczorny, dolina
```

### 🎉 Obsługiwane święta polskie 2025:

**Stałe:**
- 1 stycznia - Nowy Rok
- 6 stycznia - Święto Trzech Króli  
- 1 maja - Święto Pracy
- 3 maja - Święto Konstytucji 3 Maja
- 15 sierpnia - Wniebowzięcie NMP
- 1 listopada - Wszystkich Świętych
- 11 listopada - Święto Niepodległości
- 25 grudnia - Boże Narodzenie
- 26 grudnia - Drugi Dzień Świąt

**Ruchome (względem Wielkanocy):**
- Wielkanoc (20 kwietnia 2025)
- Poniedziałek Wielkanocny (21 kwietnia 2025)  
- Zielone Świątki (8 czerwca 2025)
- Boże Ciało (19 czerwca 2025)

**Weekendy:**
- Wszystkie soboty i niedziele

## 💰 PROSUMER NEGATIVE PRICE HANDLING (v1.3.0+)

### ⚡ Jak działa dla prosumentów:
```
Jeśli cena TGE < 0 PLN/MWh:
✅ Energia: 0 PLN (nie ujemna, nie rabat)
✅ Dystrybucja: nadal płacisz (najniższa stawka w weekend/święto)
✅ Opłaty: nadal płacisz (2 PLN/MWh)
✅ VAT: od 0 PLN energii = 0 PLN
```

### 🧮 Formuła v1.3.0+:
```
Cena_brutto = (max(0, Cena_TGE) × (1 + VAT)) + Opłata_giełdowa + Dystrybucja
```

## 🚀 Immediate Fetch (v1.1.0+)

Przy starcie integracji **natychmiast** pobiera dane:
```
🚀 TGE RDN Integration starting up...
📡 FORCE FETCH: Getting tomorrow's data (2025-10-04 - Saturday)...
🇵🇱 Weekend detected: using lowest distribution rate 24h
✅ Tomorrow data (Saturday) loaded: 24 hours, avg 229.28 PLN/MWh, ⚠️ 5 negative price hours
✅ TGE RDN Integration ready! Today: ✅, Tomorrow: ✅
```

## 📅 Daily Operation (v1.2.0+)

**TGE publikuje dane codziennie** włączając weekendy:
- **14:00-16:00**: Co 10 minut (jutro) - CODZIENNIE  
- **11:00-12:00**: Co 15 minut (dziś) - CODZIENNIE
- **Startup**: Immediate fetch z preservacją danych (v1.3.3)

## 🚀 Instalacja

1. Skopiuj folder `custom_components/tge_rdn/` do `/config/custom_components/`
2. **Uruchom ponownie Home Assistant**
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
- **Dystrybucja pozostałe godziny** [PLN/MWh] - off-peak, weekendy, święta
- **Dystrybucja szczyt przedpołudniowy** [PLN/MWh] - 7-13 dni robocze
- **Dystrybucja szczyt wieczorny** [PLN/MWh] - 16-21/19-22 dni robocze

## 📊 Sensory

Po instalacji otrzymasz 3 sensory:

- `sensor.tge_rdn_current_price` - Aktualna cena brutto (z weekendami/świętami)
- `sensor.tge_rdn_next_hour_price` - Cena następnej godziny brutto
- `sensor.tge_rdn_daily_average` - Średnia dzienna cena brutto

## 📈 Atrybuty dla wykresów - Z POLSKIMI ŚWIĘTAMI!

```yaml
data_status:
  today_available: true          # ✅ Dziś dostępne
  tomorrow_available: true       # ✅ Jutro dostępne!
  today_is_weekend: false        # ✅ Piątek = dzień roboczy
  today_is_polish_holiday: false # ✅ 3.10 = nie święto
  tomorrow_is_weekend: true      # ✅ Sobota = weekend!
  tomorrow_is_polish_holiday: false # ✅ 4.10 = nie święto
  tomorrow_day: "Saturday"       # ✅ Sobota

prices_tomorrow_gross:          # ✅ Z WEEKEND PRICING!
  - time: "2025-10-04T10:00:00"
    hour: 11
    price_tge_original: 229.0
    is_weekend: true            # ✅ Weekend flag
    is_polish_holiday: false    # ✅ Holiday flag  
    price_gross: 0.155          # ✅ Z najniższą dystrybucją!
    components:
      distribution: 80.0        # ✅ dist_low (weekend rate)

polish_holidays_support: "Weekends and Polish holidays use lowest distribution rate 24h"
```

## 🕐 Harmonogram TGE (DAILY)

- **Dziś**: ~11:05 - pobiera z zachowaniem świąt ✅
- **Jutro**: ~14:00 - **pobiera z weekend/holiday detection** ✅  
- **Weekendy**: ✅ Dane dostępne + special pricing
- **Święta**: ✅ Automatyczna detekcja + najniższa stawka
- **Startup**: ⭐ Immediate fetch z preservation

## 📄 Licencja

MIT License - zobacz plik LICENSE

## 🐛 Zgłaszanie problemów

https://github.com/szczepuz999/tge_rdn_integration/issues

## 📊 Changelog

- **v1.4.0**: 🇵🇱 Polish holidays & weekends support - lowest distribution rate 24h
- **v1.3.3**: 🛠️ Tomorrow data preservation fix - no more overwriting
- **v1.3.2**: 📡 Critical URL fix - TGE server structure change  
- **v1.3.1**: 🔧 Tomorrow data parsing fix
- **v1.3.0**: 💰 Negative prices handling for prosumers
- **v1.2.0**: 📅 Weekend data fix (TGE publishes daily)
- **v1.1.0**: 🚀 Immediate fetch on startup
- **v1.0.9**: ⏰ Better tomorrow data timing (14:00)
