from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict

class Metrics(BaseModel):
    name: str
    value: str

class Indicators(BaseModel):
    name: str
    assessment: str
    metrics: Optional[list[Metrics]] = None

class Area(BaseModel):
    name: str
    assessment: Optional[str] = None
    indicators: List[Indicators]

class Pillars(BaseModel):
    name: str
    areas: List[Area]

class CountryData(BaseModel):
    country: str
    assessment_year: int = Field(ge=2023, le=2024)
    pillars: Optional[List[Pillars]]