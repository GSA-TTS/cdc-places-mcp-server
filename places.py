import httpx
from mcp.server.fastmcp import FastMCP
from utils import set_query_params

# Initialize FastMCP server
mcp = FastMCP("CDC_PLACES")

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


@mcp.tool()
async def get_cdc_places_data(GEO: str, YEAR: str, MEASUREID: str, DATAVALUETYPID: str, LOC: str) -> str:
    """Fetch data from the CDC PLACES API for a given measure, geographic breakdown, and year.
    
    Args:
        GEO: geographic breakdown (e.g. 'state', 'county', 'census', 'zcta', 'places')
        
        YEAR: year of the data (e.g. '2020')
        
        MEASUREID: measure identifier
        MEASUREID	Measure Full Name
        ARTHRITIS	Arthritis among adults
        BPHIGH	High blood pressure among adults
        CANCER	Cancer (non-skin) or melanoma among adults
        CASTHMA	Current asthma among adults
        CHD	Coronary heart disease among adults
        COPD	Chronic obstructive pulmonary disease among adults
        DEPRESSION	Depression among adults
        DIABETES	Diagnosed diabetes among adults
        HIGHCHOL	High cholesterol among adults who have ever been screened
        KIDNEY	Chronic kidney disease among adults aged >=18 years
        OBESITY	Obesity among adults
        STROKE	Stroke among adults
        TEETHLOST	All teeth lost among adults aged >=65 years
        BINGE	Binge drinking among adults
        CSMOKING	Current cigarette smoking among adults
        LPA	No leisure-time physical activity among adults
        SLEEP	Short sleep duration among adults
        GHLTH	Fair or poor self-rated health status among adults
        MHLTH	Frequent mental distress among adults
        PHLTH	Frequent physical distress among adults
        ACCESS2	Lack of health insurance among adults aged 18â€“64 years
        BPMED	Taking medicine to control high blood pressure among adults with high blood pressure
        CERVICAL	Cervical cancer screening among adult women aged 21â€“65 years
        CHECKUP	Routine checkup within the past year among adults
        CHOLSCREEN	Cholesterol screening in the past 5 years among adults
        COLON_SCREEN	Colorectal cancer screening among adults aged 45â€“75 years
        COREM	Older adult men aged >=65 years who are up to date on a core set of clinical preventive services: Flu shot past year, PPV shot ever, Colorectal cancer screening
        COREW	Older adult women aged >=65 years who are up to date on a core set of clinical preventive services: Flu shot past year, PPV shot ever, Colorectal cancer screening, and Mammogram past 2 years
        DENTAL	Visited dentist or dental clinic in the past year among adult
        MAMMOUSE	Mammography use among women aged 50â€“74 years
        HEARING	Hearing disability among adults
        VISION	Vision disability among adults
        COGNITION	Cognitive disability among adults
        MOBILITY	Mobility disability among adults
        SELFCARE	Self-care disability among adults
        INDEPLIVE	Independent living disability among adults
        DISABILITY	Any disability among adults
        ISOLATION	Feeling socially isolated among adults
        FOODSTAMP	Received food stamps in the past 12 months among adults
        FOODINSECU	Food insecurity in the past 12 months among adults
        HOUSINSECU	Housing insecurity in the past 12 months among adults
        SHUTUTILITY	Utility services threat in the past 12 months among adults
        LACKTRPT	Lack of reliable transportation in the past 12 months among adults
        EMOTIONSPT	Lack of social and emotional support among adults
        
        DATAVALUETYPID: data value type identifier (e.g. 'CrdPrv' for crude prevalance and 'AgeAdjPrv' for Age-adjusted prevalance. Default is 'CrdPrv' unless a direct comparison is being made.)
        
        LOC: Location Name to filter the data (e.g. 'Worcester')
    """

    # construct the URL and parameters for the API query
    url, params = set_query_params(
        geo=GEO,
        year=YEAR,
        measureid=MEASUREID,  
        datavaluetypeid=DATAVALUETYPID,
        loc=LOC  
    )

    # set parameters to be returned based off geography 
    if GEO == 'county':
        params["$select"] = 'stateabbr,statedesc,locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'
    elif GEO == 'census': 
        params["$select"] = 'stateabbr,statedesc,countyname,locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'
    elif GEO == 'zcta':
        params["$select"] = 'locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'
    elif GEO == 'places':
        params["$select"] = 'stateabbr,statedesc,locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'

    data = await query_api(url, params)

    return data

