from pydantic import BaseModel, Field
from typing import Literal, Union

class Metric(BaseModel):
    name: str
    value: str

class Indicator(BaseModel):
    name: str
    assessment: Literal['Exempt', 'No', 'Not applicable', 'Partial', 'Yes', '']
    metrics: Union[Metric, Literal[""]]

class Area(BaseModel):
    name: str
    assessment: Literal['Exempt', 'No', 'Not applicable', 'Partial', 'Yes', '']
    indicators: Union[list[Indicator], Literal[""]]

class Pillar(BaseModel):
    name: Literal['EP', 'CP', 'CF']
    areas: Union[list[Area], Literal[""]]

class CountryData(BaseModel):
    pillars: Union[list[Pillar], Literal[""]]