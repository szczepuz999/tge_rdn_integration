# Przykłady konfiguracji TGE RDN

## 1. Automatyzacja - powiadomienie o wysokich cenach

```yaml
automation:
  - id: tge_high_price_notification
    alias: "Powiadomienie - wysoka cena energii"
    trigger:
      - platform: numeric_state
        entity_id: sensor.tge_rdn_current_price
        above: 600  # PLN/MWh
    action:
      - service: notify.mobile_app_phone
        data:
          title: "Wysoka cena energii!"
          message: "Aktualna cena: {{ states('sensor.tge_rdn_current_price') }} {{ state_attr('sensor.tge_rdn_current_price', 'unit_of_measurement') }}"
```

## 2. Automatyzacja - optymalizacja ładowania pojazdu elektrycznego

```yaml
automation:
  - id: tge_ev_charging_optimization
    alias: "Optymalne ładowanie EV"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: python_script.optimize_ev_charging
        data:
          prices: "{{ state_attr('sensor.tge_rdn_current_price', 'prices_tomorrow') }}"
          charging_hours: 6
          car_switch: "switch.wallbox_charging"
```

## 3. Sensor template - koszt energii dzienny

```yaml
template:
  - sensor:
      - name: "Dzienny koszt energii"
        unit_of_measurement: "PLN"
        state: >
          {% set daily_usage = states('sensor.daily_energy_consumption') | float %}
          {% set current_price = states('sensor.tge_rdn_current_price') | float %}
          {{ (daily_usage * current_price / 1000) | round(2) }}
        attributes:
          price_per_mwh: "{{ states('sensor.tge_rdn_current_price') }}"
          daily_usage_kwh: "{{ states('sensor.daily_energy_consumption') }}"
```

## 4. Karta ApexCharts - wykres cen na 48h

```yaml
type: custom:apexcharts-card
graph_span: 48h
span:
  start: day
header:
  show: true
  title: "TGE RDN - Ceny energii (48h)"
  colorize_states: true
now:
  show: true
  label: "Teraz"
  color: red
yaxis:
  - decimals: 0
    apex_config:
      tickAmount: 5
series:
  - entity: sensor.tge_rdn_current_price
    name: "Dzisiaj"
    type: column
    color: blue
    data_generator: |
      return entity.attributes.prices_today.map((item) => {
        return [new Date(item.time).getTime(), item.price];
      });
  - entity: sensor.tge_rdn_current_price  
    name: "Jutro"
    type: column
    color: green
    data_generator: |
      const tomorrow = entity.attributes.prices_tomorrow;
      if (!tomorrow) return [];
      return tomorrow.map((item) => {
        return [new Date(item.time).getTime(), item.price];
      });
```

## 5. Skrypt Python - znajdź najtańsze godziny

```python
# python_scripts/find_cheapest_hours.py

prices_today = data.get('prices_today', [])
hours_needed = int(data.get('hours_needed', 4))

if not prices_today:
    logger.warning("Brak danych o cenach na dziś")
    service_data = {'error': 'No price data available'}
else:
    # Sortuj według ceny
    sorted_prices = sorted(prices_today, key=lambda x: x['price'])
    cheapest_hours = sorted_prices[:hours_needed]

    # Sortuj według czasu
    cheapest_hours = sorted(cheapest_hours, key=lambda x: x['hour'])

    # Przygotuj wynik
    result = {
        'cheapest_hours': [h['hour'] for h in cheapest_hours],
        'cheapest_prices': [h['price'] for h in cheapest_hours],
        'average_price': sum(h['price'] for h in cheapest_hours) / len(cheapest_hours),
        'total_cost_per_mwh': sum(h['price'] for h in cheapest_hours)
    }

    logger.info(f"Najtańsze {hours_needed} godzin: {result['cheapest_hours']}")

    # Ustaw sensor z wynikami  
    hass.states.set('sensor.cheapest_hours', 
                   f"{hours_needed} godzin",
                   result)
```

## 6. Node-RED flow - automatyzacja urządzeń

```json
[
    {
        "id": "tge_price_check",
        "type": "ha-entity",
        "name": "TGE Current Price",
        "server": "home_assistant",
        "version": 2,
        "entityId": "sensor.tge_rdn_current_price",
        "outputs": 1,
        "outputProperties": [
            {
                "property": "payload",
                "propertyType": "msg",
                "value": "",
                "valueType": "entityState"
            }
        ]
    },
    {
        "id": "price_decision",
        "type": "switch",
        "name": "Cena Decision",
        "property": "payload",
        "rules": [
            {
                "t": "lt",
                "v": "300",
                "vt": "num"
            },
            {
                "t": "gte", 
                "v": "300",
                "vt": "num"
            }
        ]
    }
]
```

## 7. Dostosowana konfiguracja jednostek

```yaml
# configuration.yaml
tge_rdn:
  - name: "TGE RDN PLN/kWh"
    unit: "PLN/kWh"
    template: "{{ (value / 1000) | round(4) }}"

  - name: "TGE RDN EUR/kWh"  
    unit: "EUR/kWh"
    template: "{{ (value / 4300) | round(4) }}"  # Przyjmując kurs 4.3
```

## 8. Integracja z panelem energii

```yaml
# configuration.yaml
homeassistant:
  customize:
    sensor.tge_rdn_current_price:
      friendly_name: "Cena energii TGE RDN"
      icon: mdi:flash
      unit_of_measurement: "PLN/MWh"
      device_class: monetary
```
