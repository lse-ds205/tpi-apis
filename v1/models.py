from pydantic import BaseModel, Field
from typing import Union, List

# Data input error - not sending a number into year do it on the front-end (typos)
# Country not included in the data or year not included in the data to be included in the backend

class Metric(BaseModel):
    name: str
    value: str

class Indicator(BaseModel):
    name: str
    assessment: str
    metrics: List[Union[Metric, str]] = Field(
        default_factory=list)

class Area(BaseModel):
    name: str
    assessment: str
    indicators: List[Indicator]

class Pillar(BaseModel):
    name: str = Field(..., pattern="^(EP|CP|CF)$")
    areas: List[Area]

class CountryDataResponse(BaseModel):
    country: str
    assessment_year: int
    pillars: List[Pillar]

#None in python is represented as Null in JSON