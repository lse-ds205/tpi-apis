"""
This module provides FastAPI endpoints for retrieving Carbon Performance (CP) assessments.
It automatically selects the latest TPI data folder, then searches for CP assessment files,
loads and normalizes the data, and exposes endpoints to retrieve and compare CP scores.
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
from utils.data_utils import CPHandler
from fastapi import APIRouter, HTTPException, Query, Path, Request, Depends
import pandas as pd
import os
from pathlib import Path as FilePath
from datetime import datetime
from typing import List, Optional, Dict, Union
from middleware.rate_limiter import limiter
from schemas import (
    CPAssessmentDetail,
    CPComparisonResponse,
    PerformanceComparisonInsufficientDataResponse,
)
from utils.filters import CompanyFilters

# -------------------------------------------------------------------------
# Data Loading
# -------------------------------------------------------------------------
CP_DATA_DIR = os.getenv("CP_DATA_DIR", "data/")

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
cp_router = APIRouter(tags=["CP Endpoints"])

# ------------------------------------------------------------------------------
# Endpoint: GET /latest - Latest CP Assessments with Pagination
# ------------------------------------------------------------------------------
@cp_router.get("/latest", response_model=List[CPAssessmentDetail])
@limiter.limit("2/minute")
async def get_latest_cp_assessments(
    request: Request, 
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Results per page (max 100)"
    ),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """ "
    Retrieve the latest CP assessment levels for all companies with pagination.

    Steps:
    1. Sort the DataFrame by 'assessment date'.
    2. Group by 'company name' and select the latest record for each.
    3. Apply pagination based on page/page_size.
    4. Return a list of CPAssessmentDetail objects.
    """
    cp_handler = CPHandler(prefix=CP_DATA_DIR)
    try:
        cp_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    latest_records = cp_handler.get_latest_assessments(page, page_size)

    results = [
        CPAssessmentDetail(
            company_id=row["company name"],
            name=row["company name"],
            sector=row.get("sector", "N/A"),
            geography=row.get("geography", "N/A"),
            latest_assessment_year=pd.to_datetime(row["assessment date"]).year,
            carbon_performance_2025=row.get("carbon performance 2025", "N/A"),
            carbon_performance_2027=row.get("carbon performance 2027", "N/A"),
            carbon_performance_2035=row.get("carbon performance 2035", "N/A"),
            carbon_performance_2050=row.get("carbon performance 2050", "N/A"),
        )
        for _, row in latest_records.iterrows()
    ]

    return results


# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id} - Company CP History
# ------------------------------------------------------------------------------
@cp_router.get(
    "/company/{company_id}", response_model=List[CPAssessmentDetail]
)
@limiter.limit("100/minute")
async def get_company_cp_history(request: Request, company_id: str, filter: CompanyFilters = Depends(CompanyFilters)):
    """
    Retrieve all CP assessments for a specific company across different assessment cycles.
    """
    cp_handler = CPHandler(prefix=CP_DATA_DIR)
    try:
        cp_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    company_history = cp_handler.get_company_history(company_id)

    # Error handling: Raise a 404 if the company isn't found.
    if company_history.empty:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_id}' not found."
        )

    return [
        CPAssessmentDetail(
            company_id=row["company name"],
            name=row["company name"],
            sector=row.get("sector", "N/A"),
            geography=row.get("geography", "N/A"),
            latest_assessment_year=pd.to_datetime(row["assessment date"],dayfirst=True).year,
            carbon_performance_2025=row.get("carbon performance 2025", "N/A"),
            carbon_performance_2027=row.get("carbon performance 2027", "N/A"),
            carbon_performance_2035=row.get("carbon performance 2035", "N/A"),
            carbon_performance_2050=row.get("carbon performance 2050", "N/A"),
        )
        for _, row in company_history.iterrows()
    ]


# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/alignment - Alignment Status
# ------------------------------------------------------------------------------
@cp_router.get(
    "/company/{company_id}/alignment", response_model=Dict[str, str]
)
@limiter.limit("100/minute")
async def get_company_cp_alignment(request: Request, company_id: str, filter: CompanyFilters = Depends(CompanyFilters)):
    """
    Retrieves a company's carbon performance alignment status across target years
    """
    cp_handler = CPHandler(prefix=CP_DATA_DIR)
    try:
        cp_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    try:
        company_data_latest = cp_handler.get_company_alignment(company_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_id}' not found."
        )
    
    return {
        "2025": company_data_latest.get("carbon performance 2025", "N/A"),
        "2027": company_data_latest.get("carbon performance 2027", "N/A"),
        "2035": company_data_latest.get("carbon performance 2035", "N/A"),
        "2050": company_data_latest.get("carbon performance 2050", "N/A"),
    }


# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/comparison - Compare CP over Time
# ------------------------------------------------------------------------------
@cp_router.get(
    "/company/{company_id}/comparison",
    response_model=Union[
        CPComparisonResponse, PerformanceComparisonInsufficientDataResponse
    ],
)
@limiter.limit("100/minute")
async def compare_company_cp(request: Request, company_id: str, filter: CompanyFilters = Depends(CompanyFilters)):
    """
    Compare the most recent CP assessment to the previous one for a company.
    """
    cp_handler = CPHandler(prefix=CP_DATA_DIR)
    try:
        cp_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    company_data = cp_handler.compare_company_cp(company_id)

    if company_data[0] is None:
        return PerformanceComparisonInsufficientDataResponse(
            company_id=company_id,
            message="Insufficient data for comparison",
            available_assessment_years=company_data[1]
        )       

    else:
        latest, previous = company_data
        return CPComparisonResponse(
            company_id=company_id,
            current_year=pd.to_datetime(latest["assessment date"], dayfirst=True).year,
            previous_year=pd.to_datetime(previous["assessment date"], dayfirst=True).year,
            latest_cp_2025=latest.get("carbon performance 2025", "N/A"),
            previous_cp_2025=previous.get("carbon performance 2025", "N/A"),
            latest_cp_2035=latest.get("carbon performance 2035", "N/A"),
            previous_cp_2035=previous.get("carbon performance 2035", "N/A"),
        )