from pydantic import BaseModel, Field
from typing import Literal

class Metric(BaseModel):
    name: str
    value: str

class Indicator(BaseModel):
    name: str
    assessment: Literal['Exempt', 'No', 'Not applicable', 'Partial', 'Yes', '']
    metrics: list[Metric]

class Area(BaseModel):
    name: str
    assessment: Literal['Exempt', 'No', 'Not applicable', 'Partial', 'Yes', '']
    indicators: str

class Pillar(BaseModel):
    name: Literal['EP', 'CP', 'CF']
    areas: list[Area]

class CountryData(BaseModel):
    pillars: list[Pillar]