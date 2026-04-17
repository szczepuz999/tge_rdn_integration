# Testing Guide for TGE RDN

This guide outlines the testing procedures for the TGE RDN integration.

## Existing Tests
- `test_tge_scraping.py`: Verifies the ability to fetch data from TGE.
- `test_table_parser.py`: Tests the logic for parsing HTML tables.
- `test_integration.py`: Tests the DataUpdateCoordinator and basic sensor logic.
- `test_corrected.py`, `test_final_v1.8.1.py`, etc.: Historical test cases.

## Running Tests
Run tests using pytest:
```bash
python -m pytest tests/
```

Or run specific test files:
```bash
python tests/test_table_parser.py
```

## Adding New Tests
When modifying tariff logic or adding new dealers:
1. Create a reproduction script in `tests/` to verify the bug or feature.
2. Update existing tests if the schema of `tariffs.json` changes.
3. Test against `tests/tge_page_sample.html` to ensure parsing remains robust.
