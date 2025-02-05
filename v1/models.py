from pydantic import BaseModel, Field
from typing import Literal

class Area(BaseModel):
    indicators: dict[str, str]

class CountryData(BaseModel):
    country: str
    assessment_year: int
    EP: Area
    CP: Area
    CF: Area

#class CountryData(BaseModel):
#    country: str

    # Only allow years between 2023-2024
#   assessment_year: int = Field(ge=2023, le=2024)

    # Only allow specific values for assessment results
#    EP_1: Literal["Yes", "No", "Partial", ""] 
#    EP_2: Literal["Yes", "No", "Partial", ""]
 #   EP_3: Literal["Yes", "No", "Partial", ""]
#
 #   CP_1: Literal['Yes', 'No', 'Partial', '']
  #  CP_2: Literal['Partial', 'Exempt', 'No', 'Yes', '']
    #CP_3: Literal['No', 'Exempt', 'Partial', 'Yes', '']
   # CP_4: Literal['Partial', 'Exempt', 'No', ""]
#    CP_5: Literal['Partial', 'Yes', 'No', ""]
 #   CP_6: Literal['Partial', 'No', 'Yes', ""]
  #  CF_1: Literal['Partial', 'Exempt', 'No', 'Yes', '']
   # CF_2: Literal['Exempt', 'Partial', 'No', 'Yes', '']
    #CF_3: Literal['Yes', 'No', 'Partial', '']
 #   CF_4: Literal['Not applicable','']