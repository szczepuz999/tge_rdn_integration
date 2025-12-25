"""Check what data is in the table."""
import requests
from bs4 import BeautifulSoup
import re

url = "https://tge.pl/energia-elektryczna-rdn?dateShow=20-11-2025"

response = requests.get(url, timeout=30, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

soup = BeautifulSoup(response.text, 'html.parser')
table = soup.find('table', {'id': 'rdn'})

rows = table.find_all('tr')

print(f"Total rows: {len(rows)}")
print("\nFirst 10 data rows:")

for idx, row in enumerate(rows[2:12]):
    cells = row.find_all('td')
    if len(cells) > 0:
        date_hour = cells[0].get_text(strip=True)
        col2 = cells[2].get_text(strip=True) if len(cells) > 2 else '-'
        col7 = cells[7].get_text(strip=True) if len(cells) > 7 else '-'
        print(f"{idx}: {date_hour:25s} | Fixing I: {col2:10s} | Fixing II: {col7}")
