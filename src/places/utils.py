import httpx
import statistics
import pandas as pd
import os
from places.config import API_ENDPOINTS, LOOKUP_TABLE_PATH

def get_release_for_year(measureid, year):
    """
    Looks up the name of the data release for a given measure ID and year.
    
    Uses the local CSV lookup table at docs/places_year_measureid_lookup.csv.
    
    Args:
        measureid (str): The measure ID to look up (e.g., 'CSMOKING').
        year (str or int): The desired BRFSS year of data (e.g., '2023' or 2023).
    
    Returns:
        str: The name of the data release (e.g., 'places_release_2024') or None if not found.
    """
    # Convert year to string for comparison
    year_str = str(year)
    
    try:
        # Read the local lookup table
        lookup_df = pd.read_csv(LOOKUP_TABLE_PATH)
        
        # Find the row matching the measureid
        if measureid not in lookup_df['MeasureID'].values:
            print(f"Measure ID {measureid} not found in the lookup table.")
            return None
        
        measure_row = lookup_df[lookup_df['MeasureID'] == measureid].iloc[0]
        
        # Search through the PLACES Release columns to find which one contains the year
        release_columns = [col for col in lookup_df.columns if 'PLACES Release' in col or '500 Cities Release' in col]
        
        for col in release_columns:
            if str(measure_row[col]) == year_str:
                # Extract the release year from the column name
                # e.g., "PLACES Release 2024" -> "places_release_2024"
                if 'PLACES Release' in col:
                    release_year = col.replace('PLACES Release ', '')
                    return f"places_release_{release_year}"
                elif '500 Cities Release' in col:
                    release_year = col.replace('500 Cities Release ', '')
                    return f"500cities_release_{release_year}"
        
        print(f"No data release found for measure {measureid} with year {year_str}")
        return None
        
    except FileNotFoundError:
        print(f"Lookup table not found at: {LOOKUP_TABLE_PATH}")
        return None
    except Exception as e:
        print(f"Error reading lookup table: {e}")
        return None

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

def get_endpoint(geo: str, year: str, measureid: str):
    """
    Retrieves the API endpoint based on the geographic level, year, and measure ID.

    Args:
        geo (str): The geographic level (e.g., 'county', 'state', 'census', 'zcta', 'places').
        year (str): The year of the data release (e.g., '2020').
        measureid (str): The measure ID to look up.

    Returns:
        str: The API endpoint URL for the specified geographic level and year.
    """
    release_name = get_release_for_year(measureid, year)
    if not release_name:
        return None
    return get_endpoint_for_geo(geo, release_name)

async def _fetch_api(url: str, params: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

async def query_api(url, api_params: dict):
    """
    Query the CDC PLACES API with the given URL and parameters.
    
    Args:
        url (str): The API endpoint URL.
        api_params (dict): Dictionary of API parameters to send with the request.
    
    Returns:
        dict: The JSON response from the API.
    """
    if api_params is None:
        api_params = {}
    api_params["$limit"] = 100000
    return await _fetch_api(url, api_params)

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