from pydantic import BaseModel, Field
from typing import List, Optional

class Metric(BaseModel):
    name: str
    value: Optional[str] = None

class Indicator(BaseModel):
    name: str
    assessment: str
    metrics: Optional[Metric] = Field(default=None, exclude_none=True)
    
    model_config = {
        "json_exclude_none": True  # This will exclude None values from JSON output
    }

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