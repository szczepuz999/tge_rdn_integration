# TGE RDN Energy Prices Integration v1.5.0

[![GitHub Release](https://img.shields.io/github/release/szczepuz999/tge_rdn_integration.svg?style=flat-square)](https://github.com/szczepuz999/tge_rdn_integration/releases)
[![GitHub](https://img.shields.io/github/license/szczepuz999/tge_rdn_integration.svg?style=flat-square)](LICENSE)

Integracja Home Assistant do pobierania cen energii z TGE RDN (Towarowa Giełda Energii - Rynek Dnia Następnego).

## ✅ Wersja 1.5.0 - Co nowego:

- ⏰ **GUARANTEED HOURLY UPDATES** - sensor current_price gwarantuje aktualizację o pełnych godzinach
- 🔍 **HOUR BOUNDARY DETECTION** - wykrywa zmiany godzin i wymusza natychmiastową aktualizację
- 📅 **TIME-ALIGNED SCHEDULING** - inteligentne planowanie aktualizacji o XX:00, XX:05, XX:15
- 🚀 **FORCE UPDATE** przy każdej zmianie godziny dla aktualnej ceny
- 🇵🇱 **POLISH HOLIDAYS SUPPORT** - zachowana obsługa weekendów i świąt (v1.4.0)
- 💰 **NEGATIVE PRICES** - zachowana obsługa ujemnych cen dla prosumentów (v1.3.0)

## ⏰ GUARANTEED HOURLY UPDATES

### ⚡ Jak działa:
```
15:58 - Normal scheduled update
15:59 - Waiting for hour change...
16:00 - ⏰ HOUR BOUNDARY DETECTED!
16:00 - 🚀 FORCE UPDATE triggered (within 5 seconds)
16:00 - ✅ sensor.tge_rdn_current_price updated to hour 16 price
16:05 - Regular time-aligned update
```

### 🔍 Hour boundary detection:
- **Sprawdza co 5 minut** czy zmieniła się godzina
- **Wykrywa zmianę** np. 14:XX → 15:XX
- **Wymusza natychmiastowy update** w ciągu 5 sekund
- **Enhanced logging** pokazuje wszystkie hour changes

### 📅 Time-aligned scheduling:
```
XX:00, XX:05, XX:15 - Częste aktualizacje (co 5 min)
14:00-16:00 - Tomorrow data window (co 10 min)
11:00-12:00 - Today data window (co 15 min)  
Inne godziny - Align do następnej pełnej godziny
```

## 🇵🇱 POLISH HOLIDAYS & WEEKENDS (v1.4.0)

### ⚡ Jak działa:
```
Weekend lub Święto Państwowe:
✅ Dystrybucja: Najniższa stawka przez cały dzień (24h)
✅ Wszystkie godziny traktowane jako "off-peak"

Dzień roboczy:
✅ Normalne taryfowanie: szczyt przedpołudniowy, wieczorny, dolina
```

### 🎉 Obsługiwane święta polskie:

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
- Wielkanoc, Poniedziałek Wielkanocny
- Zielone Świątki, Boże Ciało

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
📡 FORCE FETCH: Getting tomorrow's data (2025-10-07 - Monday)...
⏰ Hour boundary detected: - → 15 - forcing update
✅ Tomorrow data (Monday) loaded: 24 hours, avg 325.50 PLN/MWh
✅ TGE RDN Integration ready! Today: ✅, Tomorrow: ✅
```

## 📅 Daily Operation

**TGE publikuje dane codziennie** włączając weekendy:
- **Hourly updates**: Gwarantowane o pełnych godzinach (v1.5.0)
- **14:00-16:00**: Co 10 minut (jutro) - CODZIENNIE  
- **11:00-12:00**: Co 15 minut (dziś) - CODZIENNIE
- **Tomorrow data preservation**: Naprawiono gubienie danych (v1.3.3)

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

- `sensor.tge_rdn_current_price` - **Aktualna cena brutto z gwarantowanymi aktualizacjami co godzinę**
- `sensor.tge_rdn_next_hour_price` - Cena następnej godziny brutto
- `sensor.tge_rdn_daily_average` - Średnia dzienna cena brutto

## 📈 Atrybuty dla wykresów - Z HOURLY UPDATES!

```yaml
hourly_updates: "Guaranteed updates at hour boundaries (XX:00) for current price"
last_update_reason: "hour_change (14 → 15)"  # lub "scheduled"

data_status:
  current_hour: 15                    # ✅ Aktualna godzina
  last_state_hour: 15                 # ✅ Ostatnia godzina kalkulacji
  today_available: true               # ✅ Dziś dostępne
  tomorrow_available: true            # ✅ Jutro dostępne!
  today_is_weekend: false             # ✅ Poniedziałek = dzień roboczy
  today_is_polish_holiday: false      # ✅ 6.10 = nie święto
  tomorrow_is_weekend: false          # ✅ Wtorek = dzień roboczy
  tomorrow_is_polish_holiday: false   # ✅ 7.10 = nie święto

prices_today_gross:                   # ✅ Z HOURLY UPDATES!
  - time: "2025-10-06T14:00:00"
    hour: 15                          # = aktualna godzina
    price_tge_original: 325.0
    price_gross: 0.523                # ✅ Aktualizowane co godzinę!
    components:
      distribution: 120.0             # Dzień roboczy szczyt
```

## 🕐 Harmonogram aktualizacji

- **Hourly**: ⏰ **Gwarantowane o XX:00** + detection co 5 min
- **Today**: ~11:05 - pobiera z zachowaniem świąt ✅
- **Tomorrow**: ~14:00 - **pobiera z weekend/holiday detection** ✅  
- **Weekends/Holidays**: ✅ Special pricing + automatic detection
- **Startup**: ⭐ Immediate fetch z zachowaniem danych

## 📄 Licencja

MIT License - zobacz plik LICENSE

## 🐛 Zgłaszanie problemów

https://github.com/szczepuz999/tge_rdn_integration/issues

## 📊 Changelog

- **v1.5.0**: ⏰ Guaranteed hourly updates - sensor updates at full hours (XX:00)
- **v1.4.0**: 🇵🇱 Polish holidays & weekends support - lowest distribution rate 24h
- **v1.3.3**: 🛠️ Tomorrow data preservation fix - no more overwriting
- **v1.3.2**: 📡 Critical URL fix - TGE server structure change  
- **v1.3.1**: 🔧 Tomorrow data parsing fix
- **v1.3.0**: 💰 Negative prices handling for prosumers
- **v1.2.0**: 📅 Weekend data fix (TGE publishes daily)
- **v1.1.0**: 🚀 Immediate fetch on startup
- **v1.0.9**: ⏰ Better tomorrow data timing (14:00)

## 🎯 Perfect for automation!

**Teraz Twoje automatyzacje mają gwarancję że sensor.tge_rdn_current_price będzie zawsze aktualny o pełnych godzinach!**
