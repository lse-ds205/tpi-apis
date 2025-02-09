from typing import List, Optional
from pydantic import BaseModel

class CountryData(BaseModel):
    country: str
    assessment_year: int
    EP_1: str 
    EP_2: str
    EP_3: str
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
    value: Optional[str]=None


class Indicator(BaseModel):
    name: str
    assessment: Optional[str]=None
    metrics: Optional[List[Metric]]=None
    source: Optional[str]=None

class Area(BaseModel):
    name: str
    assessment: Optional[str]=None
    indicators: List[Indicator] = []

class Pillar(BaseModel):
    name: str
    area: List[Area] =[]

class Metadata(BaseModel):
    metadata: str
    assessment_year: int

class ResponseData(BaseModel):
    metadata: Metadata
    pillars: List[Pillar]=[]

class ErrorResponse(BaseModel):
    message: str
    details: dict={}

