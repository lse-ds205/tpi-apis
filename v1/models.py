from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

class Metric(BaseModel):
    name: str
    value: Optional[str] = None

class Indicator(BaseModel):
    name: str
    asessment:str
    metric: Optional[List[Metric]] = None
    source: Optional[str] = None

class Area (BaseModel):
    indicators: dict[str, str]

class CountryData(BaseModel):
    country: str
    assessment_year: int
    EP: Area
    CP: Area
    CF: Area

class Pillar(BaseModel):
    name: str
    area: List[Area] = []

class Metadata(BaseModel):
    assessment_year: int
    country: str

class ResponseData(BaseModel):
    metadata: Metadata
    pillar: List[Pillar] = []