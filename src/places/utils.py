import httpx
import requests
import pandas as pd 
from places.config import API_ENDPOINTS, DATA_DICTIONARY_ENDPOINT
from places.models import PlacesParams

def get_release_for_year(measureid, year):
    """
    Looks up the name of the data release for a given measure ID and year.
    
    Args:
        measureid (str): The measure ID to look up.
        year (int): The desired year of data.
    
    Returns:
        str: The name of the data release for the specified measure ID and year.
    """

    # get the data dictionary 
    response = requests.get(DATA_DICTIONARY_ENDPOINT)

    # convert the response to a pandas dataframe
    dataDict = pd.DataFrame(response.json())

    # get the row matching the measureid
    if measureid not in dataDict['measureid'].values:
        print(f"Measure ID {measureid} not found in the data dictionary.")
        return None
    row = dataDict[dataDict['measureid'] == measureid]

    # save row to csv 
    row.to_csv(f"tests/{measureid}_data_dict.csv", index=False)

    # return the column name that matches the year
    if row.empty:
        print(f"No data found for measure ID: {measureid}")
        return None
    return row.columns[(row == year).iloc[0]].tolist()[0]

def get_endpoint_for_geo(geo, release_name):
    """
    Retrieves the API endpoint for a given geographic level and data release name.

    Args:
        geo (str): The geographic level (e.g., 'county', 'census', 'zcta', 'places').
        release_name (str): The name of the data release (e.g., 'places_release_2024').

    Returns:
        str: The API endpoint URL for the specified geographic level and data release.
    """
    if geo not in API_ENDPOINTS:
        print(f"Geographic level '{geo}' is not supported.")
        return None
    if release_name not in API_ENDPOINTS[geo]:
        print(f"Data release '{release_name}' is not available for geographic level '{geo}'.")
        return None
    return API_ENDPOINTS[geo][release_name]

def get_endpoint(params: PlacesParams):
    """
    Retrieves the API endpoint based on the geographic level and year from PlacesParams.

    Args:
        params (PlacesParams): An instance of PlacesParams containing geo and year attributes.

    Returns:
        str: The API endpoint URL for the specified geographic level and year.
    """
    release_name = get_release_for_year(params.measureid.measure_id.value, params.year)
    if not release_name:
        return None
    return get_endpoint_for_geo(params.geo.geo_type.value, release_name)

async def query_api(url, search_params: PlacesParams):
    """
    Queries the CDC Places API with the given URL and parameters.

    Args:
        url (str): The API endpoint URL.
        params (dict, optional): A dictionary of query parameters to include in the request.

    Returns:
        dict: The JSON response from the API if the request is successful.
        None: If the request fails or an error occurs.
    """
    async with httpx.AsyncClient() as client:
        try:
            params = search_params.to_api_params()
            
            # Ensure params is a dict and set the $limit parameter to 100000
            if params is None:
                params = {}
            params["$limit"] = 100000
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()  # Raise an error for bad responses
            return response.json()
        except Exception:
            return None