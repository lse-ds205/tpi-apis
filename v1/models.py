from pydantic import BaseModel, Field
from typing import Literal  # This helps us limit possible values

class Area(BaseModel):
    indicators: dict[str, str]

class CountryData(BaseModel):
    country: str
    assessment_year: int
    EP: Area
    CP: Area
    CF: Area