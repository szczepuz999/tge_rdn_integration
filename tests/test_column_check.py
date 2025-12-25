import requests
from bs4 import BeautifulSoup

response = requests.get('https://tge.pl/energia-elektryczna-rdn?dateShow=20-11-2025', timeout=30, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

soup = BeautifulSoup(response.text, 'html.parser')
table = soup.find('table', {'id': 'rdn'})

rows = table.find_all('tr')
for row in rows[2:]:
    cells = row.find_all('td')
    if len(cells) > 0:
        date_hour = cells[0].get_text(strip=True)
        if 'H03' in date_hour and '2025-11-20' in date_hour:
            print(f'H03 (2025-11-20):')
            print(f'  Fixing I (col 2): {cells[2].get_text(strip=True)}')
            print(f'  Fixing II (col 7): {cells[7].get_text(strip=True)}')
            print(f'  Weighted avg (col 13): {cells[13].get_text(strip=True)}')
            break
