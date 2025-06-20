"""
Filter models for API endpoints.

This module provides Pydantic models for filtering data across different endpoints.
These models are designed to be used with FastAPI's dependency injection system.
"""
from fastapi import Query
from typing import Optional, Union, List, Dict, Any
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

class CPBenchmarkFilter(BaseModel):
    benchmark_id: Optional[List[str]] = Query(None, description="Filter by Benchmark_id")

class CPRegionalFilter(BaseModel):
    regional_benchmark_id:  Optional[List[str]] = Query(None, description="Filter by Regional Benchmark ID"),

class MQFilter(BaseModel):
    mq_levels: Optional[List[int]] = Query(None, description="Filter by MQ Level")
    level: Optional[List[int]] = Query(None, description="Filter by Overall Management Level")
    assessment_year: Optional[int] = Query(None, description="Filter by assessment year")


def build_company_filter_conditions(filters: CompanyFilters) -> tuple[str, Dict[str, Any]]:
    """
    Build WHERE conditions and parameters for company filtering.
    
    Args:
        filters (CompanyFilters): Company filter parameters
        
    Returns:
        tuple[str, Dict[str, Any]]: WHERE clause string and parameters dictionary
    """
    conditions = []
    params = {}
    
    if filters.geography:
        conditions.append("c.geography = :geography")
        params["geography"] = filters.geography
        
    if filters.geography_code:
        conditions.append("c.geography_code = :geography_code")
        params["geography_code"] = filters.geography_code
        
    if filters.sector:
        conditions.append("c.sector_name = :sector")
        params["sector"] = filters.sector
        
    if filters.ca100_focus_company is not None:
        if filters.ca100_focus_company:
            conditions.append("c.ca100_focus = 'Yes'")
        else:
            conditions.append("c.ca100_focus != 'Yes'")
            
    if filters.large_medium_classification:
        conditions.append("c.size_classification = :size_classification")
        params["size_classification"] = filters.large_medium_classification
        
    if filters.isins:
        if isinstance(filters.isins, str):
            conditions.append("c.isin ILIKE :isin")
            params["isin"] = f"%{filters.isins}%"
        else:
            isin_conditions = []
            for i, isin in enumerate(filters.isins):
                isin_conditions.append(f"c.isin ILIKE :isin_{i}")
                params[f"isin_{i}"] = f"%{isin}%"
            if isin_conditions:
                conditions.append(f"({' OR '.join(isin_conditions)})")
                
    if filters.sedol:
        if isinstance(filters.sedol, str):
            conditions.append("c.sedol ILIKE :sedol")
            params["sedol"] = f"%{filters.sedol}%"
        else:
            sedol_conditions = []
            for i, sedol in enumerate(filters.sedol):
                sedol_conditions.append(f"c.sedol ILIKE :sedol_{i}")
                params[f"sedol_{i}"] = f"%{sedol}%"
            if sedol_conditions:
                conditions.append(f"({' OR '.join(sedol_conditions)})")
    
    where_clause = " AND " + " AND ".join(conditions) if conditions else ""
    return where_clause, params