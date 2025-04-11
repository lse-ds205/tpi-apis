"""
Filter models for API endpoints.

This module provides Pydantic models for filtering data across different endpoints.
These models are designed to be used with FastAPI's dependency injection system.
"""
from fastapi import Query
from typing import Optional, Union, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

class RangeFilter(BaseModel):
    """Base model for range-based filters."""
    min: Optional[float] = Field(None, description="Minimum value")
    max: Optional[float] = Field(None, description="Maximum value")

    @validator('min', 'max')
    def validate_range(cls, v, values):
        if v is not None and 'min' in values and 'max' in values:
            if values['min'] is not None and values['max'] is not None:
                if values['min'] > values['max']:
                    raise ValueError("min must be less than or equal to max")
        return v

class DateRangeFilter(BaseModel):
    """Filter for date ranges."""
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")

    @validator('start_date', 'end_date')
    def validate_date_range(cls, v, values):
        if v is not None and 'start_date' in values and 'end_date' in values:
            if values['start_date'] is not None and values['end_date'] is not None:
                if values['start_date'] > values['end_date']:
                    raise ValueError("start_date must be before or equal to end_date")
        return v
    
class CompanyFilters(BaseModel):
    geography: Optional[str] = Field(
        None,
        description="Filter by geography",
        example="United States of America"
    )
    geography_code: Optional[str] = Field(
        None,
        description="Filter by geography code", 
        example="USA"
    )
    sector: Optional[str] = Field(
        None,
        description="Filter by sector",
        example="Cement"
    )
    ca100_focus_company: Optional[bool] = Field(
        None,
        description="Filter for CA100 focus companies",
        example=True
    )
    large_medium_classification: Optional[str] = Field(
        None,
        description="Filter by company size classification",
        example="Large"
    )
    isins: Optional[Union[list[str], str]] = Field(
        default=None,
        description="Filter by ISIN identifiers",
        example=["US0378331005", "GB00B03MLX29"]
    )
    sedol: Optional[Union[list[str], str]] = Field(
        default=None,
        description="Filter by SEDOL identifiers",
        example=["2000019", "B03MLX2"]
    )


class CPFilter(BaseModel):
    # for the years we want to have min or max float values
    # regional benchmark id
    # alignment takes 2025, 2035, 2050, 2027, 2028


    """Filter parameters for Carbon Performance endpoints."""
    alignment_2035: Optional[list[str]] = Field(
        None,
        description="Filter by 2035 alignment status",
        example=["1.5C", "2C", "3C"]
    )
    alignment_2050: Optional[list[str]] = Field(
        None,
        description="Filter by 2050 alignment status",
        example=["1.5C", "2C", "3C"]
    )
    target_years: Optional[list[int]] = Field(
        None,
        description="Filter by target years",
        example=[2025, 2035, 2050]
    )
    score_range: Optional[RangeFilter] = Field(
        None,
        description="Filter by score range"
    )
    assessment_date: Optional[DateRangeFilter] = Field(
        None,
        description="Filter by assessment date range"
    )
    include_regional: Optional[bool] = Field(
        False,
        description="Include regional assessments in the response"
    )

# class CombinedFilter(BaseModel):
#     """Combined filter parameters for endpoints that need multiple filter types."""
#     company: Optional[CompanyFilter] = Field(
#         None,
#         description="Company-specific filters"
#     )
#     cp: Optional[CPFilter] = Field(
#         None,
#         description="Carbon Performance filters"
#     )
#     mq: Optional[MQFilter] = Field(
#         None,
#         description="Management Quality filters"
#     )
#     include_related: Optional[bool] = Field(
#         False,
#         description="Include related data in the response"
#     ) 