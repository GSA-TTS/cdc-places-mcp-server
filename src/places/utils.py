import httpx
import requests
import pandas as pd 
from places.config import API_ENDPOINTS, DATA_DICTIONARY_ENDPOINT

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

def set_query_params(geo, year, measureid=None, datavaluetypeid=None, loc=None):
    """
    Selects the corresponding API endpoint based on geography level and year and sets query parameters.
    
    Args:
        geo (str): The geographic level (e.g., 'county', 'census', 'zcta', 'places').
        year (int): The year of the data release.
        measureid (str, optional): The measure ID to filter by.
        datavaluetypeid (str, optional): The data value type ID to filter by.
        loc (str, optional): The location name to filter by.

    Returns:
        tuple: A tuple containing the API endpoint URL and a dictionary of query parameters.
    """
    
    # get the API endpoint for the specified geographic level and year
    url = get_endpoint_for_geo(geo, get_release_for_year(measureid, year))

    # initialize an empty dictionary for parameters
    params = {}
    if measureid:
        params["measureid"] = measureid
    if datavaluetypeid:
        params["datavaluetypeid"] = datavaluetypeid
    if loc:
        params["locationname"] = loc

    return url, params

async def query_api(url, params=None):
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
            # Ensure params is a dict and set the $limit parameter to 100000
            if params is None:
                params = {}
            params["$limit"] = 100000
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()  # Raise an error for bad responses
            return response.json()
        except Exception:
            return None