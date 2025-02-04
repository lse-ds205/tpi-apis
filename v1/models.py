from pydantic import BaseModel, Field
from typing import List, Union

# CountryDataResponse
# ├── country: str
# ├── assessment_year: int
# └── pillars: List[Pillar]
#     ├── name: str
#     └── areas: List[Area]
#         ├── name: str
#         ├── assessment: str
#         └── indicators: List[Indicator]
#             ├── assessment: str
#             └── metric: Metric
#                 ├── name: str
#                 └── value: str

# L5
class Metric(BaseModel):
    name: str
    value: str

# L4
class Indicator(BaseModel):
    assessment: str
    metric: Metric

# L3
class Area(BaseModel):
    name: str
    assessment: str
    indicators: List[Indicator]

# L2
class Pillar(BaseModel):
    name: str = Field(..., pattern="^(EP|CP|CF)$")
    areas: List[Area]

# L1
class CountryDataResponse(BaseModel):
    country: str
    assessment_year: int
    pillars: List[Pillar]

# L0
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