@mcp.tool()
async def compare_counties_within_state(STATE: str, YEAR: str, MEASUREID: str) -> str:
    """Compare a measure across all counties within a specified state for a given year. 
    
    Args:
        STATE: two letter abbreviation for state of interest (e.g. 'MA', 'VA', 'CA')
        
        YEAR: year of the data (e.g. '2020')
        
        MEASUREID: measure identifier
        MEASUREID	Measure Full Name
        ARTHRITIS	Arthritis among adults
        BPHIGH	High blood pressure among adults
        CANCER	Cancer (non-skin) or melanoma among adults
        CASTHMA	Current asthma among adults
        CHD	Coronary heart disease among adults
        COPD	Chronic obstructive pulmonary disease among adults
        DEPRESSION	Depression among adults
        DIABETES	Diagnosed diabetes among adults
        HIGHCHOL	High cholesterol among adults who have ever been screened
        KIDNEY	Chronic kidney disease among adults aged >=18 years
        OBESITY	Obesity among adults
        STROKE	Stroke among adults
        TEETHLOST	All teeth lost among adults aged >=65 years
        BINGE	Binge drinking among adults
        CSMOKING	Current cigarette smoking among adults
        LPA	No leisure-time physical activity among adults
        SLEEP	Short sleep duration among adults
        GHLTH	Fair or poor self-rated health status among adults
        MHLTH	Frequent mental distress among adults
        PHLTH	Frequent physical distress among adults
        ACCESS2	Lack of health insurance among adults aged 18â€“64 years
        BPMED	Taking medicine to control high blood pressure among adults with high blood pressure
        CERVICAL	Cervical cancer screening among adult women aged 21â€“65 years
        CHECKUP	Routine checkup within the past year among adults
        CHOLSCREEN	Cholesterol screening in the past 5 years among adults
        COLON_SCREEN	Colorectal cancer screening among adults aged 45â€“75 years
        COREM	Older adult men aged >=65 years who are up to date on a core set of clinical preventive services: Flu shot past year, PPV shot ever, Colorectal cancer screening
        COREW	Older adult women aged >=65 years who are up to date on a core set of clinical preventive services: Flu shot past year, PPV shot ever, Colorectal cancer screening, and Mammogram past 2 years
        DENTAL	Visited dentist or dental clinic in the past year among adult
        MAMMOUSE	Mammography use among women aged 50â€“74 years
        HEARING	Hearing disability among adults
        VISION	Vision disability among adults
        COGNITION	Cognitive disability among adults
        MOBILITY	Mobility disability among adults
        SELFCARE	Self-care disability among adults
        INDEPLIVE	Independent living disability among adults
        DISABILITY	Any disability among adults
        ISOLATION	Feeling socially isolated among adults
        FOODSTAMP	Received food stamps in the past 12 months among adults
        FOODINSECU	Food insecurity in the past 12 months among adults
        HOUSINSECU	Housing insecurity in the past 12 months among adults
        SHUTUTILITY	Utility services threat in the past 12 months among adults
        LACKTRPT	Lack of reliable transportation in the past 12 months among adults
        EMOTIONSPT	Lack of social and emotional support among adults
        
    """

    # construct the URL and parameters for the API query
    url, params = set_query_params(
        geo='county',
        year=YEAR,
        measureid=MEASUREID,  
        datavaluetypeid='AgeAdjPrv', # Use Age-adjusted prevalence for comparison
    )

    # filter for the state of interest 
    params["$where"] = f"stateabbr = '{STATE}'"
    params["$select"] = 'locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'

    data = await query_api(url, params)

    return data

@mcp.tool()
async def compare_census_tracts_within_county(STATE: str, COUNTY: str, YEAR: str, MEASUREID: str) -> str:
    """Compare a measure across all census tracts within a specified county for a given year. 
    
    Args:
        STATE: two letter abbreviation for state that contains the county of interest (e.g. 'MA', 'VA', 'CA')

        COUNTY: name of the county of interest (e.g. 'Worcester', 'Fairfax', 'Los Angeles')
        
        YEAR: year of the data (e.g. '2020')
        
        MEASUREID: measure identifier
        MEASUREID	Measure Full Name
        ARTHRITIS	Arthritis among adults
        BPHIGH	High blood pressure among adults
        CANCER	Cancer (non-skin) or melanoma among adults
        CASTHMA	Current asthma among adults
        CHD	Coronary heart disease among adults
        COPD	Chronic obstructive pulmonary disease among adults
        DEPRESSION	Depression among adults
        DIABETES	Diagnosed diabetes among adults
        HIGHCHOL	High cholesterol among adults who have ever been screened
        KIDNEY	Chronic kidney disease among adults aged >=18 years
        OBESITY	Obesity among adults
        STROKE	Stroke among adults
        TEETHLOST	All teeth lost among adults aged >=65 years
        BINGE	Binge drinking among adults
        CSMOKING	Current cigarette smoking among adults
        LPA	No leisure-time physical activity among adults
        SLEEP	Short sleep duration among adults
        GHLTH	Fair or poor self-rated health status among adults
        MHLTH	Frequent mental distress among adults
        PHLTH	Frequent physical distress among adults
        ACCESS2	Lack of health insurance among adults aged 18â€“64 years
        BPMED	Taking medicine to control high blood pressure among adults with high blood pressure
        CERVICAL	Cervical cancer screening among adult women aged 21â€“65 years
        CHECKUP	Routine checkup within the past year among adults
        CHOLSCREEN	Cholesterol screening in the past 5 years among adults
        COLON_SCREEN	Colorectal cancer screening among adults aged 45â€“75 years
        COREM	Older adult men aged >=65 years who are up to date on a core set of clinical preventive services: Flu shot past year, PPV shot ever, Colorectal cancer screening
        COREW	Older adult women aged >=65 years who are up to date on a core set of clinical preventive services: Flu shot past year, PPV shot ever, Colorectal cancer screening, and Mammogram past 2 years
        DENTAL	Visited dentist or dental clinic in the past year among adult
        MAMMOUSE	Mammography use among women aged 50â€“74 years
        HEARING	Hearing disability among adults
        VISION	Vision disability among adults
        COGNITION	Cognitive disability among adults
        MOBILITY	Mobility disability among adults
        SELFCARE	Self-care disability among adults
        INDEPLIVE	Independent living disability among adults
        DISABILITY	Any disability among adults
        ISOLATION	Feeling socially isolated among adults
        FOODSTAMP	Received food stamps in the past 12 months among adults
        FOODINSECU	Food insecurity in the past 12 months among adults
        HOUSINSECU	Housing insecurity in the past 12 months among adults
        SHUTUTILITY	Utility services threat in the past 12 months among adults
        LACKTRPT	Lack of reliable transportation in the past 12 months among adults
        EMOTIONSPT	Lack of social and emotional support among adults
        
    """

    # construct the URL and parameters for the API query
    url, params = set_query_params(
        geo='census',
        year=YEAR,
        measureid=MEASUREID,  
        datavaluetypeid='CrdPrv'
    )

    # filter for the state of interest 
    params["$where"] = f"stateabbr = '{STATE}' AND countyname = '{COUNTY}'"
    params["$select"] = 'locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'

    data = await query_api(url, params)

    return data

