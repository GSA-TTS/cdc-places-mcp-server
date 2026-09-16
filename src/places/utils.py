import httpx
import statistics
import pandas as pd
import os
from datetime import datetime, timezone
from places.config import (
    API_ENDPOINTS,
    LOOKUP_TABLE_PATH,
    DATA_DICTIONARY_ENDPOINT,
    PLACES_METHODOLOGY_URL,
)

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


def _get_measure_row(measureid):
    """
    Return the lookup-table row for a measure ID as a pandas Series, or None.

    Args:
        measureid (str): The measure ID to look up (e.g., 'CSMOKING').

    Returns:
        pandas.Series or None: The matching row, or None if not found.
    """
    try:
        lookup_df = pd.read_csv(LOOKUP_TABLE_PATH)
    except FileNotFoundError:
        print(f"Lookup table not found at: {LOOKUP_TABLE_PATH}")
        return None
    except Exception as e:
        print(f"Error reading lookup table: {e}")
        return None

    if measureid not in lookup_df["MeasureID"].values:
        return None

    return lookup_df[lookup_df["MeasureID"] == measureid].iloc[0]


def get_measure_name(measureid):
    """
    Return the human-readable full name for a measure ID.

    Prefers the current 'Measure full name' column and falls back to the
    historical 'Measure full name 2016-2023' column.

    Args:
        measureid (str): The measure ID to look up (e.g., 'CSMOKING').

    Returns:
        str or None: The measure's full name, or None if not found.
    """
    row = _get_measure_row(measureid)
    if row is None:
        return None

    for col in ("Measure full name", "Measure full name 2016-2023"):
        if col in row.index:
            value = row[col]
            if pd.notna(value) and str(value).strip():
                return str(value).strip()
    return None


def _release_column_for_release_name(release_name):
    """
    Map an internal release name to the lookup-table column that holds its
    BRFSS survey year.

    Examples:
        'places_release_2020'  -> 'PLACES Release 2020'
        '500cities_release_2019' -> '500 Cities Release 2019'

    Args:
        release_name (str): The internal release name.

    Returns:
        str or None: The matching column name, or None if it can't be derived.
    """
    if not release_name:
        return None
    if release_name.startswith("places_release_"):
        return f"PLACES Release {release_name.replace('places_release_', '')}"
    if release_name.startswith("500cities_release_"):
        return f"500 Cities Release {release_name.replace('500cities_release_', '')}"
    return None


def get_brfss_year(measureid, release_name):
    """
    Return the underlying BRFSS survey year for a measure in a given release.

    Args:
        measureid (str): The measure ID (e.g., 'CSMOKING').
        release_name (str): The internal release name (e.g., 'places_release_2020').

    Returns:
        str or None: The BRFSS survey year (e.g., '2018'), or None if not found.
    """
    row = _get_measure_row(measureid)
    if row is None:
        return None

    col = _release_column_for_release_name(release_name)
    if not col or col not in row.index:
        return None

    value = row[col]
    if pd.isna(value) or not str(value).strip():
        return None
    return str(value).strip()


def _socrata_dataset_id(url):
    """Extract the Socrata dataset ID (e.g. 'dv4u-3x3q') from a resource URL."""
    if not url:
        return None
    return url.rstrip("/").split("/")[-1].replace(".json", "")


def _release_year(release_name):
    """Extract the release year (e.g. '2020') from an internal release name."""
    if not release_name:
        return None
    return release_name.split("_")[-1]


def build_citation(geo, year, measureid, url, release_name):
    """
    Build a structured citation for a CDC PLACES data query.

    Args:
        geo (str): The geographic level (e.g., 'county', 'census', 'zcta', 'places').
        year (str): The requested BRFSS year passed to the tool.
        measureid (str): The measure ID (e.g., 'CSMOKING').
        url (str): The resolved Socrata API endpoint URL.
        release_name (str): The internal release name (e.g., 'places_release_2020').

    Returns:
        dict: A structured citation block describing the data source.
    """
    release_year = _release_year(release_name)
    measure_name = get_measure_name(measureid)
    brfss_year = get_brfss_year(measureid, release_name)
    dataset_id = _socrata_dataset_id(url)
    accessed_date = datetime.now(timezone.utc).date().isoformat()

    suggested = (
        f"Centers for Disease Control and Prevention. PLACES: {geo} Data "
        f"({release_year} Release). {measure_name or measureid}. "
        f"Socrata dataset {dataset_id}. {url}. Accessed {accessed_date}."
    )

    return {
        "source": "CDC PLACES",
        "dataset": release_name,
        "release_year": release_year,
        "geography": geo,
        "measure_id": measureid,
        "measure_name": measure_name,
        "brfss_survey_year": brfss_year,
        "socrata_dataset_id": dataset_id,
        "source_url": url,
        "data_dictionary_url": DATA_DICTIONARY_ENDPOINT,
        "methodology_url": PLACES_METHODOLOGY_URL,
        "accessed_date": accessed_date,
        "suggested_citation": suggested,
    }