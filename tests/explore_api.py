import os, sys

# add places module to path 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from places.models import PlacesParams, GeoType, GeoTypeEnum, MeasureID, MeasureIDEnum, DataValueTypeID, DataValueTypeIDEnum
from places.utils import get_endpoint
from test_utils import query_api
import pandas as pd 

def get_places_data(geo, year, measureid, datavaluetypeid, locationname):

    # set parameters for test query 
    params = PlacesParams(
        geo=GeoType(geo_type=GeoTypeEnum(geo)), 
        year=year,
        measureid=MeasureID(measure_id=MeasureIDEnum(measureid)),
        datavaluetypeid=DataValueTypeID(datavaluetype_id=DataValueTypeIDEnum(datavaluetypeid)),
        locationname=locationname,
    )

    # get endpoint and convert query parameters 
    url = get_endpoint(params)

    # query the API
    data = query_api(url, params)

    # export data to csv 
    df = pd.DataFrame(data)
    df.to_csv("tests/places_data.csv", index=False)

get_places_data()


