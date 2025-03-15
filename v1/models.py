from pydantic import BaseModel, Field
from typing import Union, List, Optional

class MetricSource(BaseModel):
    source_name: Optional[str]

class Metric(BaseModel):
    name: str
    value: str
    source: Optional[MetricSource] = None

class IndicatorSource(BaseModel):
    source_name: Optional[str]

class Indicator(BaseModel):
    name: str
    assessment: str
    metrics: List[Union[Metric, str]] = Field(default_factory=list)
    source: Optional[IndicatorSource] = None

class Area(BaseModel):
    name: str
    assessment: str
    indicators: List[Indicator]

class Pillar(BaseModel):
    name: str = Field(..., pattern="^(EP|CP|CF)$")
    areas: List[Area]

class CountryDataResponse(BaseModel):
    country: str
    assessment_year: int = Field(ge=2023, le=2024)
    pillars: List[Pillar]
