from places.models import PlacesParams
import httpx 

def query_api(url, search_params: PlacesParams):
    """
    Queries the CDC Places API with the given URL and parameters.

    Args:
        url (str): The API endpoint URL.
        params (dict, optional): A dictionary of query parameters to include in the request.

    Returns:
        dict: The JSON response from the API if the request is successful.
        None: If the request fails or an error occurs.
    """
    with httpx.Client() as client:
        try:
            params = search_params.to_api_params()
            print(f"Querying URL: {url} with params: {params}")
            # Ensure params is a dict and set the $limit parameter to 100000
            if params is None:
                params = {}
            params["$limit"] = 100000
            response = client.get(url, params=params, timeout=30.0)
            response.raise_for_status()  # Raise an error for bad responses
            return response.json()
        except Exception:
            return None