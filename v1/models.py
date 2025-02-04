from pydantic import BaseModel
from typing import List, Dict, Optional, Literal

class CountryData(BaseModel):
    country: str
    # Only allow years between 2023-2024
    assessment_year: int = Field(ge=2023, le=2024)
    # Only allow specific values for assessment results
    EP_1: Literal["Yes", "No", "Partial", ""] 
    EP_2: Literal["Yes", "No", "Partial", ""]
    EP_3: Literal["Yes", "No", "Partial", ""]

class Metric(BaseModel):
    name: str
    value: Optional[str] = None

class Indicator(BaseModel):
    name: str
    asessment:str
    metric: Optional[list[Metric]] = None
    source: Optional[str] = None

class Area (BaseModel):
    name: str
    assessment: Optional[str] = None
    indicator: List[Indicator] = []

class Pilar(BaseModel):
    name: str
    area: List[Area] = []

class Metadata(BaseModel):
    assessment_year: int
    country: str

class ResponseData(BaseModel):
    metadata: Metadata
    pilar: List[Pilar] = []