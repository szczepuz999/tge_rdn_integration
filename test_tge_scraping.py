"""Test script to analyze TGE website structure."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

def analyze_tge_page():
    """Analyze the HTML structure of TGE page."""
    url = "https://tge.pl/energia-elektryczna-rdn"
    
    print(f"🔍 Fetching {url}...")
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return
        
        print(f"✅ Page loaded ({len(response.content)} bytes)")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all tables
        tables = soup.find_all('table')
        print(f"\n📊 Found {len(tables)} table(s)")
        
        for idx, table in enumerate(tables):
            print(f"\n=== Table {idx + 1} ===")
            
            # Get table headers
            headers = []
            header_rows = table.find_all('th')
            if header_rows:
                headers = [th.get_text(strip=True) for th in header_rows]
                print(f"Headers: {headers}")
            
            # Get first few rows
            rows = table.find_all('tr')
            print(f"Total rows: {len(rows)}")
            
            print("\nFirst 5 rows:")
            for i, row in enumerate(rows[:5]):
                cells = row.find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                print(f"  Row {i+1}: {cell_texts}")
            
            # Check for table classes/ids
            if table.get('class'):
                print(f"Table classes: {table.get('class')}")
            if table.get('id'):
                print(f"Table ID: {table.get('id')}")
        
        # Look for price data patterns
        print("\n\n🔍 Searching for price patterns...")
        text = soup.get_text()
        
        # Look for common patterns
        if 'PLN/MWh' in text:
            print("✅ Found 'PLN/MWh' in page")
        if 'EUR/MWh' in text:
            print("✅ Found 'EUR/MWh' in page")
        
        # Look for date patterns
        import re
        date_patterns = re.findall(r'\d{2}[-/\.]\d{2}[-/\.]\d{4}', text)
        if date_patterns:
            print(f"✅ Found date patterns: {date_patterns[:5]}")
        
        # Look for hour patterns (H01, H02, etc.)
        hour_patterns = re.findall(r'H\d{2}', text)
        if hour_patterns:
            print(f"✅ Found hour patterns: {set(hour_patterns)}")
        
        # Save a sample of the HTML
        print(f"\n💾 Saving HTML sample to 'tge_page_sample.html'")
        with open('tge_page_sample.html', 'w', encoding='utf-8') as f:
            f.write(response.text[:50000])  # First 50KB
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_tge_page()