@mcp.tool()
async def compare_places_within_state(STATE: str, YEAR: str, MEASUREID: str) -> str:
    """Compare a measure across all designated places within a specified state for a given year. 
    
    Args:
        STATE: two letter abbreviation for state that contains the county of interest (e.g. 'MA', 'VA', 'CA')

        YEAR: year of the data (e.g. '2020')
        
        MEASUREID: measure identifier
        MEASUREID	Measure Full Name
        ARTHRITIS	Arthritis among adults
        BPHIGH	High blood pressure among adults
        CANCER	Cancer (non-skin) or melanoma among adults
        CASTHMA	Current asthma among adults
        CHD	Coronary heart disease among adults
        COPD	Chronic obstructive pulmonary disease among adults
        DEPRESSION	Depression among adults
        DIABETES	Diagnosed diabetes among adults
        HIGHCHOL	High cholesterol among adults who have ever been screened
        KIDNEY	Chronic kidney disease among adults aged >=18 years
        OBESITY	Obesity among adults
        STROKE	Stroke among adults
        TEETHLOST	All teeth lost among adults aged >=65 years
        BINGE	Binge drinking among adults
        CSMOKING	Current cigarette smoking among adults
        LPA	No leisure-time physical activity among adults
        SLEEP	Short sleep duration among adults
        GHLTH	Fair or poor self-rated health status among adults
        MHLTH	Frequent mental distress among adults
        PHLTH	Frequent physical distress among adults
        ACCESS2	Lack of health insurance among adults aged 18â€“64 years
        BPMED	Taking medicine to control high blood pressure among adults with high blood pressure
        CERVICAL	Cervical cancer screening among adult women aged 21â€“65 years
        CHECKUP	Routine checkup within the past year among adults
        CHOLSCREEN	Cholesterol screening in the past 5 years among adults
        COLON_SCREEN	Colorectal cancer screening among adults aged 45â€“75 years
        COREM	Older adult men aged >=65 years who are up to date on a core set of clinical preventive services: Flu shot past year, PPV shot ever, Colorectal cancer screening
        COREW	Older adult women aged >=65 years who are up to date on a core set of clinical preventive services: Flu shot past year, PPV shot ever, Colorectal cancer screening, and Mammogram past 2 years
        DENTAL	Visited dentist or dental clinic in the past year among adult
        MAMMOUSE	Mammography use among women aged 50â€“74 years
        HEARING	Hearing disability among adults
        VISION	Vision disability among adults
        COGNITION	Cognitive disability among adults
        MOBILITY	Mobility disability among adults
        SELFCARE	Self-care disability among adults
        INDEPLIVE	Independent living disability among adults
        DISABILITY	Any disability among adults
        ISOLATION	Feeling socially isolated among adults
        FOODSTAMP	Received food stamps in the past 12 months among adults
        FOODINSECU	Food insecurity in the past 12 months among adults
        HOUSINSECU	Housing insecurity in the past 12 months among adults
        SHUTUTILITY	Utility services threat in the past 12 months among adults
        LACKTRPT	Lack of reliable transportation in the past 12 months among adults
        EMOTIONSPT	Lack of social and emotional support among adults
        
    """

    # construct the URL and parameters for the API query
    url, params = set_query_params(
        geo='places',
        year=YEAR,
        measureid=MEASUREID,  
        datavaluetypeid='AgeAdjPrv'  # Use Age-adjusted prevalence for comparison
    )

    # filter for the state of interest 
    params["$where"] = f"stateabbr = '{STATE}'"
    params["$select"] = 'locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'

    data = await query_api(url, params)

    return data

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')