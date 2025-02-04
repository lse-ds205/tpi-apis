from pydantic import BaseModel, Field
from typing import Literal, Union

class Metric(BaseModel):
    name: str
    value: str

class Indicator(BaseModel):
    name: str
    assessment: Literal['Not Applicable',
                        'No Data',
                        'Not applicable',
                        'Yes',
                        'No',
                        'No data',
                        'Exempt']
    metrics: Union[Metric, Literal[""]]

class Area(BaseModel):
    name: str
    assessment: Literal['Exempt', 'No', 'Not applicable', 'Partial', 'Yes', '']
    indicators: list[Indicator]

class Pillar(BaseModel):
    name: Literal['EP', 'CP', 'CF']
    areas: list[Area]

class Metadata(BaseModel):
    country: str
    assessment_year: int = Field(ge=2023, le=2024)
    
class CountryData(BaseModel):
    metadata: Metadata
    pillars: list[Pillar]