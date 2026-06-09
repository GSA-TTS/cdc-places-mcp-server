from enum import Enum 

class MeasureID(str, Enum):
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
    LONELINESS = "LONELINESS"
