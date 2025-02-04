from pydantic import BaseModel, Field
from typing import Literal

class CountryData(BaseModel):
    country: str
    assessment_year: int = Field(ge=2023, le=2024)
    EP_1: Literal["Yes", "No", "Partial", ""] 
    EP_2: Literal["Yes", "No", "Partial", ""]
    EP_3: Literal["Yes", "No", "Partial", ""]
    CP_1: Literal["Yes", "No", "Partial", ""]
    CP_2: Literal["Yes", "No", "Partial", "Exempt", ""]
    CP_3: Literal["Yes", "No", "Partial", "Exempt", ""]
    CP_4: Literal["Yes", "No", "Partial", "Exempt", ""]
    CP_5: Literal["Yes", "No", "Partial", "Exempt", ""]
    CP_6: Literal["Yes", "No", "Partial", "Exempt", ""]
    CF_1: Literal["Yes", "No", "Partial", "Exempt", ""]
    CF_2: Literal["Yes", "No", "Partial", "Exempt", ""]
    CF_3: Literal["Yes", "No", "Partial", "Exempt", ""]
    CF_4: Literal["Yes", "No", "Partial", "Exempt", ""]
    
class Area(BaseModel):
    indicators: dict[str, str]

class CountryData(BaseModel):
    country: str
    assessment_year: int
    EP: Area
    CP: Area
    CF: Area

