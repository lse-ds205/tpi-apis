"""
This module provides FastAPI endpoints for retrieving company data and assessments.
It loads the company assessment dataset from a CSV file, normalizes the data,
and exposes endpoints for listing companies, retrieving company details, history,
and comparing performance between assessment cycles.
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
from fastapi import APIRouter, HTTPException, Query, Request, Depends
import pandas as pd
from datetime import datetime
from typing import Union, List, Dict, Any
from pathlib import Path
from middleware.rate_limiter import limiter
from schemas import (
    CompanyBase,
    CompanyDetail,
    CompanyListResponse,
    CompanyHistoryResponse,
    PerformanceComparisonResponse,
    PerformanceComparisonInsufficientDataResponse,
)
from utils.utils import normalize_company_id
from utils.database_manager import DatabaseManagerFactory
from utils.filters import CompanyFilters, build_company_filter_conditions

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
router = APIRouter(tags=["Company Endpoints"])

# SQL file paths
SQL_DIR = Path(__file__).parent.parent / "sql" / "tpi" / "queries"

# --------------------------------------------------------------------------
# Endpoint: GET /companies - List All Companies with Pagination
# --------------------------------------------------------------------------
@router.get("/companies", response_model=CompanyListResponse)
@limiter.limit("100/minute")
async def get_all_companies(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Results per page"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """
    Retrieve a paginated list of all companies and their latest assessments.
    """
    db_manager = DatabaseManagerFactory.get_manager("tpi_api")
    
    # Build filter conditions
    where_clause, params = build_company_filter_conditions(filter)
    
    # Count total companies using SQL template
    try:
        count_result = db_manager.execute_sql_template(
            SQL_DIR / "count_all_companies.sql",
            params,
            where_clause
        )
        total_companies = int(count_result.iloc[0]['total'])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error counting companies: {str(e)}"
        )
    
    # Get paginated companies with latest assessment data using SQL template
    offset = (page - 1) * per_page
    params.update({"limit": per_page, "offset": offset})
    
    try:
        companies_result = db_manager.execute_sql_template(
            SQL_DIR / "get_all_companies.sql",
            params,
            where_clause
        )
        
        companies = []
        for _, row in companies_result.iterrows():
            companies.append(CompanyBase(
                company_id=normalize_company_id(row["company_name"]),
                name=row["company_name"],
                sector=row.get("sector", "N/A"),
                geography=row.get("geography", "N/A"),
                latest_assessment_year=int(pd.to_datetime(row["latest_mq_date"]).year) if pd.notna(row.get("latest_mq_date")) else None,
                management_quality_score=row.get("management_quality_score"),
                carbon_performance_alignment_2035=str(row.get("carbon_performance_alignment_2035", "N/A")),
                emissions_trend=row.get("emissions_trend", "Unknown"),
            ))
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving companies: {str(e)}"
        )

    return CompanyListResponse(
        total=total_companies,
        page=page,
        per_page=per_page,
        companies=companies,
    )

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id} - Retrieve Company Details
# ------------------------------------------------------------------------------
@router.get("/company/{company_id}", response_model=CompanyDetail)
@limiter.limit("100/minute")
async def get_company_details(request: Request, company_id: str,
                        filter: CompanyFilters = Depends(CompanyFilters)):
    """
    Retrieve the latest MQ & CP scores for a specific company.
    """
    db_manager = DatabaseManagerFactory.get_manager("tpi_api")
    normalized_input = normalize_company_id(company_id)
    
    # Build filter conditions
    where_clause, params = build_company_filter_conditions(filter)
    params["company_name"] = company_id
    
    try:
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_company_details.sql",
            params,
            where_clause
        )
        
        if result.empty:
            raise HTTPException(
                status_code=404, detail=f"Company '{company_id}' not found."
            )
        
        row = result.iloc[0]
        print(row['company_name'])
        
        return CompanyDetail(
            company_id=normalized_input,
            name=normalized_input,
            sector=row.get("sector", "N/A"),
            geography=row.get("geography", "N/A"),
            latest_assessment_year=int(pd.to_datetime(row["assessment_date"]).year) if pd.notna(row.get("assessment_date")) else None,
            management_quality_score=row.get("level"),
            carbon_performance_alignment_2035=str(row.get("carbon_performance_alignment_2035", "N/A")),
            emissions_trend=row.get("performance_change", "Unknown"),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving company details: {str(e)}"
        )

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/history - Retrieve Company History
# ------------------------------------------------------------------------------
@router.get("/company/{company_id}/history", response_model=CompanyHistoryResponse)
@limiter.limit("100/minute")
async def get_company_history(request: Request, company_id: str, filter: CompanyFilters = Depends(CompanyFilters)):
    """
    Retrieve a company's historical MQ & CP scores.
    """
    db_manager = DatabaseManagerFactory.get_manager("tpi_api")
    normalized_input = normalize_company_id(company_id)
    
    # Build filter conditions
    where_clause, params = build_company_filter_conditions(filter)
    params["company_name"] = company_id
    
    try:
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_company_history.sql",
            params,
            where_clause
        )
        
        if result.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"No history found for company '{company_id}'."
            )
        
        history = []
        for _, row in result.iterrows():
            history.append(CompanyDetail(
                company_id=normalized_input,
                name=row["company_name"],
                sector=row.get("sector", "N/A"),
                geography=row.get("geography", "N/A"),
                latest_assessment_year=int(pd.to_datetime(row["assessment_date"]).year) if pd.notna(row.get("assessment_date")) else None,
                management_quality_score=row.get("level"),
                carbon_performance_alignment_2035=str(row.get("carbon_performance_alignment_2035", "N/A")),
                emissions_trend=row.get("performance_change", "Unknown"),
            ))
        
        return CompanyHistoryResponse(
            company_id=normalized_input,
            history=history,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving company history: {str(e)}"
        )

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/performance-comparison - Compare Performance
# ------------------------------------------------------------------------------
@router.get(
    "/company/{company_id}/performance-comparison",
    response_model=Union[
        PerformanceComparisonResponse,
        PerformanceComparisonInsufficientDataResponse,
    ],
)
@limiter.limit("100/minute")
async def compare_company_performance(request: Request, company_id: str, filter: CompanyFilters = Depends(CompanyFilters)):
    """
    Compare a company's latest performance against the previous year.
    """
    db_manager = DatabaseManagerFactory.get_manager("tpi_api")
    normalized_input = normalize_company_id(company_id)
    
    # Build filter conditions
    where_clause, params = build_company_filter_conditions(filter)
    params["company_name"] = company_id
    
    # Get the two most recent assessments using SQL template
    try:
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_company_performance_comparison.sql",
            params,
            where_clause
        )
        
        if result.empty:
            raise HTTPException(
                status_code=404, detail=f"Company '{company_id}' not found."
            )
        
        if len(result) < 2:
            # Get available years for insufficient data response using SQL template
            years_result = db_manager.execute_sql_template(
                SQL_DIR / "get_company_assessment_years.sql",
                params,
                where_clause
            )
            available_years = [int(row["year"]) for _, row in years_result.iterrows()]
            
            return PerformanceComparisonInsufficientDataResponse(
                company_id=normalized_input,
                message=f"Only one record exists for '{company_id}', so performance comparison is not possible.",
                available_assessment_years=available_years,
            )
        
        latest = result.iloc[0]
        previous = result.iloc[1]
        
        return PerformanceComparisonResponse(
            company_id=normalized_input,
            current_year=int(latest["assessment_year"]),
            previous_year=int(previous["assessment_year"]),
            latest_mq_score=float(latest["level"]) if pd.notna(latest.get("level")) else None,
            previous_mq_score=float(previous["level"]) if pd.notna(previous.get("level")) else None,
            latest_cp_alignment=str(latest.get("carbon_performance_alignment_2035", "N/A")),
            previous_cp_alignment=str(previous.get("carbon_performance_alignment_2035", "N/A")),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing company performance: {str(e)}"
        )
        


