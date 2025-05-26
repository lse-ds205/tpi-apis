"""
Filter models for API endpoints.

This module provides Pydantic models for filtering data across different endpoints.
These models are designed to be used with FastAPI's dependency injection system.
"""
from fastapi import Query
from typing import Optional, Union, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class RangeFilter(BaseModel):
    """Base model for range-based filters."""
    min: Optional[float] = Field(None, description="Minimum value")
    max: Optional[float] = Field(None, description="Maximum value")

    @field_validator('min', 'max')
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

    @field_validator('start_date', 'end_date')
    def validate_date_range(cls, v, values):
        if v is not None and values.get('start_date') is not None and values.get('end_date') is not None:
            if values['start_date'] > values['end_date']:
                raise ValueError("start_date must be before or equal to end_date")
        return v
    
class CompanyFilters(BaseModel):
    geography: Optional[str] = Field(
        None,
        description="Filter by geography",
        json_schema_extra={"example": "United States of America"}
    )
    geography_code: Optional[str] = Field(
        None,
        description="Filter by geography code", 
        json_schema_extra={"example": "USA"}
    )
    sector: Optional[str] = Field(
        None,
        description="Filter by sector",
        json_schema_extra={"example": "Cement"}
    )
    ca100_focus_company: Optional[bool] = Field(
        None,
        description="Filter for CA100 focus companies",
        json_schema_extra={"example": True}
    )
    large_medium_classification: Optional[str] = Field(
        None,
        description="Filter by company size classification",
        json_schema_extra={"example": "Large"}
    )
    isins: Optional[Union[list[str], str]] = Field(
        default=None,
        description="Filter by ISIN identifiers",
        json_schema_extra={"example": ["US0378331005", "GB00B03MLX29"]}
    )
    sedol: Optional[Union[list[str], str]] = Field(
        default=None,
        description="Filter by SEDOL identifiers",
        json_schema_extra={"example": ["2000019", "B03MLX2"]}
    )


class CPBenchmarkFilter(BaseModel):
    benchmark_id: Optional[List[str]] = Query(None, description="Filter by Benchmark_id")

class CPRegionalFilter(BaseModel):
    regional_benchmark_id:  Optional[List[str]] = Query(None, description="Filter by Regional Benchmark ID"),

class MQFilter(BaseModel):
    mq_levels: Optional[List[int]] = Query(None, description="Filter by MQ Level")
    level: Optional[List[int]] = Query(None, description="Filter by Overall Management Level")
    assessment_year: Optional[int] = Query(None, description="Filter by assessment year")