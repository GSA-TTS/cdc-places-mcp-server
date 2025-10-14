from pydantic import BaseModel, Field, field_validator
from enum import Enum 
from typing import Optional, List, Union

class StateCode(str, Enum):
    AL = "AL"
    AK = "AK"
    AZ = "AZ"
    AR = "AR"
    CA = "CA"
    CO = "CO"
    CT = "CT"
    DE = "DE"
    FL = "FL"
    GA = "GA"
    HI = "HI"
    ID = "ID"
    IL = "IL"
    IN = "IN"
    IA = "IA"
    KS = "KS"
    KY = "KY"
    LA = "LA"
    ME = "ME"
    MD = "MD"
    MA = "MA"
    MI = "MI"
    MN = "MN"
    MS = "MS"
    MO = "MO"
    MT = "MT"
    NE = "NE"
    NV = "NV"
    NH = "NH"
    NJ = "NJ"
    NM = "NM"
    NY = "NY"
    NC = "NC"
    ND = "ND"
    OH = "OH"
    OK = "OK"
    OR = "OR"
    PA = "PA"
    RI = "RI"
    SC = "SC"
    SD = "SD"
    TN = "TN"
    TX = "TX"
    UT = "UT"
    VT = "VT"
    VA = "VA"
    WA = "WA"
    WV = "WV"
    WI = "WI"
    WY = "WY"
    DC = "DC"
    PR = "PR"
    VI = "VI"
    GU = "GU"
    AS = "AS"
    MP = "MP"
    FM = "FM"
    MH = "MH"
    PW = "PW"

class MeasureIDEnum(str, Enum):
    """Enumeration of health measure IDs from CDC PLACES dataset"""
    
    # Chronic Conditions
    ARTHRITIS = "ARTHRITIS"
    BPHIGH = "BPHIGH"
    CANCER = "CANCER"
    CASTHMA = "CASTHMA"
    CHD = "CHD"
    COPD = "COPD"
    DEPRESSION = "DEPRESSION"
    DIABETES = "DIABETES"
    HIGHCHOL = "HIGHCHOL"
    KIDNEY = "KIDNEY"
    OBESITY = "OBESITY"
    STROKE = "STROKE"
    TEETHLOST = "TEETHLOST"
    
    # Risk Behaviors
    BINGE = "BINGE"
    CSMOKING = "CSMOKING"
    LPA = "LPA"
    SLEEP = "SLEEP"
    
    # Health Status
    GHLTH = "GHLTH"
    MHLTH = "MHLTH"
    PHLTH = "PHLTH"
    
    # Prevention
    ACCESS2 = "ACCESS2"
    BPMED = "BPMED"
    CERVICAL = "CERVICAL"
    CHECKUP = "CHECKUP"
    CHOLSCREEN = "CHOLSCREEN"
    COLON_SCREEN = "COLON_SCREEN"
    COREM = "COREM"
    COREW = "COREW"
    DENTAL = "DENTAL"
    MAMMOUSE = "MAMMOUSE"
    
    # Disabilities
    HEARING = "HEARING"
    VISION = "VISION"
    COGNITION = "COGNITION"
    MOBILITY = "MOBILITY"
    SELFCARE = "SELFCARE"
    INDEPLIVE = "INDEPLIVE"
    DISABILITY = "DISABILITY"
    
    # Social Determinants of Health
    ISOLATION = "ISOLATION"
    FOODSTAMP = "FOODSTAMP"
    FOODINSECU = "FOODINSECU"
    HOUSINSECU = "HOUSINSECU"
    SHUTUTILITY = "SHUTUTILITY"
    LACKTRPT = "LACKTRPT"
    EMOTIONSPT = "EMOTIONSPT"


