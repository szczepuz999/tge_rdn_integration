# TGE RDN Integration for Home Assistant

Integracja Home Assistant do pobierania cen energii elektrycznej z Rynku Dnia Następnego (RDN) TGE z pełnym naliczaniem VAT, opłat giełdowych i dystrybucyjnych.

## 🧮 Wzór obliczania ceny końcowej

```
total_gross = (cena_TGE × (1 + VAT)) + exchange_fee + distribution_rate
```

**VAT naliczany jest tylko od ceny TGE**, a opłaty giełdowe i dystrybucyjne dodawane są bez VAT.

## 📊 Ceny brutto w atrybutach

**NOWOŚĆ:** Wszystkie ceny w atrybutach są teraz obliczone z pełnym naliczaniem VAT, opłat i dystrybucji!

### Dostępne atrybuty:

#### Ceny oryginalne (TGE netto):
- `prices_today` - bazowe ceny TGE na dziś
- `prices_tomorrow` - bazowe ceny TGE na jutro
- `today_average/min/max` - statystyki TGE

#### Ceny brutto (z VAT + opłaty):
- `prices_today_gross` - kompletne ceny brutto na dziś
- `prices_tomorrow_gross` - kompletne ceny brutto na jutro  
- `today_average_gross/min_gross/max_gross` - statystyki brutto
- `tomorrow_average_gross/min_gross/max_gross` - statystyki brutto

### Struktura ceny brutto:

```yaml
prices_today_gross: [
  {
    "time": "2025-10-01T19:00:00",
    "hour": 20,
    "price_tge_net": 450.0,           # Oryginalna cena TGE
    "price_gross": 0.706,             # Cena brutto w wybranej jednostce
    "price_gross_pln_mwh": 705.5      # Cena brutto w PLN/MWh
  }
]
```

## ⚡ Strefy taryfowe dystrybucji

### Okres letni (kwiecień-wrzesień):
- **07:00–13:00**: Szczyt przedpołudniowy
- **19:00–22:00**: Szczyt popołudniowy
- **13:00–19:00 i 22:00–07:00**: Pozostałe godziny

### Okres zimowy (październik-marzec):
- **07:00–13:00**: Szczyt przedpołudniowy  
- **16:00–21:00**: Szczyt popołudniowy
- **13:00–16:00 i 21:00–07:00**: Pozostałe godziny

## 🔧 Konfiguracja

W opcjach integracji ustaw:
- **Opłata giełdowa [PLN/MWh]**: np. 2.0
- **Stawka VAT**: np. 0.23 (23%)
- **3 stawki dystrybucji**: pozostałe/przedpołudnie/popołudnie [PLN/MWh]

## 📈 Przykład karty ApexCharts z cenami brutto

```yaml
type: custom:apexcharts-card
graph_span: 24h
header:
  title: "TGE RDN - Ceny energii brutto"
series:
  - entity: sensor.tge_rdn_current_price
    name: "Cena brutto"
    type: column
    data_generator: |
      return entity.attributes.prices_today_gross.map((item) => {
        return [new Date(item.time).getTime(), item.price_gross];
      });
```

## 🚀 Instalacja

1. Skopiuj `custom_components/tge_rdn` do `/config/custom_components/`
2. Restart Home Assistant (automatyczna instalacja bibliotek)
3. Dodaj integrację: Konfiguracja → Integracje → + → "TGE RDN"
4. Skonfiguruj stawki w Opcjach

## 📊 Sensory

- `sensor.tge_rdn_current_price` - Cena brutto bieżąca
- `sensor.tge_rdn_next_hour_price` - Cena brutto następnej godziny
- `sensor.tge_rdn_daily_average` - Średnia cena brutto dzienna

## 🔍 Rozbicie kosztów

Każdy sensor zawiera szczegółowy rozkład w `components`:

```yaml
components:
  base_energy_pln_mwh: 450.0           # TGE netto
  tge_with_vat_pln_mwh: 553.5          # TGE + VAT
  exchange_fee_pln_mwh: 2.0            # Opłata giełdowa
  distribution_pln_mwh: 150.0          # Dystrybucja
  vat_rate: 0.23                       # VAT 23%
  total_gross_pln_mwh: 705.5           # Cena końcowa
```

## 💡 Korzyści nowego wzoru

- VAT tylko od energii TGE (~5% taniej niż poprzedni wzór)
- Ceny brutto w atrybutach gotowe do wykresów
- Pełna transparentność kosztów
- Automatyczne przełączanie stref taryfowych

**Wszystkie ceny w atrybutach zawierają już pełne naliczenia zgodnie z wzorem!**
