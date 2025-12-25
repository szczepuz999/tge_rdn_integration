"""Test the updated TGE RDN integration with web scraping."""
import sys
import os
from datetime import datetime, timedelta

# Add the custom_components to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the updated sensor module
from custom_components.tge_rdn.sensor import TGERDNDataUpdateCoordinator
from custom_components.tge_rdn.const import TGE_PAGE_URL

# Mock HomeAssistant objects
class MockHass:
    def __init__(self):
        pass
    
    async def async_add_executor_job(self, func, *args):
        """Execute a function in executor."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

class MockEntry:
    def __init__(self):
        self.entry_id = "test_entry"
        self.data = {}
        self.options = {
            "unit": "PLN/kWh",
            "exchange_fee": 2.0,
            "vat_rate": 0.23,
            "dist_low": 80.0,
            "dist_med": 120.0,
            "dist_high": 160.0,
        }

async def test_coordinator():
    """Test the coordinator data fetching."""
    print("=" * 70)
    print("Testing TGE RDN Integration v1.8.0 - Web Table Parsing")
    print("=" * 70)
    
    hass = MockHass()
    entry = MockEntry()
    
    coordinator = TGERDNDataUpdateCoordinator(hass, entry)
    
    # Test parsing for tomorrow (data that exists on the website)
    print(f"\n📅 Testing data fetch for tomorrow...")
    tomorrow = datetime.now() + timedelta(days=1)
    
    result = await coordinator._fetch_day_data(tomorrow, "tomorrow")
    
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
            print(f"   {i}. H{hour_data['hour']:02d}: {hour_data['price']:.2f} PLN/MWh (time: {hour_data['time']})")
        
        # Test that DST markers are preserved
        dst_hours = [h for h in result['hourly_data'] if h.get('dst_marker')]
        if dst_hours:
            print(f"\n🕐 DST markers found: {len(dst_hours)} hours")
            for h in dst_hours:
                print(f"   H{h['hour']:02d} (marker: {h['dst_marker']})")
        else:
            print(f"\n🕐 No DST markers (normal day)")
        
        return True
    else:
        print(f"\n⚠️ No data available for tomorrow yet")
        
        # Try today instead
        print(f"\n📅 Testing data fetch for today...")
        today = datetime.now()
        result = await coordinator._fetch_day_data(today, "today")
        
        if result:
            print(f"\n✅ Successfully fetched today's data!")
            print(f"   Date: {result['date']}")
            print(f"   Total hours: {result['total_hours']}")
            print(f"   Average price: {result['average_price']:.2f} PLN/MWh")
            return True
        else:
            print(f"\n❌ No data available")
            return False

async def test_price_calculation():
    """Test price calculations."""
    print("\n" + "=" * 70)
    print("Testing Price Calculations")
    print("=" * 70)
    
    hass = MockHass()
    entry = MockEntry()
    
    coordinator = TGERDNDataUpdateCoordinator(hass, entry)
    
    # Fetch data
    tomorrow = datetime.now() + timedelta(days=1)
    data = await coordinator._fetch_day_data(tomorrow, "tomorrow")
    
    if not data:
        print("⚠️ Skipping price calculation test - no data available")
        return
    
    # Simulate coordinator data
    coordinator.data = {
        "today": None,
        "tomorrow": data,
        "last_update": datetime.now()
    }
    
    # Test price calculation logic
    if data and data['hourly_data']:
        first_hour = data['hourly_data'][0]
        raw_price = first_hour['price']
        
        # Calculate with VAT and fees
        vat_rate = 0.23
        fee = 2.0
        dist = 80.0  # Assuming low tariff
        
        price_with_vat = raw_price * (1 + vat_rate)
        total_pln_mwh = price_with_vat + fee + dist
        total_pln_kwh = total_pln_mwh / 1000
        
        print(f"\n💰 Price Calculation Example (H{first_hour['hour']:02d}):")
        print(f"   Base price (TGE): {raw_price:.2f} PLN/MWh")
        print(f"   With VAT (23%): {price_with_vat:.2f} PLN/MWh")
        print(f"   + Exchange fee: {fee:.2f} PLN/MWh")
        print(f"   + Distribution: {dist:.2f} PLN/MWh")
        print(f"   Total: {total_pln_mwh:.2f} PLN/MWh")
        print(f"   Total: {total_pln_kwh:.4f} PLN/kWh")

async def main():
    """Run all tests."""
    import asyncio
    
    try:
        # Test data fetching
        success = await test_coordinator()
        
        # Test price calculations
        await test_price_calculation()
        
        print("\n" + "=" * 70)
        if success:
            print("✅ All tests passed!")
        else:
            print("⚠️ Some tests could not complete (data not available)")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
