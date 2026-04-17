---
name: tge-rdn-dev
description: Planning, implementation, and testing of the TGE RDN Home Assistant integration. Use for any changes or upgrades to TGE RDN.
---

# TGE RDN Development

This skill provides procedural knowledge for maintaining and upgrading the TGE RDN Home Assistant integration.

## Project Structure

- `custom_components/tge_rdn/`: Core integration code.
  - `const.py`: Configuration keys and constants.
  - `config_flow.py`: Multi-step setup process for dealers/distributors.
  - `sensor.py`: Price calculation and distribution logic.
  - `tariffs.json`: Database of dealers, distributors, and tariffs.
  - `translations/`: UI localizations.
- `tests/`: Project-specific test suite.

## Core Development Workflow

### 1. Research
Analyze `tariffs.json` and `sensor.py` to understand existing pricing logic. Verify TGE data format from `tests/tge_page_sample.html`.
- Reference: [Tariffs Schema](references/tariffs_schema.md)

### 2. Strategy
Propose changes based on user requirements. If adding a new dealer or distributor, define its properties in a draft `tariffs.json` update.

### 3. Execution (Plan -> Act -> Validate)
- **Plan**: Define specific logic changes in `sensor.py` or new fields in `const.py`.
- **Act**: Apply surgical changes using `replace`.
- **Validate**: Run existing and new tests.
  - Reference: [Testing Guide](references/testing_guide.md)

## Key Technical Details

- **Distribution Logic**: `sensor.py` handles `single`, `dual_standard`, `dual_weekend`, and `triple_tauron` logic.
- **TGE Data Source**: Prices are scraped from `https://tge.pl/energia-elektryczna-rdn` (Fixing I).
- **Date Handling**: The integration handles Polish holidays and DST transitions.
