from pydantic import BaseModel, Field
from typing import Literal  # This helps us limit possible values

# This Area model is nested in the CountryData model, analogue to the nested dictionaries (see app.py)
class Area(BaseModel):
    indicators: dict[str, Literal["Yes", "No", "Partial", "Exempt", "Not applicable", ""]]

class CountryData2(BaseModel):
    country: str

    # Only allow years between 2023-2024 -> if I enter 2022, I now get an Internal Server Error
    assessment_year: int = Field(ge=2023, le=2024)
    
    # Area model nested in CountryData model
    EP: Area
    CP: Area
    CF: Area