from pydantic import BaseModel

class Metric(BaseModel):
    name: str
    value: str
    
class CountryData(BaseModel):
    country: str
    assessment_year: int
    EP_1: str 
    EP_2: str
    EP_3: str
    CP_1: str
    CP_2: str
    CP_3: str
    CP_4: str
    CP_5: str
    CP_6: str
    CF_1: str
    CF_2: str
    CF_3: str
    CF_4: str

class Indicator(BaseModel):
    assessment: str
    metric: Metric


from pydantic import BaseModel

from .models import CountryData 