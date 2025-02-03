from pydantic import BaseModel, Field
from typing import Literal

class Metric(BaseModel):
    name: str
    value: str

class Indicator(BaseModel):
    name: str
    assessment: Literal['Exempt', 'No', 'Not applicable', 'Partial', 'Yes', '']
    metrics: Metric

class Area(BaseModel):
    name: str
    assessment: Literal['Exempt', 'No', 'Not applicable', 'Partial', 'Yes', '']
    indicators: Indicator

class Pillar(BaseModel):
    name: Literal['EP', 'CP', 'CF']
    areas: Area

class CountryData(BaseModel):
    pillars: Pillar