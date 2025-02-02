from pydantic import BaseModel, Field
from typing import Literal  # This helps us limit possible values

class Area(BaseModel):
    indicators: dict[str, str]

class CountryData(BaseModel):
    country: str
    # Only allow years between 2023-2024
    assessment_year: int = Field(ge=2023, le=2024)
    # Only allow specific values for assessment results
    EP_1: Literal["Yes", "No", "Partial", ""] 
    EP_2: Literal["Yes", "No", "Partial", ""]
    EP_3: Literal["Yes", "No", "Partial", ""]
    CP_1: Literal["Yes", "No", "Partial", ""]
    CP_2: Literal["Yes", "No", "Partial", "", "Exempt"]
    CP_3: Literal["Yes", "No", "Partial", "", "Exempt"]
    CP_4: Literal["No", "Partial", "", "Exempt"]
    CP_5: Literal["Yes", "No", "Partial", ""]
    CP_6: Literal["Yes", "No", "Partial", ""]
    CF_1: Literal["Yes", "No", "Partial", "", "Exempt"]
    CF_2: Literal["Yes", "No", "Partial", "", "Exempt"]
    CF_3: Literal["Yes", "No", "Partial", ""]
    CF_4: Literal["Not applicable", "nan",""]