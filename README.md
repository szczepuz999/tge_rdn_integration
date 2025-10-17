# TGE RDN Energy Prices Integration v1.6.1

Integracja Home Assistant do pobierania cen energii z TGE RDN (Towarowa Giełda Energii - Rynek Dnia Następnego).

## ✅ Wersja 1.6.1 - Co nowego:

- 🔍 **SMART URL FINDING** - automatyczne radzenie sobie z niespójnymi nazwami plików TGE
- 📁 **9 FILE VARIATIONS** - próbuje _2, _3, ost, _ost, _final i inne warianty
- 🔄 **AUTOMATIC FALLBACK** - jeśli jeden wariant nie działa, próbuje kolejnych
- 📊 **ENHANCED LOGGING** - pokazuje wszystkie próby znalezienia pliku

## 🔍 SMART URL FINDING (v1.6.1)

### Problem z TGE:
TGE używa **niespójnych nazw plików**:
```
2025-10-17: ...delivery_day_2025_10_17_2.xlsx      ← _2
2025-10-16: ...delivery_day_2025_10_16ost.xlsx     ← ost
2025-10-15: ...delivery_day_2025_10_15.xlsx        ← standard
```

### Rozwiązanie v1.6.1:
Integracja automatycznie próbuje **9 wariantów**:
1. Standardowa nazwa
2. _2, _3, _4 (wersje)
3. ost, _ost (ostateczna)
4. _final, _v2, _v3 (inne warianty)

### Example logs:
```
🌐 Fetching today data - trying 9 URL variations
🌐 Attempt 1/9: ...2025_10_17.xlsx
❌ Attempt 1 failed: HTTP 404
🌐 Attempt 2/9: ...2025_10_17_2.xlsx
✅ File found at attempt 2/9!
✅ Today data loaded: 24 hours, avg 350.50 PLN/MWh
```

## ⏰ HOURLY UPDATES & EARLIER TOMORROW CHECK

- **Hourly updates**: Gwarantowane o pełnych godzinach (v1.5.0)
- **Tomorrow check**: Od 12:00 zamiast 13:30 (v1.5.1)

## 🇵🇱 POLISH HOLIDAYS & PROSUMER PRICING

- **Weekends/Holidays**: Najniższa dystrybucja 24h (v1.4.0)
- **Negative prices**: Prosumer logic - energia 0 PLN (v1.3.0)

## 🚀 Instalacja

```bash
# 1. Skopiuj folder
cp -r custom_components/tge_rdn /config/custom_components/

# 2. Restart Home Assistant
sudo systemctl restart home-assistant
```

## 📊 Sensory

- `sensor.tge_rdn_current_price` - Aktualna cena
- `sensor.tge_rdn_next_hour_price` - Następna godzina
- `sensor.tge_rdn_daily_average` - Średnia dzienna

## Changelog

- **v1.6.0**: 🔍 Smart URL finding - handles inconsistent TGE naming
- **v1.5.1**: ⏰ Earlier tomorrow check from 12:00
- **v1.5.0**: ⏰ Guaranteed hourly updates
- **v1.4.0**: 🇵🇱 Polish holidays support
- **v1.3.3**: 🛠️ Tomorrow data preservation
- **v1.3.0**: 💰 Negative prices handling
