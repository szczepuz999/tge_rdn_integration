#!/usr/bin/env python3
"""Test script for TGE RDN integration."""

import requests
import pandas as pd
from datetime import datetime

def test_tge_rdn_fetch():
    """Test fetching TGE RDN data."""
    today = datetime.now()
    url = f"https://www.tge.pl/pub/TGE/SDAC%20{today.year}/RDN/Raport_RDN_dzie_dostawy_delivery_day_{today.year}_{today.month:02d}_{today.day:02d}.xlsx"

    print(f"Testing URL: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        print("✓ File downloaded successfully")

        # Parse Excel
        df = pd.read_excel(response.content, sheet_name="WYNIKI", header=None)
        print(f"✓ Excel parsed, shape: {df.shape}")

        # Find hourly data
        hourly_count = 0
        for index, row in df.iterrows():
            time_value = row[8]  # Column I
            price_value = row[10]  # Column K

            if pd.notna(time_value) and isinstance(time_value, str):
                if "_H" in str(time_value) and pd.notna(price_value):
                    hourly_count += 1

        print(f"✓ Found {hourly_count} hourly price records")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=== TGE RDN Integration Test ===")
    success = test_tge_rdn_fetch()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
