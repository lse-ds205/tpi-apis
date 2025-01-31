from pydantic import BaseModel

class CountryData(BaseModel):
    country: str
    assessment_year: int
    EP1: str 
    EP2: str
    EP3: str
    CP1: str
    CP2: str,
    CP3: str,
    CP4: str,
    CP5: str,
    CP6: str,
    CF1: str,
    CF2: str,
    CF3: str,
    CF4: str