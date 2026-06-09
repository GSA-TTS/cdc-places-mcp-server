from places.utils import get_endpoint_for_geo, get_release_for_year, _fetch_api, compute_summary_stats
from places.models import MeasureID

from typing import Annotated, Literal, Optional

def register(mcp):
    """Register the area_summary_stats tool with the MCP server."""

    @mcp.tool()
    async def area_summary_stats(
        geo_scope: Annotated[
            Literal["counties_in_state", "tracts_in_county", "places_in_state"],
            "Geographic scope for summary statistics"
        ],
        state_code: Annotated[str, "Two-letter state abbreviation (e.g., 'CA', 'MI')"],
        year: Annotated[str, "Year of the data release (e.g., '2020')"],
        measureid: Annotated[MeasureID, "The health measure identifier"],
        datavaluetypeid: Annotated[
            Literal["CrdPrv", "AgeAdjPrv"],
            "Type of data value to retrieve (crude prevalence or age-adjusted prevalence)"
        ],
        county: Annotated[
            Optional[str], 
            "County name (required if geo_scope is 'tracts_in_county'). Use just the county name, e.g. 'Worcester'."
        ] = None,
    ):
        """Get summary statistics for a health measure across all areas within a geographic scope.

        Supports three scopes:
        - counties_in_state: all counties within a state
        - tracts_in_county: all census tracts within a county (requires county field)
        - places_in_state: all designated places (cities/CDPs) within a state

        Returns count, mean, min, Q1, median, Q3, and max. Point statistics (min, median, max)
        include the corresponding location name.

        Returns:
            dict: Summary statistics with location attribution for point values.
        """
        # Validate county requirement for tracts_in_county
        if geo_scope == "tracts_in_county" and not county:
            return {"error": "county parameter is required when geo_scope is 'tracts_in_county'"}
        
        # Map geo_scope to geo_type
        geo_type_map = {
            "counties_in_state": "county",
            "tracts_in_county": "census",
            "places_in_state": "places",
        }
        geo_type = geo_type_map[geo_scope]
        
        # Get the release name for the specified measure and year
        release_name = get_release_for_year(measureid.value, year)
        if not release_name:
            return {"error": f"No data release found for measure {measureid.value} in year {year}"}

        # Get the API endpoint
        url = get_endpoint_for_geo(geo_type, release_name)
        if not url:
            return {"error": f"No endpoint found for geo type '{geo_type}' and release '{release_name}'"}

        # Build API parameters
        api_params = {
            "measureid": measureid.value,
            "datavaluetypeid": datavaluetypeid,
            "$limit": 100000,
        }
        
        # Add geo-specific parameters
        if geo_type == "county":
            api_params["$where"] = f"stateabbr = '{state_code}'"
            api_params["$select"] = "locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation"
        elif geo_type == "census":
            api_params["$where"] = f"stateabbr = '{state_code}' AND countyname = '{county}'"
            api_params["$select"] = "locationname,countyname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation"
        elif geo_type == "places":
            api_params["$where"] = f"stateabbr = '{state_code}'"
            api_params["$select"] = "locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation"

        # Fetch data from API
        records = await _fetch_api(url, api_params)
        if not records:
            return {"error": "No data returned from API"}

        # Compute summary statistics
        stats = compute_summary_stats(records)

        return {
            "measure": measureid.value,
            "geo_scope": geo_scope,
            "state": state_code,
            "county": county,
            "year": year,
            "datavaluetypeid": datavaluetypeid,
            "stats": stats,
        }
