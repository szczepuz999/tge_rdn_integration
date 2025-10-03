# TGE RDN Energy Prices Integration v1.0.7

[![GitHub Release](https://img.shields.io/github/release/szczepuz999/tge_rdn_integration.svg?style=flat-square)](https://github.com/szczepuz999/tge_rdn_integration/releases)
[![GitHub](https://img.shields.io/github/license/szczepuz999/tge_rdn_integration.svg?style=flat-square)](LICENSE)

Integracja Home Assistant do pobierania cen energii z TGE RDN (Towarowa Giełda Energii - Rynek Dnia Następnego).

## ✅ Wersja 1.0.7 - Co nowego:

- 🔧 **NAPRAWIONO URL TGE** - teraz pobiera dane z `Wyniki%2015` zamiast `SDAC 2025`
- ❌ **USUNIĘTO TEMPLATE** - prostsze konfigurowanie, brak problemów z Jinja2
- 🏷️ **GITHUB INFO** - poprawne linki do @szczepuz999/tge_rdn_integration
- 📊 **CENY BRUTTO** - VAT + opłaty giełdowe + dystrybucja

## 🚀 Instalacja

1. Skopiuj folder `custom_components/tge_rdn/` do `/config/custom_components/`
2. Uruchom ponownie Home Assistant
3. Dodaj integrację: **Configuration** → **Integrations** → **+ Add Integration** → **"TGE RDN"**
4. Skonfiguruj stawki w opcjach integracji

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

**Przykład:**
- Cena TGE: 350 PLN/MWh
- VAT 23%: 350 × 1.23 = 430.5 PLN/MWh
- Opłata giełdowa: 2 PLN/MWh
- Dystrybucja (szczyt): 120 PLN/MWh
- **Suma brutto: 552.5 PLN/MWh (0.553 PLN/kWh)**

## 📈 Atrybuty dla wykresów

Każdy sensor zawiera atrybuty z pełnymi danymi:

```yaml
prices_today_gross:
  - time: "2025-10-03T10:00:00"
    hour: 11
    price_tge_net: 350.0
    price_gross: 0.553
    price_gross_pln_mwh: 552.5
```

## 🕐 Harmonogram aktualizacji

- **Dziś**: Dane dostępne po ~11:05
- **Jutro**: Dane dostępne po ~13:20  
- **Weekendy**: Brak danych (normalne)

## 📄 Licencja

MIT License - zobacz plik LICENSE

## 🐛 Zgłaszanie problemów

https://github.com/szczepuz999/tge_rdn_integration/issues
