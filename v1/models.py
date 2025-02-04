from pydantic import BaseModel
from typing import List, Optional

'''
Ideal data structure is:

metadata:{country, assessment_year}
pillars -> {asssessment (AREA)} -> each item of list a dict {name, assessment, indicators} 
indicators 
source


'''

class Metric(BaseModel):
    name: str
    value: Optional[str] = None

class Indicator(BaseModel):
    name: str
    assessment: Optional[str] = None
    metrics: Optional[List[Metric]] = None
    source: Optional[str] = None

class Area(BaseModel):
    name: str
    assessment: Optional[str] = None
    indicators: List[Indicator] = []

class Pillar(BaseModel):
    name: str
    areas: List[Area] = []

class Metadata(BaseModel):
    country: str
    assessment_year: int

class ResponseData(BaseModel):
    metadata: Metadata
    pillars: List[Pillar] = []

class ErrorResponseData(BaseModel):
    "some sort of error structuring"
    