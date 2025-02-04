from pydantic import BaseModel, Field
from typing import Literal, List, Optional

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
    metrics: Optional[List[Metric]]
    source: Optional[IndicatorSource] = None
    

class Area(BaseModel):
    name: str
    indicators: Optional[List[Indicator]]

class CountryData(BaseModel):
    country: str
    assessment_year: int = Field(ge=2023, le=2024)
    areas: Optional[List[Area]]
    # EP_1: Literal["Yes", "No", "Partial", ""] 
    # EP_2: Literal["Yes", "No", "Partial", ""]
    # EP_3: Literal["Yes", "No", "Partial", ""]
    # CP_1: Literal["Yes", "No", "Partial", ""]
    # CP_2: Literal["Yes", "No", "Partial", "Exempt", ""]
    # CP_3: Literal["Yes", "No", "Partial", "Exempt", ""]
    # CP_4: Literal["Yes", "No", "Partial", "Exempt", ""]
    # CP_5: Literal["Yes", "No", "Partial", "Exempt", ""]
    # CP_6: Literal["Yes", "No", "Partial", "Exempt", ""]
    # CF_1: Literal["Yes", "No", "Partial", "Exempt", ""]
    # CF_2: Literal["Yes", "No", "Partial", "Exempt", ""]
    # CF_3: Literal["Yes", "No", "Partial", "Exempt", ""]
    # CF_4: Literal["Yes", "No", "Partial", "Exempt", ""]

