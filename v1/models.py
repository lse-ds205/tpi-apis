from pydantic import BaseModel
from typing import List, Optional

class Metric(BaseModel):
    name: str
    value: Optional[str] = None

class Indicator(BaseModel):
    name: str
    assessment: str
    metrics: Optional[Metric] = None
    source: Optional[str] = None
    indicators: Optional[List['Indicator']] = None  # Allow for nested indicators

class Area(BaseModel):
    name: str
    assessment: str
    indicators: List[Indicator]

class CountryData(BaseModel):
    country: str
    assessment_year: int
    EP: Area
    CP: Area
    CF: Area

class Pillar(BaseModel):
    name: str
    areas: List[Area]

class Metadata(BaseModel):
    assessment_year: int
    country: str

class ResponseData(BaseModel):
    pillars: List[Pillar]