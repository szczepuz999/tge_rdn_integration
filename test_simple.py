"""Simple test of the HTML table parsing function."""
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

TGE_PAGE_URL = "https://tge.pl/energia-elektryczna-rdn"

def parse_html_table_for_date(target_date: datetime) -> Optional[Dict[str, Any]]:
    """Parse TGE HTML table to extract price data for specific date."""
    try:
        date_str = target_date.strftime("%Y-%m-%d")
        print(f"🔍 Fetching table data for: {date_str}")

        response = requests.get(TGE_PAGE_URL, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if response.status_code != 200:
            print(f"Failed to access TGE page: HTTP {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main table
        table = soup.find('table', {'id': 'rdn'})
        if not table:
            table = soup.find('table', class_='table-rdb')
        
        if not table:
            print("Could not find price table")
            return None
        
        # Parse rows
        rows = table.find_all('tr')
        hourly_data = []
        negative_hours = 0
        
        for row in rows[2:]:  # Skip header rows
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            
            # First cell contains date and hour: "2025-11-22_H01"
            date_hour_text = cells[0].get_text(strip=True)
            
            # Skip quarter-hour entries
            if '_Q' in date_hour_text:
                continue
            
            # Parse date and hour: format 2025-11-22_H01 or 2025-11-22_H02a
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
            
            # Try Fixing II price (column ~7)
            if len(cells) > 7:
                price_text = cells[7].get_text(strip=True)
                if price_text and price_text != '-':
                    price_text = price_text.replace(',', '.').replace(' ', '')
                    try:
                        price = float(price_text)
                    except ValueError:
                        pass
            
            # If no Fixing II, try weighted average from all trading (column ~13)
            if price is None and len(cells) > 13:
                price_text = cells[13].get_text(strip=True)
                if price_text and price_text != '-':
                    price_text = price_text.replace(',', '.').replace(' ', '')
                    try:
                        price = float(price_text)
                    except ValueError:
                        pass
            
            # If still no price, try continuous trading (column ~4)
            if price is None and len(cells) > 4:
                price_text = cells[4].get_text(strip=True)
                if price_text and price_text != '-':
                    price_text = price_text.replace(',', '.').replace(' ', '')
                    try:
                        price = float(price_text)
                    except ValueError:
                        pass
            
            if price is None:
                continue
            
            if price < 0:
                negative_hours += 1
            
            hour_datetime = target_date.replace(
                hour=hour_num - 1,  # H01 = 00:00-01:00
                minute=0,
                second=0,
                microsecond=0
            )
            
            hourly_data.append({
                'time': hour_datetime.isoformat(),
                'hour': hour_num,
                'price': price,
                'is_negative': price < 0,
                'dst_marker': dst_marker
            })
        
        if not hourly_data:
            print(f"No data for {date_str}")
            return None
        
        # Sort by hour
        hourly_data.sort(key=lambda x: x['hour'])
        
        # Calculate statistics
        prices = [item['price'] for item in hourly_data]
        
        result = {
            "date": target_date.date().isoformat(),
            "hourly_data": hourly_data,
            "average_price": sum(prices) / len(prices) if prices else 0,
            "min_price": min(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
            "total_hours": len(hourly_data),
            "negative_hours": negative_hours,
        }
        
        print(f"✅ Found {len(hourly_data)} hours for {date_str}")
        return result
        
    except Exception as e:
        print(f"Error parsing table for {target_date.date()}: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_integration():
    """Test the integration functionality."""
    print("=" * 70)
    print("Testing TGE RDN Integration v1.8.0 - Web Table Parsing")
    print("=" * 70)
    
    # Test for tomorrow
    tomorrow = datetime.now() + timedelta(days=1)
    print(f"\n📅 Testing data fetch for {tomorrow.date()}...")
    
    result = parse_html_table_for_date(tomorrow)
    
    if result:
        print(f"\n✅ Successfully fetched data!")
        print(f"   Date: {result['date']}")
        print(f"   Total hours: {result['total_hours']}")
        print(f"   Average price: {result['average_price']:.2f} PLN/MWh")
        print(f"   Min price: {result['min_price']:.2f} PLN/MWh")
        print(f"   Max price: {result['max_price']:.2f} PLN/MWh")
        print(f"   Negative hours: {result['negative_hours']}")
        
        print(f"\n📊 First 5 hours:")
        for i, hour_data in enumerate(result['hourly_data'][:5], 1):
            print(f"   {i}. H{hour_data['hour']:02d}: {hour_data['price']:.2f} PLN/MWh")
        
        # Calculate a sample price with fees
        print(f"\n💰 Sample Price Calculation (H{result['hourly_data'][0]['hour']:02d}):")
        raw_price = result['hourly_data'][0]['price']
        vat_rate = 0.23
        fee = 2.0
        dist = 80.0
        
        price_with_vat = raw_price * (1 + vat_rate)
        total_pln_mwh = price_with_vat + fee + dist
        total_pln_kwh = total_pln_mwh / 1000
        
        print(f"   Base price (TGE): {raw_price:.2f} PLN/MWh")
        print(f"   With VAT (23%): {price_with_vat:.2f} PLN/MWh")
        print(f"   + Exchange fee: {fee:.2f} PLN/MWh")
        print(f"   + Distribution: {dist:.2f} PLN/MWh")
        print(f"   Total: {total_pln_mwh:.2f} PLN/MWh = {total_pln_kwh:.4f} PLN/kWh")
        
        print("\n" + "=" * 70)
        print("✅ Integration test PASSED!")
        print("=" * 70)
        return True
    else:
        print(f"\n⚠️ No data for tomorrow, trying today...")
        today = datetime.now()
        result = parse_html_table_for_date(today)
        
        if result:
            print(f"\n✅ Found today's data!")
            print(f"   Date: {result['date']}")
            print(f"   Total hours: {result['total_hours']}")
            print(f"   Average: {result['average_price']:.2f} PLN/MWh")
            print("\n✅ Integration test PASSED (with today's data)")
            return True
        else:
            print("\n❌ No data available")
            return False

if __name__ == "__main__":
    test_integration()
