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

# CompanyFilters to work with FastAPI dependency injection
class CompanyFilters:
    def __init__(
        self,
        geography: Optional[str] = Query(None, description="Filter by geography"),
        geography_code: Optional[str] = Query(None, description="Filter by geography code"),
        sector: Optional[str] = Query(None, description="Filter by sector"),
        ca100_focus_company: Optional[bool] = Query(None, description="Filter for CA100 focus companies"),
        large_medium_classification: Optional[str] = Query(None, description="Filter by company size classification"),
        isins: Optional[str] = Query(None, description="Filter by ISIN identifiers (comma-separated)"),
        sedol: Optional[str] = Query(None, description="Filter by SEDOL identifiers (comma-separated)")
    ):
        self.geography = geography
        self.geography_code = geography_code
        self.sector = sector
        self.ca100_focus_company = ca100_focus_company
        self.large_medium_classification = large_medium_classification
        # Convert comma-separated strings to lists
        self.isins = isins.split(',') if isins else None
        self.sedol = sedol.split(',') if sedol else None

class CPBenchmarkFilter:
    def __init__(
        self,
        benchmark_id: Optional[str] = Query(None, description="Filter by Benchmark_id (comma-separated)")
    ):
        self.benchmark_id = benchmark_id.split(',') if benchmark_id else None

class CPRegionalFilter:
    def __init__(
        self,
        regional_benchmark_id: Optional[str] = Query(None, description="Filter by Regional Benchmark ID (comma-separated)")
    ):
        self.regional_benchmark_id = regional_benchmark_id.split(',') if regional_benchmark_id else None

class MQFilter:
    def __init__(
        self,
        mq_levels: Optional[str] = Query(None, description="Filter by MQ Level (comma-separated integers)"),
        level: Optional[str] = Query(None, description="Filter by Overall Management Level (comma-separated integers)"),
        assessment_year: Optional[int] = Query(None, description="Filter by assessment year")
    ):
        # Convert comma-separated strings to lists of integers
        self.mq_levels = [int(x.strip()) for x in mq_levels.split(',') if x.strip().isdigit()] if mq_levels else None
        self.level = [int(x.strip()) for x in level.split(',') if x.strip().isdigit()] if level else None
        self.assessment_year = assessment_year