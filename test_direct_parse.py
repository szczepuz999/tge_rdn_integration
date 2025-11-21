"""Direct test of the parsing function to verify Fixing I is used."""
import sys
import os
from datetime import datetime

# Add custom_components to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'tge_rdn'))

# Import the actual parsing method
import requests
from bs4 import BeautifulSoup
import re

def parse_html_table_for_date(target_date: datetime):
    """Copy of the actual parsing function to test."""
    try:
        date_str = target_date.strftime("%Y-%m-%d")
        
        # Use previous day for URL parameter (TGE shows next day's data)
        from datetime import timedelta
        previous_day = target_date - timedelta(days=1)
        date_param = previous_day.strftime("%d-%m-%Y")
        url_with_date = f"https://tge.pl/energia-elektryczna-rdn?dateShow={date_param}"
        
        print(f"🔍 Fetching: {url_with_date}")
        print(f"   Expected data for: {date_str}")
        
        response = requests.get(url_with_date, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'rdn'})
        
        if not table:
            print("❌ Table not found")
            return None
        
        rows = table.find_all('tr')
        hourly_data = []
        
        for row in rows[2:]:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            
            date_hour_text = cells[0].get_text(strip=True)
            
            # Skip quarter-hour entries
            if '_Q' in date_hour_text:
                continue
            
            # Parse date and hour
            match = re.match(r'(\d{4}-\d{2}-\d{2})_H(\d{2})([a-z]?)', date_hour_text)
            if not match:
                continue
            
            row_date_str = match.group(1)
            hour_num = int(match.group(2))
            dst_marker = match.group(3)
            
            # Only process rows for target date
            if row_date_str != date_str:
                continue
            
            # Parse price - try multiple columns
            price = None
            source_column = None
            
            # Try Fixing I price (column 2) - PRIMARY SOURCE
            if len(cells) > 2:
                price_text = cells[2].get_text(strip=True)
                if price_text and price_text != '-':
                    price_text = price_text.replace(',', '.').replace(' ', '')
                    try:
                        price = float(price_text)
                        source_column = "Fixing I (col 2)"
                    except ValueError:
                        pass
            
            # If no Fixing I, try Fixing II price (column 7)
            if price is None and len(cells) > 7:
                price_text = cells[7].get_text(strip=True)
                if price_text and price_text != '-':
                    price_text = price_text.replace(',', '.').replace(' ', '')
                    try:
                        price = float(price_text)
                        source_column = "Fixing II (col 7)"
                    except ValueError:
                        pass
            
            # If still no price, try weighted average
            if price is None and len(cells) > 13:
                price_text = cells[13].get_text(strip=True)
                if price_text and price_text != '-':
                    price_text = price_text.replace(',', '.').replace(' ', '')
                    try:
                        price = float(price_text)
                        source_column = "Weighted Avg (col 13)"
                    except ValueError:
                        pass
            
            if price is None:
                continue
            
            hourly_data.append({
                'hour': hour_num,
                'price': price,
                'source': source_column
            })
        
        return hourly_data
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Test for today (Nov 21, 2025)
print("=" * 70)
print("Testing Fixing I Column Usage")
print("=" * 70)

today = datetime(2025, 11, 21)
data = parse_html_table_for_date(today)

if data:
    print(f"\n✅ Found {len(data)} hours\n")
    
    # Show first 5 hours
    print("First 5 hours:")
    for item in data[:5]:
        print(f"  H{item['hour']:02d}: {item['price']:8.2f} PLN/MWh (from {item['source']})")
    
    # Check H03 specifically
    h03 = next((item for item in data if item['hour'] == 3), None)
    if h03:
        print(f"\n📊 H03 Details:")
        print(f"   Price: {h03['price']} PLN/MWh")
        print(f"   Source: {h03['source']}")
        
        if abs(h03['price'] - 420.90) < 0.01:
            print(f"   ✅ CORRECT! Using Fixing I (expected 420.90)")
        elif abs(h03['price'] - 383.08) < 0.01:
            print(f"   ❌ WRONG! Using Fixing II (383.08 instead of 420.90)")
        else:
            print(f"   ⚠️  Unexpected value")
    
    # Count sources
    source_count = {}
    for item in data:
        source = item['source']
        source_count[source] = source_count.get(source, 0) + 1
    
    print(f"\n📈 Source Distribution:")
    for source, count in source_count.items():
        print(f"   {source}: {count} hours")

else:
    print("❌ No data returned")
