"""Debug script to see what dates are in the table."""
import requests
from bs4 import BeautifulSoup

def check_table_dates(url):
    """Check what dates are in the table."""
    print(f"Fetching: {url}")
    
    response = requests.get(url, timeout=30, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'id': 'rdn'})
    if not table:
        table = soup.find('table', class_='table-rdb')
    
    if not table:
        print("No table found")
        return
    
    rows = table.find_all('tr')
    print(f"\nFound {len(rows)} rows")
    
    dates_found = set()
    
    for i, row in enumerate(rows[:30]):  # Check first 30 rows
        cells = row.find_all('td')
        if cells and len(cells) > 0:
            first_cell = cells[0].get_text(strip=True)
            print(f"Row {i}: '{first_cell}'")
            if '_H' in first_cell or '_Q' in first_cell:
                # Extract date part
                date_part = first_cell.split('_')[0]
                dates_found.add(date_part)
    
    print(f"\n\nDates found in table: {sorted(dates_found)}")

# Test different URLs
print("=" * 70)
print("Testing URL WITHOUT date parameter")
print("=" * 70)
check_table_dates("https://tge.pl/energia-elektryczna-rdn")

print("\n\n" + "=" * 70)
print("Testing URL WITH dateShow=21-11-2025")
print("=" * 70)
check_table_dates("https://tge.pl/energia-elektryczna-rdn?dateShow=21-11-2025")

print("\n\n" + "=" * 70)
print("Testing URL WITH dateShow=22-11-2025")
print("=" * 70)
check_table_dates("https://tge.pl/energia-elektryczna-rdn?dateShow=22-11-2025")
