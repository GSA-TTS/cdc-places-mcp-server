from typing import Annotated, Literal, Optional, List  

from places.utils import query_api, get_endpoint
from places.models import MeasureID


def register(mcp):
    """Register the get_cdc_places_data tool with the MCP server."""

    @mcp.tool()
    async def get_cdc_places_data(
        year: Annotated[str, "Year of the data release, e.g. '2020'"],
        measureid: Annotated[MeasureID, "The health measure identifier"],
        geo: Annotated[
            Literal["state", "county", "census", "zcta", "places"],
            "Geographic breakdown level"
        ],
        datavaluetypeid: Annotated[
            Literal["CrdPrv", "AgeAdjPrv"],
            "Type of data value to retrieve (e.g. crude prevalence, age-adjusted prevalence)"
        ],
        locationname: Annotated[
            Optional[str | List[str]], 
            "The name of the location (e.g., county name). Phrase as just the county name (e.g. 'Worcester', not 'Worcester County'). Can be a single string or a list of strings."
        ] = None
    ):
        """Fetch data from the CDC PLACES API for a given measure, geographic breakdown, and year.
        
        Example of valid parameters in a query for smoking rates amongst adults in Wayne County, Michigan, in 2020: 
            
                "geo":"county",
                "year":"2020",
                "measureid":"CSMOKING",
                "datavaluetypeid":"CrdPrv", 
                "locationname":"Wayne"
        """
        
        # Construct the URL for the API query
        url = get_endpoint(geo, year, measureid.value)
        
        if not url:
            return {"error": f"Could not determine API endpoint for geo={geo}, year={year}, measureid={measureid.value}"}
        
        # Build API parameters
        api_params = {
            "measureid": measureid.value,
            "datavaluetypeid": datavaluetypeid,
        }
        
        if locationname:
            api_params["locationname"] = locationname
        
        # Set parameters based on geography
        if geo == 'county':
            api_params["$select"] = 'stateabbr,statedesc,locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'
        elif geo == 'census': 
            api_params["$select"] = 'stateabbr,statedesc,countyname,locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'
        elif geo == 'zcta':
            api_params["$select"] = 'locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'
        elif geo == 'places':
            api_params["$select"] = 'stateabbr,statedesc,locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'

        # Query the API and return the result
        return await query_api(url, api_params)
