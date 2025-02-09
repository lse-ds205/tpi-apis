from pydantic import BaseModel, Field
from typing import Literal

class CountryData(BaseModel):
     country: str
    # Only allow years between 2023-2024
     assessment_year: int = Field(ge=2023, le=2024)
    # Only allow specific values for assessment results
     EP_1: Literal["Yes", "No", "Partial", ""] 
     EP_2: Literal["Yes", "No", "Partial", ""]
     EP_3: Literal["Yes", "No", "Partial", ""]

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
