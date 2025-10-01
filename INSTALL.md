# Przewodnik instalacji TGE RDN

## Wymagania systemowe

- Home Assistant 2023.1 lub nowszy
- Python 3.9+
- Dostęp do internetu

## Krok po kroku

### 1. Instalacja przez HACS

1. **Otwórz HACS**
   - Przejdź do HACS w Home Assistant
   - Kliknij na "Integracje"

2. **Dodaj repozytorium**
   - Kliknij menu (...) w prawym górnym rogu
   - Wybierz "Custom repositories"
   - URL: `https://github.com/twoj-username/tge-rdn-integration`
   - Kategoria: "Integration"

3. **Zainstaluj integrację**
   - Wyszukaj "TGE RDN"  
   - Kliknij "Pobierz"
   - Restartuj Home Assistant

### 2. Instalacja ręczna

```bash
cd /config
mkdir -p custom_components
cd custom_components
git clone https://github.com/twoj-username/tge-rdn-integration tge_rdn
# lub rozpakuj archiwum ZIP
```

### 3. Konfiguracja integracji

1. **Dodaj integrację**
   - Idź do Konfiguracja → Integracje
   - Kliknij "+ Dodaj integrację"
   - Wyszukaj "TGE RDN"

2. **Podstawowa konfiguracja**
   - Nazwa: `TGE RDN` (domyślnie)
   - Kliknij "Prześlij"

3. **Opcje (opcjonalne)**
   - Jednostka: PLN/MWh, PLN/kWh, EUR/MWh, EUR/kWh
   - Template Jinja2: np. `{{ value | round(2) }}`

## Rozwiązywanie problemów

### Błąd: "Cannot connect to TGE server"

**Przyczyny:**
- Brak połączenia internetowego
- Serwery TGE niedostępne
- Plik dla danej daty jeszcze nie opublikowany

**Rozwiązania:**
1. Sprawdź połączenie internetowe
2. Sprawdź logi: `tail -f /config/home-assistant.log | grep tge_rdn`
3. Pliki TGE są publikowane po 11:05 (fixing I) i 13:20 (fixing II)

### Błąd: "Error parsing Excel data"

**Przyczyny:**
- Zmiana formatu pliku Excel przez TGE
- Uszkodzony plik podczas pobierania

**Rozwiązania:**
1. Sprawdź czy plik można pobrać ręcznie z TGE
2. Poczekaj kilka minut i spróbuj ponownie
3. Zgłoś problem z logami

### Sensor pokazuje "Unknown" lub "Unavailable"

**Przyczyny:**
- Pierwsze uruchomienie (brak danych)
- Błąd parsowania danych
- Problemy z harmonogramem aktualizacji

**Rozwiązania:**
1. Poczekaj na następną aktualizację (max 1h)
2. Ręcznie wywołaj aktualizację w Developer Tools
3. Sprawdź czy aktualny czas mieści się w godzinach publikacji TGE

### Brak danych na jutro

**To normalne!** Dane na następny dzień są publikowane dopiero po 15:00.

### Wysokie zużycie pamięci

Integracja przechowuje dane godzinowe na 2 dni (48 rekordów). To nie powinno wpłynąć na wydajność HA.

## Testowanie instalacji

Uruchom test:
```bash
cd /config/custom_components/tge_rdn
python3 test.py
```

Oczekiwany wynik:
```
=== TGE RDN Integration Test ===
Testing URL: https://www.tge.pl/pub/TGE/SDAC%202025/RDN/...
✓ File downloaded successfully
✓ Excel parsed, shape: (132, 29)
✓ Found 24 hourly price records

Test result: PASSED
```

## Logi i debugowanie

### Włącz szczegółowe logowanie

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.tge_rdn: debug
```

### Przydatne polecenia

```bash
# Sprawdź logi integracji
grep "tge_rdn" /config/home-assistant.log

# Sprawdź czy pliki TGE są dostępne dzisiaj
curl -I "https://www.tge.pl/pub/TGE/SDAC%202025/RDN/Raport_RDN_dzie_dostawy_delivery_day_$(date +%Y_%m_%d).xlsx"

# Test parsowania w Python
python3 -c "
import pandas as pd
import requests
from datetime import datetime
url = 'https://www.tge.pl/pub/TGE/SDAC%202025/RDN/Raport_RDN_dzie_dostawy_delivery_day_$(date +%Y_%m_%d).xlsx'
r = requests.get(url)
df = pd.read_excel(r.content, sheet_name='WYNIKI', header=None)
print(f'Shape: {df.shape}')
print(f'Column I samples: {df[8][10:15].tolist()}')
print(f'Column K samples: {df[10][10:15].tolist()}')
"
```

## Kontakt

W przypadku problemów:
1. Sprawdź [Issues na GitHub](https://github.com/user/repo/issues)
2. Załącz logi z Home Assistant
3. Podaj wersję HA i detale konfiguracji
