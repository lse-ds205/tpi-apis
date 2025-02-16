from pydantic import BaseModel, Field
from typing import List, Literal  # This helps us limit possible values

# Model for Week 2's class
# This Area model is nested in the CountryData model, analogue to the nested dictionaries (see app.py)
class Area(BaseModel):
    indicators: dict[str, Literal["Yes", "No", "Partial", "Exempt", "Not applicable", ""]]

class CountryData1(BaseModel):
    country: str

    # Only allow years between 2023-2024 -> if I enter 2022, I now get an Internal Server Error
    assessment_year: int = Field(ge=2023, le=2024)
    
    # Area model nested in CountryData model
    EP: Area
    CP: Area
    CF: Area

# Model for the Formative Exercise (Week 2 and 3)
class Metric(BaseModel):
    name: str
    value: str

class Indicator(BaseModel):
    name: str
    assessment: str
    metrics: List[Metric]

class Area(BaseModel):
    name: str
    assessment: str
    indicators: List[Indicator]

class Pillar(BaseModel):
    name: Literal["EP", "CP", "CF", ""]
    areas: List[Area]

class CountryData2(BaseModel):
    pillars: List[Pillar]