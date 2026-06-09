# CDC PLACES MCP Server

⚠️ **DISCLAIMER**: This is a proof of concept and is not intended for production use. The developers bear no responsibility for the accuracy of the data returned from the tool.

A Model Context Protocol (MCP) server that provides programmatic access to the CDC PLACES dataset for health statistics and outcomes data across US geographic areas.

## Overview

The CDC PLACES dataset provides model-based estimates for chronic disease risk factors, health outcomes, and clinical preventive service use for all 50 states, the District of Columbia, and 500 of the largest US cities and census places. This MCP server enables easy access to this comprehensive health data through MCP clients (such as Claude Desktop, Zed, or any MCP-compatible application).

**Latest Data**: Supports PLACES Release 2025 (using 2023 BRFSS data for most measures)

## Features

### Available Tools

#### 1. `get_cdc_places_data`
Fetch health data for specific measures, locations, and time periods.

**Parameters:**
- `year` (string): Year of the data release (e.g., "2023", "2022")
- `measureid` (enum): Health measure identifier (e.g., "CSMOKING", "DIABETES", "OBESITY")
- `geo` (literal): Geographic level - "state", "county", "census", "zcta", or "places"
- `datavaluetypeid` (literal): "CrdPrv" (crude prevalence) or "AgeAdjPrv" (age-adjusted prevalence)
- `locationname` (optional): Location name (e.g., "Wayne" for Wayne County)

**Example Query:**
```
Get smoking rates for Wayne County, Michigan in 2023
```

#### 2. `area_summary_stats`
Calculate summary statistics across multiple geographic areas within a scope.

**Parameters:**
- `geo_scope` (literal): "counties_in_state", "tracts_in_county", or "places_in_state"
- `state_code` (string): Two-letter state abbreviation (e.g., "CA", "MI")
- `year` (string): Year of the data release
- `measureid` (enum): Health measure identifier
- `datavaluetypeid` (literal): Data value type
- `county` (optional): County name (required for "tracts_in_county" scope)

**Returns:** Count, mean, min, Q1, median, Q3, max with location attribution for point statistics

**Example Query:**
```
Get obesity statistics across all counties in California for 2023
```

### Supported Health Measures (45 total)

The server supports 45 health measures across 6 categories:

- **Health Outcomes** (13 measures): ARTHRITIS, BPHIGH, CANCER, CASTHMA, CHD, COPD, DEPRESSION, DIABETES, HIGHCHOL, KIDNEY, OBESITY, STROKE, TEETHLOST
- **Health Risk Behaviors** (4 measures): BINGE, CSMOKING, LPA, SLEEP
- **Health Status** (3 measures): GHLTH, MHLTH, PHLTH
- **Prevention** (10 measures): ACCESS2, BPMED, CERVICAL, CHECKUP, CHOLSCREEN, COLON_SCREEN, COREM, COREW, DENTAL, MAMMOUSE
- **Disability** (8 measures): HEARING, VISION, COGNITION, MOBILITY, SELFCARE, INDEPLIVE, DISABILITY
- **Health-Related Social Needs** (7 measures): ISOLATION, FOODSTAMP, FOODINSECU, HOUSINSECU, SHUTUTILITY, LACKTRPT, EMOTIONSPT, LONELINESS

**New in 2025**: The LONELINESS measure was added to track social isolation indicators.

## Installation

### Prerequisites
- Python 3.13+
- MCP-compatible client (e.g., Claude Desktop, Zed)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/GSA-TTS/cdc-places-mcp-server.git
cd cdc-places-mcp-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or using `uv`:
```bash
uv pip install -r requirements.txt
```

3. Configure your MCP client to use this server (see Configuration section below)

## Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "places": {
      "command": "python",
      "args": ["-m", "places.app"],
      "cwd": "/path/to/cdc-places-mcp-server",
      "env": {
        "PYTHONPATH": "/path/to/cdc-places-mcp-server/src"
      }
    }
  }
}
```

### Zed Editor

Add to Zed settings:

```json
{
  "context_servers": {
    "places": {
      "command": {
        "path": "python",
        "args": ["-m", "places.app"],
        "cwd": "/path/to/cdc-places-mcp-server",
        "env": {
          "PYTHONPATH": "/path/to/cdc-places-mcp-server/src"
        }
      }
    }
  }
}
```

## Usage

Once configured, you can query the CDC PLACES data through your MCP client:

**Example queries:**
- "What are the diabetes rates in Los Angeles County for 2023?"
- "Show me obesity statistics across all counties in Texas"
- "Compare smoking rates between Wayne County, Michigan and Cook County, Illinois"
- "Get summary statistics for depression across all census tracts in Worcester County, Massachusetts"

## Project Structure

```
cdc-places-mcp-server/
├── src/places/
│   ├── app.py                 # FastMCP server initialization
│   ├── config.py              # API endpoints and configuration
│   ├── models.py              # Pydantic models for validation
│   ├── routes.py              # Custom HTTP routes (health check)
│   ├── utils.py               # Utility functions (API queries, lookups)
│   ├── data/
│   │   └── places_year_measureid_lookup.csv  # Local lookup table
│   └── tools/
│       ├── __init__.py        # Tool registration
│       ├── get_cdc_places_data.py
│       └── area_summary_stats.py
├── tests/
│   ├── test_lookup_table.py  # Comprehensive test suite (19 tests)
│   └── README.md              # Test documentation
├── docs/
│   └── SBX_PATTERNS.md        # Docker sandbox patterns
├── eval/                       # Evaluation scripts
├── pyproject.toml             # Python package configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Architecture Highlights

### Local Lookup Table
The server uses a local CSV lookup table (`src/places/data/places_year_measureid_lookup.csv`) to map health measures and years to CDC PLACES data releases. This eliminates network dependencies for lookups and enables offline development.

### Modular Tool Design
Each MCP tool is defined in its own file within `src/places/tools/`, making the codebase easy to extend and maintain. Tools use explicit parameters for better MCP client ergonomics.

### Data Sources
- **Primary**: CDC PLACES API via data.cdc.gov
- **Releases**: 2020-2025 (PLACES) and 2016-2019 (500 Cities)
- **Update Frequency**: Annual releases, typically containing data 1-2 years prior

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

The test suite includes:
- 14 tests for `get_release_for_year()` utility function
- 5 tests for lookup table data integrity
- Coverage of 2025 release data, new measures, edge cases, and error handling

See [tests/README.md](tests/README.md) for detailed test documentation.

## Development

### Adding New Measures

When CDC releases new measures:

1. Download sample data from the CDC PLACES dataset
2. Update `src/places/data/places_year_measureid_lookup.csv` with the new release column
3. Add measure enum to `src/places/models.py` if it's a new measure
4. Run tests to verify: `pytest tests/ -v`

### Project Dependencies

- **fastmcp** (3.4.2+): Model Context Protocol server framework
- **pandas** (3.0.3+): Data manipulation for lookup table
- **requests** (2.34.2+): HTTP requests to CDC API
- **pytest** (9.0.3+): Testing framework

## Data Limitations

- Some measures are collected only in odd years (BPHIGH, HIGHCHOL, CHOLSCREEN, BPMED)
- Some measures are collected only in even years (TEETHLOST, SLEEP, DENTAL, MAMMOUSE, etc.)
- Certain measures were discontinued after specific releases (KIDNEY after 2023, CERVICAL/COREM/COREW after 2023)
- The LONELINESS measure was added in the 2025 release

## Resources

- [CDC PLACES Dataset](https://www.cdc.gov/places/index.html)
- [CDC PLACES Data Dictionary](https://data.cdc.gov/500-Cities-Places/PLACES-Data-Dictionary/wb67-qxck)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

## Contributing

This is a pilot project under active development. Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## Disclaimer

This MCP server is a pilot project and is under development. The developers bear no responsibility for the accuracy of the data returned from the tool. Always verify critical health data against official CDC sources.

## Contact

For questions or issues, please open a GitHub issue.
