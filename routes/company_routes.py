"""
This module provides FastAPI endpoints for retrieving company data and assessments.
It loads the company assessment dataset from a CSV file, normalizes the data,
and exposes endpoints for listing companies, retrieving company details, history,
and comparing performance between assessment cycles.
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends
import pandas as pd
from pathlib import Path as FilePath
from datetime import datetime
from typing import Union
from schemas import (
    CompanyBase,
    CompanyDetail,
    CompanyListResponse,
    CompanyHistoryResponse,
    PerformanceComparisonResponse,
    PerformanceComparisonInsufficientDataResponse,
)
from utils import normalize_company_id
from data_utils import CompanyDataHandler
from filters import CompanyFilters

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
router = APIRouter(prefix="/company", tags=["Company Endpoints"])

# --------------------------------------------------------------------------
# Endpoint: GET /companies - List All Companies with Pagination
# --------------------------------------------------------------------------
@router.get("/companies", response_model=CompanyListResponse)
def get_all_companies(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Results per page"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """
    Retrieve a paginated list of all companies and their latest assessments.

    Steps:
    1. Validate that the dataset is loaded and not empty
    2. Apply pagination
    3. Normalize each company record, generating a unique ID
    """
    # Error handling: Ensure that the company dataset is loaded and not empty.
    company_handler = CompanyDataHandler()
    try:
        print(filter)
        company_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    company_df = company_handler.get_df()
    if company_df is None or company_df.empty:
        raise HTTPException(
            status_code=503, detail="Company dataset not loaded or empty"
        )
    
    try:
        total_companies = company_handler.get_df_length()
        paginated_data = company_handler.paginate(company_df, page, per_page)
        companies = company_handler.format_data(paginated_data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing company data: {str(e)}"
        )

    return CompanyListResponse(
        total=total_companies,
        page=page,
        per_page=per_page,
        companies=[CompanyBase(**company) for company in companies],
    )


# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id} - Retrieve Company Details
# ------------------------------------------------------------------------------
@router.get("/company/{company_id}", response_model=CompanyDetail)
def get_company_details(company_id: str,
                        filter: CompanyFilters = Depends(CompanyFilters)):
    """
    Retrieve the latest MQ & CP scores for a specific company.

    Raises 404 if the company is not found
    """
    company_handler = CompanyDataHandler()
    try:
        company_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    
    normalized_input = normalize_company_id(company_id)

    company = company_handler.get_latest_details(normalized_input)
    if company.empty:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_id}' not found."
        )

    return CompanyDetail(
        company_id=normalized_input,
        name=company.get("company name", "N/A"),
        sector=company.get("sector", "N/A"),
        geography=company.get("geography", "N/A"),
        latest_assessment_year=company.get(
            "latest assessment year", None
        ),
        management_quality_score=company.get("level", None),
        carbon_performance_alignment_2035=str(
            company.get("carbon performance alignment 2035", "N/A")
        ),
        emissions_trend=company.get(
            "performance compared to previous year", "Unknown"
        ),
    )

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/history - Retrieve Company History
# ------------------------------------------------------------------------------
@router.get(
    "/company/{company_id}/history", response_model=CompanyHistoryResponse
)
def get_company_history(company_id: str, filter: CompanyFilters = Depends(CompanyFilters)):
    """
    Retrieve a company's historical MQ & CP scores.

    - Checks for 'mq assessment date' column.
    - Filters records by company ID.
    - Returns a list of historical assessment details.
    """

    company_handler = CompanyDataHandler()
    try:
        company_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )    
    # Error handling: Check if the essential column "mq assessment date" exists.

    normalized_input = normalize_company_id(company_id)
    history = company_handler.get_company_history(normalized_input)

    # Error handling: If no records are found, raise a 404 error.
    if history.empty:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_id}' not found."
        )
    if "mq assessment date" not in history.columns:
        raise HTTPException(
            status_code=500,
            detail="Column 'MQ Assessment Date' not found in dataset. Check CSV structure.",
        )

    return CompanyHistoryResponse(
        company_id=normalized_input,
        history=[
            CompanyDetail(
                company_id=normalized_input,
                name=row.get("company name", "N/A"),
                sector=row.get("sector", "N/A"),
                geography=row.get("geography", "N/A"),
                # Convert the assessment date to an integer year; use a default if not present.
                latest_assessment_year=(
                    int(
                        datetime.strptime(
                            row.get("mq assessment date", "01/01/1900"),
                            "%d/%m/%Y",
                        ).year
                    )
                    if pd.notna(row.get("mq assessment date"))
                    else None
                ),
                management_quality_score=row.get("level", None),
                carbon_performance_alignment_2035=str(
                    row.get("carbon performance alignment 2035", "N/A")
                ),  # Ensuring string conversion
                emissions_trend=row.get("performance compared to previous year", "Unknown"),
            )
            for _, row in history.iterrows()
        ],
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
def compare_company_performance(company_id: str, filter: CompanyFilters = Depends(CompanyFilters)):
    """
    Compare a company's latest performance against the previous year.
    
    Steps:
    1. Get company history using DataHandler
    2. Check if we have enough data for comparison (at least 2 records)
    3. Compare latest and previous records
    """
    company_handler = CompanyDataHandler()
    try:
        company_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    normalized_input = normalize_company_id(company_id)
    
    comparison = company_handler.compare_performance(normalized_input)
    
    if comparison is None:
        available_years = company_handler.get_available_years(normalized_input)
        return PerformanceComparisonInsufficientDataResponse(
            company_id=normalized_input,
            message=f"Only one record exists for '{company_id}', so performance comparison is not possible.",
            available_assessment_years=available_years,
        )
    
    if comparison.empty:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_id}' not found."
        )

    if "mq assessment date" not in comparison.columns:
        raise HTTPException(
            status_code=500,
            detail="Column 'MQ Assessment Date' not found in dataset. Check CSV structure.",
        )
        
    latest, previous = comparison
    
    return PerformanceComparisonResponse(
        company_id=normalized_input,
        current_year=latest["assessment_year"],
        previous_year=previous["assessment_year"],
        latest_mq_score=float(latest.get("level")) if pd.notna(latest.get("level")) else None,
        previous_mq_score=float(previous.get("level")) if pd.notna(previous.get("level")) else None,
        latest_cp_alignment=str(latest.get("carbon performance alignment 2035", "N/A")),
        previous_cp_alignment=str(previous.get("carbon performance alignment 2035", "N/A")),
    )
        


