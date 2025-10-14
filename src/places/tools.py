from places.utils import query_api, get_endpoint
from places.models import PlacesParams

def register_tools(mcp):

    @mcp.tool()
    async def get_cdc_places_data(search_params: PlacesParams) -> str:
        """Fetch data from the CDC PLACES API for a given measure, geographic breakdown, and year.
        
        Args:
            search_params (PlacesParams): An instance of PlacesParams containing geo, year, measureid, datavaluetypeid, and loc attributes.
        Returns:
            dict: API response containing CDC Places data
        """
        # construct the URL for the API query
        url = get_endpoint(search_params)

        # query the API and return the result 
        return await query_api(url, search_params)
    
    # @mcp.tool()
    # async def compare_counties_within_state(search_params: PlacesParams) -> str:
    #     """Compare a measure across all counties within a specified state for a given year. 
        
    #     Args:
    #         search_params (PlacesParams): An instance of PlacesParams containing geo, year, measureid, datavaluetypeid, and loc attributes.
    #     Returns:
    #         dict: API response containing CDC Places data
    #     """

    #     # construct the URL and parameters for the API query
    #     url, params = set_query_params(
    #         geo='county',
    #         year=YEAR,
    #         measureid=MEASUREID,  
    #         datavaluetypeid='AgeAdjPrv', # Use Age-adjusted prevalence for comparison
    #     )

    #     # filter for the state of interest 
    #     params["$where"] = f"stateabbr = '{STATE}'"
    #     params["$select"] = 'locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'

    #     data = await query_api(url, params)

    #     return data
    
    # @mcp.tool()
    # async def compare_census_tracts_within_county(STATE: str, COUNTY: str, YEAR: str, MEASUREID: str) -> str:
    #     """Compare a measure across all census tracts within a specified county for a given year. 
        
    #     Args:
            
            
    #     """

    #     # construct the URL and parameters for the API query
    #     url, params = set_query_params(
    #         geo='census',
    #         year=YEAR,
    #         measureid=MEASUREID,  
    #         datavaluetypeid='CrdPrv'
    #     )

    #     # filter for the state of interest 
    #     params["$where"] = f"stateabbr = '{STATE}' AND countyname = '{COUNTY}'"
    #     params["$select"] = 'locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'

    #     data = await query_api(url, params)

    #     return data
    
    # @mcp.tool()
    # async def compare_places_within_state(STATE: str, YEAR: str, MEASUREID: str) -> str:
    #     """Compare a measure across all designated places within a specified state for a given year. 
        
    #     Args:
            
    #     """

    #     # construct the URL and parameters for the API query
    #     url, params = set_query_params(
    #         geo='places',
    #         year=YEAR,
    #         measureid=MEASUREID,  
    #         datavaluetypeid='AgeAdjPrv'  # Use Age-adjusted prevalence for comparison
    #     )

    #     # filter for the state of interest 
    #     params["$where"] = f"stateabbr = '{STATE}'"
    #     params["$select"] = 'locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'

    #     data = await query_api(url, params)

    #     return data