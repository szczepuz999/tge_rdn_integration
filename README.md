# TGE RDN Integration for Home Assistant

Integracja Home Assistant do pobierania cen energii elektrycznej z Rynku Dnia Następnego (RDN) Towarowej Giełdy Energii (TGE).

## Funkcjonalności

- **Automatyczne pobieranie**: Pobiera ceny o 00:10 na bieżący dzień oraz o 15:00 na następny dzień
- **Sensory godzinowe**: Aktualna cena, cena następnej godziny, średnia dzienna
- **Różne jednostki**: PLN/MWh, PLN/kWh, EUR/MWh, EUR/kWh
- **Szablony Jinja2**: Możliwość dostosowania wartości przez szablony
- **Atrybuty rozszerzone**: Pełne dane godzinowe, minimum, maksimum, średnie

## Instalacja

### Poprzez HACS (zalecane)

1. Otwórz HACS w Home Assistant
2. Przejdź do "Integracje" 
3. Kliknij menu (...) i wybierz "Custom repositories"
4. Dodaj URL repozytorium i wybierz kategorię "Integration"
5. Zainstaluj integrację TGE RDN
6. Restartuj Home Assistant

### Instalacja ręczna

1. Pobierz pliki integracji
2. Skopiuj folder `tge_rdn` do `config/custom_components/`
3. Restartuj Home Assistant

## Konfiguracja

1. Przejdź do **Konfiguracja** > **Integracje**
2. Kliknij **Dodaj integrację**
3. Wyszukaj **TGE RDN**
4. Skonfiguruj nazwę integracji
5. Opcjonalnie skonfiguruj jednostki i szablony w opcjach

## Sensory

Integracja tworzy następujące sensory:

- `sensor.tge_rdn_current_price` - Aktualna cena energii
- `sensor.tge_rdn_next_hour_price` - Cena w następnej godzinie  
- `sensor.tge_rdn_daily_average` - Średnia cena dzienna

## Atrybuty

Każdy sensor zawiera dodatkowe atrybuty:

- `prices_today` - Wszystkie ceny godzinowe na dziś
- `prices_tomorrow` - Wszystkie ceny godzinowe na jutro (jeśli dostępne)
- `today_average/min/max` - Statystyki dzisiejsze
- `tomorrow_average/min/max` - Statystyki jutra
- `last_update` - Czas ostatniej aktualizacji

## Przykład użycia z ApexCharts

```yaml
type: custom:apexcharts-card
graph_span: 24h
span:
  start: day
header:
  show: true
  title: TGE RDN - Ceny energii dzisiaj
  colorize_states: true
now:
  show: true
  label: Teraz
series:
  - entity: sensor.tge_rdn_current_price
    type: column
    name: Cena energii
    data_generator: |
      return entity.attributes.prices_today.map((item) => {
        return [new Date(item.time).getTime(), item.price];
      });
```

## Konfiguracja jednostek

Dostępne jednostki:
- `PLN/MWh` (domyślnie)
- `PLN/kWh` 
- `EUR/MWh`
- `EUR/kWh`

## Szablony Jinja2

Przykład szablonu do zaokrąglenia:
```
{{ (value | float) | round(2) }}
```

Przykład szablonu z marżą:
```
{{ (value | float * 1.23) | round(2) }}
```

## Harmonogram aktualizacji

- **00:10** - Pobieranie cen na bieżący dzień
- **15:00** - Pobieranie cen na następny dzień
- W innych godzinach sprawdzanie co godzinę

## Wymagania

- Home Assistant 2023.1+
- Python 3.9+
- Biblioteki: pandas, requests, openpyxl

## Wsparcie

W przypadku problemów:
1. Sprawdź logi Home Assistant
2. Upewnij się że TGE publikuje dane (po 11:05 i 13:20)
3. Zgłoś problem z logami w Issues

## Licencja

MIT License
