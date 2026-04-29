from places.utils import query_api, get_endpoint, get_endpoint_for_geo, get_release_for_year, _fetch_api, compute_summary_stats
from places.models import PlacesParams, AreaSummaryParams

def register_tools(mcp):

    @mcp.tool()
    async def get_cdc_places_data(search_params: PlacesParams):
        """Fetch data from the CDC PLACES API for a given measure, geographic breakdown, and year.
        
        Args:
            search_params (PlacesParams): An instance of PlacesParams containing geo, year, measureid, datavaluetypeid, and locationname attributes.
        Returns:
            dict: API response containing CDC Places data

        Example of valid parameters in a query for smoking rates amongst adults in Wayne County, Michigan, in 2020: 
            {"search_params":{
                "geo":{"geo_type":"county", "stateabbr":"MI"},
                "year":"2020",
                "measureid":{"measure_id":"CSMOKING"},
                "datavaluetypeid":{"datavaluetype_id":"CrdPrv"}}, 
                "locationname":{"locationname":"Wayne"}
            }
        """
        # construct the URL for the API query
        url = get_endpoint(search_params)

        # query the API and return the result
        return await query_api(url, search_params)

    @mcp.tool()
    async def area_summary_stats(search_params: AreaSummaryParams):
        """Get summary statistics for a health measure across all areas within a geographic scope.

        Supports three scopes:
        - counties_in_state: all counties within a state
        - tracts_in_county: all census tracts within a county (requires county field)
        - places_in_state: all designated places (cities/CDPs) within a state

        Returns count, mean, min, Q1, median, Q3, and max. Point statistics (min, median, max)
        include the corresponding location name.

        Args:
            search_params (AreaSummaryParams): Parameters specifying scope, state, measure, and year.
        Returns:
            dict: Summary statistics with location attribution for point values.
        """
        geo_type = search_params.get_geo_type()
        release_name = get_release_for_year(search_params.measureid.measure_id.value, search_params.year)
        if not release_name:
            return {"error": f"No data release found for measure {search_params.measureid.measure_id.value} in year {search_params.year}"}

        url = get_endpoint_for_geo(geo_type, release_name)
        if not url:
            return {"error": f"No endpoint found for geo type '{geo_type}' and release '{release_name}'"}

        records = await _fetch_api(url, search_params.to_api_params())
        if not records:
            return {"error": "No data returned from API"}

        stats = compute_summary_stats(records)

        return {
            "measure": search_params.measureid.measure_id.value,
            "geo_scope": search_params.geo_scope.value,
            "state": search_params.state.value,
            "county": search_params.county,
            "year": search_params.year,
            "datavaluetypeid": search_params.get_datavaluetypeid(),
            "stats": stats,
        }