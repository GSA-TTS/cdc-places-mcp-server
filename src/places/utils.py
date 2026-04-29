import httpx
import requests
import statistics
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

async def _fetch_api(url: str, params: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

async def query_api(url, search_params: PlacesParams):
    params = search_params.to_api_params()
    if params is None:
        params = {}
    params["$limit"] = 100000
    return await _fetch_api(url, params)

def compute_summary_stats(records: list) -> dict:
    valid = []
    for r in records:
        try:
            valid.append((float(r["data_value"]), r))
        except (KeyError, TypeError, ValueError):
            continue

    if not valid:
        return {"error": "No valid data values found"}

    valid.sort(key=lambda x: x[0])
    values = [v for v, _ in valid]
    n = len(values)

    mean_val = statistics.mean(values)
    quartiles = statistics.quantiles(values, n=4)
    median_val = statistics.median(values)
    median_idx = min(range(n), key=lambda i: abs(values[i] - median_val))

    def location_info(record):
        info = {"value": float(record["data_value"]), "location": record["locationname"]}
        if "countyname" in record:
            info["county"] = record["countyname"]
        return info

    return {
        "count": n,
        "mean": round(mean_val, 2),
        "min": location_info(valid[0][1]),
        "q1": round(quartiles[0], 2),
        "median": location_info(valid[median_idx][1]),
        "q3": round(quartiles[2], 2),
        "max": location_info(valid[-1][1]),
    }