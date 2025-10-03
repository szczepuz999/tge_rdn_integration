# TGE RDN Energy Prices Integration v1.0.9

[![GitHub Release](https://img.shields.io/github/release/szczepuz999/tge_rdn_integration.svg?style=flat-square)](https://github.com/szczepuz999/tge_rdn_integration/releases)
[![GitHub](https://img.shields.io/github/license/szczepuz999/tge_rdn_integration.svg?style=flat-square)](LICENSE)

Integracja Home Assistant do pobierania cen energii z TGE RDN (Towarowa Giełda Energii - Rynek Dnia Następnego).

## ✅ Wersja 1.0.9 - Co nowego:

- ⏰ **IMPROVED TOMORROW DATA** - sprawdza od 14:00 co 10 minut (wcześniej 15:00)
- 🧠 **INTELIGENTNE OKNA** - różne interwały w różnych godzinach
- 📊 **ENHANCED ATTRIBUTES** - tomorrow_data_status z informacjami o dostępności
- 🔍 **LEPSZE LOGOWANIE** - jasne info kiedy dane na jutro się pojawiają

## ⏰ Harmonogram sprawdzania v1.0.9

| Czas | Interwał | Cel |
|------|----------|-----|
| 00:05-01:00 | 5 minut | Dane na dziś |
| 11:00-12:00 | 15 minut | Publikacja danych na dziś |
| 13:30-14:00 | 15 minut | Przygotowanie do jutro |
| **14:00-16:00** | **10 minut** | **Publikacja danych na jutro** ⭐ |
| 16:00-18:00 | 10 minut | Dalsze sprawdzanie jutro |
| 18:00+ | 60 minut | Normalny tryb |

## 🚀 Instalacja

1. Skopiuj folder `custom_components/tge_rdn/` do `/config/custom_components/`
2. Uruchom ponownie Home Assistant  
3. Dodaj integrację: **Configuration** → **Integrations** → **+ Add Integration** → **"TGE RDN"**
4. Skonfiguruj stawki w opcjach integracji

## 📊 Enhanced Attributes v1.0.9

```yaml
data_status:
  today_available: true
  tomorrow_available: true
  today_hours: 24
  tomorrow_hours: 24
  tomorrow_expected_time: "14:00-15:30"
  tomorrow_last_check: "2025-10-03T14:25:00"
```

## 🔍 Przykładowe logi v1.0.9

```
INFO: Starting TGE data update at 14:23:45
INFO: Attempting to fetch tomorrow's data (2025-10-04) at 14:23:45
INFO: ✅ Tomorrow's data became available at 14:23:45
INFO: Tomorrow data loaded: 24 hours, avg 325.50 PLN/MWh
INFO: Data update complete: Today ✅ Available, Tomorrow ✅ Available
```

## ⚙️ Konfiguracja

### Jednostki cen:
- **PLN/MWh** - Cena w złotych za megawatogodzinę
- **PLN/kWh** - Cena w złotych za kilowatogodzinę (zalecane)
- **EUR/MWh** - Cena w euro za megawatogodzinę
- **EUR/kWh** - Cena w euro za kilowatogodzinę

### Opłaty i podatki:
- **Opłata giełdowa** [PLN/MWh] - np. 2.0
- **Stawka VAT** - np. 0.23 dla 23%
- **Dystrybucja pozostałe godziny** [PLN/MWh] - taryfa poza szczytem
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
prices_tomorrow_gross:  # ⭐ Dostępne już od 14:00!
  - time: "2025-10-04T10:00:00"
    hour: 11
    price_tge_net: 325.0
    price_gross: 0.528
    price_gross_pln_mwh: 528.0
```

## 🕐 Harmonogram TGE

- **Dziś**: ~11:05 (publikacja przez TGE)
- **Jutro**: ~14:00 (publikacja przez TGE) ⭐ IMPROVED
- **Weekendy**: Brak danych (normalne)

## 📄 Licencja

MIT License - zobacz plik LICENSE

## 🐛 Zgłaszanie problemów

https://github.com/szczepuz999/tge_rdn_integration/issues
