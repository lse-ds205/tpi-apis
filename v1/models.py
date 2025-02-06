from pydantic import BaseModel
from typing import Literal

class CountryData(BaseModel):
    country: str
    assessment_year: int = Field(ge=2023, le=2024)
    # Only allow specific values for assessment results
    EP_1: Literal["Yes", "No", "Partial", ""] 
    EP_2: Literal["Yes", "No", "Partial", ""]
    EP_3: Literal["Yes", "No", "Partial", ""]
    CP_1: Literal["Yes", "No", "Partial", ""]
    CP_2: Literal['Partial','Exempt', 'No' ,'Yes','']
    CP_3: Literal['No' ,'Exempt' ,'Partial' ,'Yes','']
    CP_4: Literal['Partial' ,'Exempt' ,'No','']
    CP_5: Literal["Yes", "No", "Partial", ""] 
    CP_6: Literal["Yes", "No", "Partial", ""]
    CF_1: Literal['Partial','Exempt', 'No' ,'Yes','']
    CF_2: Literal['No' ,'Exempt' ,'Partial' ,'Yes','']
    CF_3: Literal["Yes", "No", "Partial", ""] 
    CF_4: Literal["Not applicable", 'nan', ""] 

class Indicator(BaseModel):
    assessment: str
    metric: Metric


class Metric(BaseModel):
    name: str
    value: str