"""Test the corrected TGE integration with date-specific URLs."""
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
        # IMPORTANT: The TGE website shows prices for the NEXT day after dateShow parameter
        # To get prices for date X, we need to request dateShow=X-1 (previous day)
        previous_day = target_date - timedelta(days=1)
        date_param = previous_day.strftime("%d-%m-%Y")
        url_with_date = f"{TGE_PAGE_URL}?dateShow={date_param}"
        
        print(f"🔍 Fetching: {url_with_date} (for data of {date_str})")

        response = requests.get(url_with_date, timeout=30, headers={
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

def check_working_day():
    """Check if today is a working day."""
    from datetime import date
    
    def is_holiday(d: date) -> bool:
        """Check if Polish holiday."""
        fixed = [(1,1),(1,6),(5,1),(5,3),(8,15),(11,1),(11,11),(12,25),(12,26)]
        if (d.month, d.day) in fixed:
            return True
        
        # Easter calculation
        y = d.year
        a=y%19; b=y//100; c=y%100; d_=b//4; e=b%4
        f=(b+8)//25; g=(b-f+1)//3; h=(19*a+b-d_-g+15)%30
        i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7
        m=(a+11*h+22*l)//451; mon=(h+l-7*m+114)//31
        day=((h+l-7*m+114)%31)+1
        easter = date(y, mon, day)
        
        moveable = [easter, easter+timedelta(1), easter+timedelta(49), easter+timedelta(60)]
        return d in moveable
    
    today = datetime.now().date()
    is_weekend = today.weekday() in (5, 6)
    is_hol = is_holiday(today)
    is_working = not (is_weekend or is_hol)
    
    print(f"\n📅 Today: {today} ({['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][today.weekday()]})")
    print(f"   Weekend: {is_weekend}")
    print(f"   Holiday: {is_hol}")
    print(f"   Working day: {is_working}")
    
    return is_working

def test_corrected_integration():
    """Test the corrected integration."""
    print("=" * 70)
    print("Testing TGE RDN Integration - Date-Specific URLs")
    print("=" * 70)
    
    # Test for today (Nov 21, 2025)
    today = datetime.now()
    print(f"\n📅 Testing TODAY ({today.date()})...")
    today_data = parse_html_table_for_date(today)
    
    if today_data:
        print(f"\n✅ TODAY's data successfully fetched!")
        print(f"   Date: {today_data['date']}")
        print(f"   Total hours: {today_data['total_hours']}")
        print(f"   Average price: {today_data['average_price']:.2f} PLN/MWh")
        print(f"   Min: {today_data['min_price']:.2f} PLN/MWh")
        print(f"   Max: {today_data['max_price']:.2f} PLN/MWh")
        print(f"\n   First 3 hours:")
        for h in today_data['hourly_data'][:3]:
            print(f"      H{h['hour']:02d}: {h['price']:.2f} PLN/MWh")
    else:
        print(f"\n❌ No data for today")
    
    # Test for tomorrow (Nov 22, 2025)
    tomorrow = today + timedelta(days=1)
    print(f"\n📅 Testing TOMORROW ({tomorrow.date()})...")
    tomorrow_data = parse_html_table_for_date(tomorrow)
    
    if tomorrow_data:
        print(f"\n✅ TOMORROW's data successfully fetched!")
        print(f"   Date: {tomorrow_data['date']}")
        print(f"   Total hours: {tomorrow_data['total_hours']}")
        print(f"   Average price: {tomorrow_data['average_price']:.2f} PLN/MWh")
        print(f"   Min: {tomorrow_data['min_price']:.2f} PLN/MWh")
        print(f"   Max: {tomorrow_data['max_price']:.2f} PLN/MWh")
        print(f"\n   First 3 hours:")
        for h in tomorrow_data['hourly_data'][:3]:
            print(f"      H{h['hour']:02d}: {h['price']:.2f} PLN/MWh")
    else:
        print(f"\n❌ No data for tomorrow")
    
    # Test working day attribute
    is_working = check_working_day()
    
    print("\n" + "=" * 70)
    if today_data and tomorrow_data:
        print("✅ ALL TESTS PASSED!")
        print(f"   Today: {today_data['total_hours']} hours")
        print(f"   Tomorrow: {tomorrow_data['total_hours']} hours")
        print(f"   Is working day: {is_working}")
    elif today_data:
        print("⚠️ Only today's data available")
    elif tomorrow_data:
        print("⚠️ Only tomorrow's data available")
    else:
        print("❌ No data available")
    print("=" * 70)

if __name__ == "__main__":
    test_corrected_integration()
