"""Find H03 in the already fetched data."""
import requests
from bs4 import BeautifulSoup

url = "https://tge.pl/energia-elektryczna-rdn?dateShow=20-11-2025"

response = requests.get(url, timeout=30, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

soup = BeautifulSoup(response.text, 'html.parser')
table = soup.find('table', {'id': 'rdn'})

rows = table.find_all('tr')

print("Looking for H03:")

for idx, row in enumerate(rows[2:]):
    cells = row.find_all('td')
    if len(cells) > 0:
        date_hour = cells[0].get_text(strip=True)
        if 'H03' in date_hour and '_Q' not in date_hour:
            col2 = cells[2].get_text(strip=True) if len(cells) > 2 else '-'
            col7 = cells[7].get_text(strip=True) if len(cells) > 7 else '-'
            print(f"\n✅ Found: {date_hour}")
            print(f"   Fixing I (col 2): {col2}")
            print(f"   Fixing II (col 7): {col7}")
            
            # Parse value
            if col2 != '-':
                value = float(col2.replace(',', '.'))
                print(f"   Fixing I value: {value} PLN/MWh")
                if abs(value - 420.90) < 0.01:
                    print("   🎉 This matches expected value 420.90!")
