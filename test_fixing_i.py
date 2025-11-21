"""Test that Fixing I column is used correctly."""
import requests
from bs4 import BeautifulSoup
import re

def test_fixing_i_column():
    """Verify we're using Fixing I (column 2) not Fixing II (column 7)."""
    
    url = "https://tge.pl/energia-elektryczna-rdn?dateShow=20-11-2025"
    
    response = requests.get(url, timeout=30, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'id': 'rdn'})
    
    if not table:
        print("❌ Table not found")
        return
    
    # Get headers
    header_rows = table.find_all('tr')[:2]
    print("📋 Table Structure:")
    print("  Row 0 (main headers):")
    for idx, th in enumerate(header_rows[0].find_all(['th', 'td'])):
        colspan = th.get('colspan', '1')
        text = th.get_text(strip=True)
        if text:
            print(f"    Col {idx} (colspan={colspan}): {text}")
    
    print("\n  Row 1 (sub-headers):")
    for idx, th in enumerate(header_rows[1].find_all(['th', 'td'])):
        text = th.get_text(strip=True)[:40]
        if 'Kurs' in text or 'PLN' in text:
            print(f"    Col {idx}: {text}")
    
    # Find H03 row for 2025-11-20
    print("\n🔍 Looking for H03 (2025-11-20)...")
    rows = table.find_all('tr')
    
    for row in rows[2:]:  # Skip header rows
        cells = row.find_all('td')
        if len(cells) < 3:
            continue
        
        date_hour = cells[0].get_text(strip=True)
        
        # Match H03 for date 2025-11-20
        match = re.match(r'(\d{4}-\d{2}-\d{2})_H(\d{2})', date_hour)
        if match and match.group(1) == '2025-11-20' and match.group(2) == '03':
            print(f"\n✅ Found: {date_hour}")
            
            # Get prices from different columns
            fixing_i = cells[2].get_text(strip=True) if len(cells) > 2 else '-'
            fixing_ii = cells[7].get_text(strip=True) if len(cells) > 7 else '-'
            weighted_avg = cells[13].get_text(strip=True) if len(cells) > 13 else '-'
            
            print(f"\n📊 H03 Prices:")
            print(f"  Fixing I (col 2):    {fixing_i} PLN/MWh")
            print(f"  Fixing II (col 7):   {fixing_ii} PLN/MWh")
            print(f"  Weighted (col 13):   {weighted_avg} PLN/MWh")
            
            # Convert and verify
            if fixing_i and fixing_i != '-':
                fixing_i_value = float(fixing_i.replace(',', '.'))
                print(f"\n✅ Fixing I parsed: {fixing_i_value} PLN/MWh")
                
                if abs(fixing_i_value - 420.90) < 0.01:
                    print("🎉 SUCCESS! Fixing I column contains expected value (420.90)")
                else:
                    print(f"⚠️  Fixing I value is {fixing_i_value}, expected ~420.90")
            
            break
    else:
        print("❌ H03 row not found")

if __name__ == "__main__":
    test_fixing_i_column()
