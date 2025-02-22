from pydantic import BaseModel
from typing import Literal  # This helps us limit possible values

class CountryData(BaseModel):
    country: str
    # Only allow years between 2023-2024
    assessment_year: int = Field(ge=2023, le=2024)
    # Only allow specific values for assessment results
    EP_1: Literal["Yes", "No", "Partial", ""] 
    EP_2: Literal["Yes", "No", "Partial", ""]
    EP_3: Literal["Yes", "No", "Partial", ""]

# ✅ Define Metric first
class Metric(BaseModel):
    name: str
    value: float

# Now reference Metric in Indicator
class Indicator(BaseModel):
    assessment: str
    metric: Metric
