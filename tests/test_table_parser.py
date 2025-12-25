"""Test script to extract TGE prices from the HTML table."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def parse_tge_table(date_filter=None):
    """
    Parse TGE RDN table from web page.
    
    Args:
        date_filter: datetime object or None. If provided, filters data for this date.
        
    Returns:
        dict: Hourly price data for the requested date(s)
    """
    url = "https://tge.pl/energia-elektryczna-rdn"
    
    print(f"🔍 Fetching {url}...")
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main table
        table = soup.find('table', {'id': 'rdn'})
        if not table:
            table = soup.find('table', class_='table-rdb')
        
        if not table:
            print("❌ Could not find price table")
            return None
        
        print(f"✅ Found price table")
        
        # Parse rows
        rows = table.find_all('tr')
        
        # Group data by date
        data_by_date = {}
        
        for row in rows[2:]:  # Skip header rows
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            
            # First cell contains date and hour: "2025-11-22_H01" or "2025-11-22_Q00:15"
            date_hour_text = cells[0].get_text(strip=True)
            
            # Skip quarter-hour entries (Q00:15, Q00:30, etc.)
            if '_Q' in date_hour_text:
                continue
            
            # Parse date and hour
            # Format: 2025-11-22_H01
            match = re.match(r'(\d{4}-\d{2}-\d{2})_H(\d{2})([a-z]?)', date_hour_text)
            if not match:
                continue
            
            date_str = match.group(1)
            hour_num = int(match.group(2))
            dst_marker = match.group(3)  # 'a' or 'b' for DST changes
            
            # Parse price from "Kurs jednolity [PLN/MWh]" or weighted average
            # This is typically in column 7 or 13 (Fixing II "Kurs jednolity [PLN/MWh]")
            # If Fixing II is empty, try weighted average from continuous trading
            
            price = None
            
            # Try Fixing II price (column index ~7)
            if len(cells) > 7:
                price_text = cells[7].get_text(strip=True)
                if price_text and price_text != '-':
                    # Replace comma with dot for float conversion
                    price_text = price_text.replace(',', '.').replace(' ', '')
                    try:
                        price = float(price_text)
                    except ValueError:
                        pass
            
            # If no Fixing II price, try weighted average from all trading
            if price is None and len(cells) > 13:
                price_text = cells[13].get_text(strip=True)
                if price_text and price_text != '-':
                    price_text = price_text.replace(',', '.').replace(' ', '')
                    try:
                        price = float(price_text)
                    except ValueError:
                        pass
            
            # If still no price, try continuous trading weighted average (column ~4)
            if price is None and len(cells) > 4:
                price_text = cells[4].get_text(strip=True)
                if price_text and price_text != '-':
                    price_text = price_text.replace(',', '.').replace(' ', '')
                    try:
                        price = float(price_text)
                    except ValueError:
                        pass
            
            if price is None:
                # Skip rows without price
                continue
            
            # Create date object
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Initialize date in dict if not exists
            if date_str not in data_by_date:
                data_by_date[date_str] = {
                    'date': date_str,
                    'date_obj': date_obj,
                    'hourly_data': []
                }
            
            # Add hourly data
            hour_datetime = date_obj.replace(
                hour=hour_num - 1,  # H01 = 00:00-01:00
                minute=0,
                second=0,
                microsecond=0
            )
            
            data_by_date[date_str]['hourly_data'].append({
                'time': hour_datetime.isoformat(),
                'hour': hour_num,
                'price': price,
                'is_negative': price < 0,
                'dst_marker': dst_marker
            })
        
        # Calculate statistics for each date
        for date_str, date_data in data_by_date.items():
            hourly_data = date_data['hourly_data']
            
            # Sort by hour
            hourly_data.sort(key=lambda x: x['hour'])
            
            prices = [item['price'] for item in hourly_data]
            
            date_data['average_price'] = sum(prices) / len(prices) if prices else 0
            date_data['min_price'] = min(prices) if prices else 0
            date_data['max_price'] = max(prices) if prices else 0
            date_data['total_hours'] = len(hourly_data)
            date_data['negative_hours'] = sum(1 for p in prices if p < 0)
        
        # Filter by date if requested
        if date_filter:
            target_date_str = date_filter.strftime('%Y-%m-%d')
            if target_date_str in data_by_date:
                return data_by_date[target_date_str]
            else:
                print(f"⚠️ No data for {target_date_str}")
                return None
        
        return data_by_date
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_parser():
    """Test the parser."""
    print("=" * 60)
    print("Testing TGE Price Parser")
    print("=" * 60)
    
    # Get all available data
    all_data = parse_tge_table()
    
    if all_data:
        print(f"\n✅ Found data for {len(all_data)} date(s):")
        for date_str, data in sorted(all_data.items()):
            print(f"\n📅 {date_str}:")
            print(f"   Hours: {data['total_hours']}")
            print(f"   Average: {data['average_price']:.2f} PLN/MWh")
            print(f"   Min: {data['min_price']:.2f} PLN/MWh")
            print(f"   Max: {data['max_price']:.2f} PLN/MWh")
            print(f"   Negative hours: {data['negative_hours']}")
            
            # Show first 3 hours
            print(f"   First 3 hours:")
            for hour_data in data['hourly_data'][:3]:
                print(f"      H{hour_data['hour']:02d}: {hour_data['price']:.2f} PLN/MWh")
    
    # Test filtering for today
    print("\n" + "=" * 60)
    print("Testing date filter (today)")
    print("=" * 60)
    
    today_data = parse_tge_table(datetime.now())
    if today_data:
        print(f"\n✅ Today's data:")
        print(f"   Date: {today_data['date']}")
        print(f"   Hours: {today_data['total_hours']}")
        print(f"   Average: {today_data['average_price']:.2f} PLN/MWh")
    else:
        print("⚠️ No data for today yet")
    
    # Test filtering for tomorrow
    print("\n" + "=" * 60)
    print("Testing date filter (tomorrow)")
    print("=" * 60)
    
    tomorrow_data = parse_tge_table(datetime.now() + timedelta(days=1))
    if tomorrow_data:
        print(f"\n✅ Tomorrow's data:")
        print(f"   Date: {tomorrow_data['date']}")
        print(f"   Hours: {tomorrow_data['total_hours']}")
        print(f"   Average: {tomorrow_data['average_price']:.2f} PLN/MWh")
    else:
        print("⚠️ No data for tomorrow yet")

if __name__ == "__main__":
    test_parser()
