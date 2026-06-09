# Tests for CDC PLACES MCP Server

This directory contains tests for the CDC PLACES MCP Server.

## Running Tests

### Run all tests:
```bash
pytest tests/ -v
```

### Run specific test file:
```bash
pytest tests/test_lookup_table.py -v
```

### Run specific test class:
```bash
pytest tests/test_lookup_table.py::TestGetReleaseForYear -v
```

### Run specific test:
```bash
pytest tests/test_lookup_table.py::TestGetReleaseForYear::test_2025_release_measures -v
```

## Test Coverage

### `test_lookup_table.py`
Tests for the local CSV lookup table functionality:

**TestGetReleaseForYear** - Tests for the `get_release_for_year()` utility function:
- 2025 release measures (2023 data)
- 2024 release measures (2022 data)
- 2023 and older releases
- New LONELINESS measure
- Discontinued measures (KIDNEY, CERVICAL, etc.)
- Odd-year measures (BPHIGH, HIGHCHOL, etc.)
- Even-year measures (TEETHLOST, SLEEP, etc.)
- Invalid inputs and edge cases
- Type flexibility (string vs integer years)
- Case sensitivity
- All category coverage

**TestLookupTableConsistency** - Tests for data integrity:
- Presence of "PLACES Release 2025" column
- Presence and metadata of LONELINESS measure
- Total measure count (45 measures)
- No missing MeasureIDs
- Data distribution in 2025 release

## Requirements

Tests require:
- `pytest` - Test framework
- `pandas` - For CSV data validation tests

Install test dependencies:
```bash
pip install pytest pandas
```

Or if using uv:
```bash
uv pip install pytest pandas
```
