from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

class CountryData(BaseModel):
    country: str
    # Only allow years between 2023-2024
    assessment_year: int = Field(ge=2023, le=2024)
    # Only allow specific values for assessment results
    EP_1: Literal["Yes", "No", "Partial", ""] 
    EP_2: Literal["Yes", "No", "Partial", ""]
    EP_3: Literal["Yes", "No", "Partial", ""]
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

class Metric(BaseModel):
    name: str
    value: Optional[str] = None

class Indicator(BaseModel):
    name: str
    asessment:str
    metric: Optional[List[Metric]] = None
    source: Optional[str] = None

class Area (BaseModel):
    name: str
    assessment: Optional[str] = None
    indicator: List[Indicator] = []

class Pillar(BaseModel):
    name: str
    area: List[Area] = []

class Metadata(BaseModel):
    assessment_year: int
    country: str

class ResponseData(BaseModel):
    metadata: Metadata
    pillar: List[Pillar] = []