class MeasureID(BaseModel):
    """Model for health measure identifiers with descriptions"""
    
    measure_id: MeasureIDEnum = Field(..., description="Health measure identifier code")
    
    @property
    def description(self) -> str:
        """Get the human-readable description for the measure ID"""
        descriptions = {
            MeasureIDEnum.ARTHRITIS: "Arthritis among adults",
            MeasureIDEnum.BPHIGH: "High blood pressure among adults",
            MeasureIDEnum.CANCER: "Cancer (non-skin) or melanoma among adults",
            MeasureIDEnum.CASTHMA: "Current asthma among adults",
            MeasureIDEnum.CHD: "Coronary heart disease among adults",
            MeasureIDEnum.COPD: "Chronic obstructive pulmonary disease among adults",
            MeasureIDEnum.DEPRESSION: "Depression among adults",
            MeasureIDEnum.DIABETES: "Diagnosed diabetes among adults",
            MeasureIDEnum.HIGHCHOL: "High cholesterol among adults who have ever been screened",
            MeasureIDEnum.KIDNEY: "Chronic kidney disease among adults aged >=18 years",
            MeasureIDEnum.OBESITY: "Obesity among adults",
            MeasureIDEnum.STROKE: "Stroke among adults",
            MeasureIDEnum.TEETHLOST: "All teeth lost among adults aged >=65 years",
            MeasureIDEnum.BINGE: "Binge drinking among adults",
            MeasureIDEnum.CSMOKING: "Current cigarette smoking among adults",
            MeasureIDEnum.LPA: "No leisure-time physical activity among adults",
            MeasureIDEnum.SLEEP: "Short sleep duration among adults",
            MeasureIDEnum.GHLTH: "Fair or poor self-rated health status among adults",
            MeasureIDEnum.MHLTH: "Frequent mental distress among adults",
            MeasureIDEnum.PHLTH: "Frequent physical distress among adults",
            MeasureIDEnum.ACCESS2: "Lack of health insurance among adults aged 18–64 years",
            MeasureIDEnum.BPMED: "Taking medicine to control high blood pressure among adults with high blood pressure",
            MeasureIDEnum.CERVICAL: "Cervical cancer screening among adult women aged 21–65 years",
            MeasureIDEnum.CHECKUP: "Routine checkup within the past year among adults",
            MeasureIDEnum.CHOLSCREEN: "Cholesterol screening in the past 5 years among adults",
            MeasureIDEnum.COLON_SCREEN: "Colorectal cancer screening among adults aged 45–75 years",
            MeasureIDEnum.COREM: "Older adult men aged >=65 years who are up to date on a core set of clinical preventive services: Flu shot past year, PPV shot ever, Colorectal cancer screening",
            MeasureIDEnum.COREW: "Older adult women aged >=65 years who are up to date on a core set of clinical preventive services: Flu shot past year, PPV shot ever, Colorectal cancer screening, and Mammogram past 2 years",
            MeasureIDEnum.DENTAL: "Visited dentist or dental clinic in the past year among adult",
            MeasureIDEnum.MAMMOUSE: "Mammography use among women aged 50–74 years",
            MeasureIDEnum.HEARING: "Hearing disability among adults",
            MeasureIDEnum.VISION: "Vision disability among adults",
            MeasureIDEnum.COGNITION: "Cognitive disability among adults",
            MeasureIDEnum.MOBILITY: "Mobility disability among adults",
            MeasureIDEnum.SELFCARE: "Self-care disability among adults",
            MeasureIDEnum.INDEPLIVE: "Independent living disability among adults",
            MeasureIDEnum.DISABILITY: "Any disability among adults",
            MeasureIDEnum.ISOLATION: "Feeling socially isolated among adults",
            MeasureIDEnum.FOODSTAMP: "Received food stamps in the past 12 months among adults",
            MeasureIDEnum.FOODINSECU: "Food insecurity in the past 12 months among adults",
            MeasureIDEnum.HOUSINSECU: "Housing insecurity in the past 12 months among adults",
            MeasureIDEnum.SHUTUTILITY: "Utility services threat in the past 12 months among adults",
            MeasureIDEnum.LACKTRPT: "Lack of reliable transportation in the past 12 months among adults",
            MeasureIDEnum.EMOTIONSPT: "Lack of social and emotional support among adults",
        }
        return descriptions[self.measure_id]
    
    @classmethod
    def get_description(cls, measure_id: MeasureIDEnum) -> str:
        """Static method to get description without creating an instance"""
        temp = cls(measure_id=measure_id)
        return temp.description

class GeoTypeEnum(str, Enum):
    """Enumeration of geographic breakdown types"""
    
    STATE = "state"
    COUNTY = "county"
    CENSUS = "census"
    ZCTA = "zcta"
    PLACES = "places"

class GeoType(BaseModel):
    """Model for geographic breakdown types with descriptions"""
    
    geo_type: GeoTypeEnum = Field(..., description="Geographic breakdown type")
    
    @property
    def description(self) -> str:
        """Get the human-readable description for the geographic type"""
        descriptions = {
            GeoTypeEnum.STATE: "State-level geographic breakdown",
            GeoTypeEnum.COUNTY: "County-level geographic breakdown",
            GeoTypeEnum.CENSUS: "Census tract-level geographic breakdown",
            GeoTypeEnum.ZCTA: "ZIP Code Tabulation Area (ZCTA) geographic breakdown",
            GeoTypeEnum.PLACES: "City and Census Designated Places geographic breakdown",
        }
        return descriptions[self.geo_type]

class DataValueTypeIDEnum(str, Enum):
    """Enumeration of data value type IDs"""
    
    CRDPRV = "CrdPrv"
    AGEADJPRV = "AgeAdjPrv" 

class DataValueTypeID(BaseModel):
    """Model for data value type identifiers with descriptions"""
    
    datavaluetype_id: DataValueTypeIDEnum = Field(..., description="Data value type identifier")
    
    @property
    def description(self) -> str:
        """Get the human-readable description for the data value type ID"""
        descriptions = {
            DataValueTypeIDEnum.CRDPRV: "Crude prevalence",
            DataValueTypeIDEnum.AGEADJPRV: "Age-adjusted prevalence",
        }
        return descriptions[self.datavaluetype_id]

class PlacesParams(BaseModel):
    year: str = Field(..., description="The year of the data release (e.g., 2024).")
    measureid: MeasureID = Field(..., description="The health measure identifier.")
    geo: GeoType = Field(..., description="The geographic breakdown type.")
    datavaluetypeid: DataValueTypeID = Field(..., description="The data value type identifier.")
    locationname: Optional[Union[str, List[str]]] = Field(None, description="The name of the location (e.g., county name). Can be a single string or a list of strings.")

    def to_api_params(self):
        """Convert the PlacesParams instance to a dictionary of API parameters."""

        params = {
            "measureid": self.measureid.measure_id.value,
            "datavaluetypeid": self.datavaluetypeid.datavaluetype_id.value,
        }
        if self.locationname:
            if isinstance(self.locationname, list):
                params["locationname"] = ",".join(self.locationname)
            else:
                params["locationname"] = self.locationname
        
        # set parameters to be returned based off geography
        GEO = self.geo.geo_type.value
        if GEO == 'county':
            params["$select"] = 'stateabbr,statedesc,locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'
        elif GEO == 'census': 
            params["$select"] = 'stateabbr,statedesc,countyname,locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'
        elif GEO == 'zcta':
            params["$select"] = 'locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'
        elif GEO == 'places':
            params["$select"] = 'stateabbr,statedesc,locationname,data_value,low_confidence_limit,high_confidence_limit,totalpopulation'

        return params

