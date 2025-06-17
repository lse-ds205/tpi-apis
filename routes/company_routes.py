"""
This module provides FastAPI endpoints for retrieving company data and assessments.
It loads the company assessment dataset from a CSV file, normalizes the data,
and exposes endpoints for listing companies, retrieving company details, history,
and comparing performance between assessment cycles.
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
import re
from fastapi import APIRouter, HTTPException, Query, Request, Depends, Path
import pandas as pd
from pathlib import Path as FilePath
from datetime import datetime
from typing import Union
from middleware.rate_limiter import limiter
from schemas import (
    CompanyBase,
    CompanyDetail,
    CompanyListResponse,
    CompanyHistoryResponse,
    PerformanceComparisonResponse,
    PerformanceComparisonInsufficientDataResponse,
)
from utils import normalize_company_id, get_latest_data_dir, get_latest_assessment_file
from data_utils import CompanyDataHandler
from filters import CompanyFilters
import io
from fastapi.responses import StreamingResponse
import numpy as np

# -------------------------------------------------------------------------
# Constants and Data Loading
# -------------------------------------------------------------------------
BASE_DIR = FilePath(__file__).resolve().parent.parent
BASE_DATA_DIR = BASE_DIR / "data"
DATA_DIR = get_latest_data_dir(BASE_DATA_DIR)

# Define the path for the company assessments CSV file.
latest_file = get_latest_assessment_file(
    "Company_Latest_Assessments*.csv", DATA_DIR
)

# Load the company dataset into a DataFrame.
company_df = pd.read_csv(latest_file)

# Standardize column names: strip extra spaces and convert to lowercase.
company_df.columns = company_df.columns.str.strip().str.lower()
expected_column = "company name"
company_df[expected_column] = (
    company_df[expected_column].str.strip().str.lower()
)

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
router = APIRouter(tags=["Company Endpoints"])

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
    Optionally filter by region (geography) and/or sector.
    """
    # Error handling: Ensure that the company dataset is loaded and not empty.
    company_handler = CompanyDataHandler()
    try:
        company_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    company_df = company_handler.get_df()
    if company_df is None or company_df.empty:
        raise HTTPException(
            status_code=503, detail="Company dataset is not loaded. Please ensure the data file exists in the /data folder."
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
# Endpoint: GET /company/{company_identifier} - Retrieve Company Details
# ------------------------------------------------------------------------------

@router.get("/company/{company_identifier}", response_model=CompanyDetail)
@limiter.limit("100/minute")
async def get_company_details(
    request: Request, 
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """
    Retrieve the latest MQ & CP scores for a specific company.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
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
    
    company_df = company_handler.get_df()
    
    # Try ISIN matching first
    mask = company_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    company = company_df[mask]
    
    # If no ISIN match, try normalized company name
    if company.empty:
        normalized_input = normalize_company_id(company_identifier)
        try:
            company = company_handler.get_latest_details(normalized_input)
        except (ValueError, IndexError) as e:
            # Catch the out-of-bounds error or manual ValueError
            raise HTTPException(
                status_code=404, detail=f"Company '{company_identifier}' not found."
            )
        
        return CompanyDetail(
            company_id=normalized_input,
            name=company.get("company name", "N/A"),
            sector=company.get("sector", "N/A"),
            geography=company.get("geography", "N/A"),
            latest_assessment_year=company.get("latest assessment year", None),
            management_quality_score=company.get("level", None),
            carbon_performance_alignment_2035=str(
                company.get("carbon performance alignment 2035", "N/A")
            ),
            emissions_trend=company.get(
                "performance compared to previous year", "Unknown"
            ),
        )
    else:
        # ISIN match found, use the latest record
        latest_record = company.iloc[-1].fillna("N/A")
        return CompanyDetail(
            company_id=company_identifier,
            name=latest_record.get("company name", "N/A"),
            sector=latest_record.get("sector", "N/A"),
            geography=latest_record.get("geography", "N/A"),
            latest_assessment_year=latest_record.get("latest assessment year", None),
            management_quality_score=latest_record.get("level", None),
            carbon_performance_alignment_2035=str(latest_record.get("carbon performance alignment 2035", "N/A")),
            emissions_trend=latest_record.get("performance compared to previous year", "Unknown"),
        )

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_identifier}/history - Retrieve Company History
# ------------------------------------------------------------------------------
@router.get("/company/{company_identifier}/history", response_model=CompanyHistoryResponse)
@limiter.limit("100/minute")
async def get_company_history(
    request: Request,
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """
    Retrieve company history for a given identifier.
    Optionally filter by region (geography) and/or sector.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    company_handler = CompanyDataHandler()

    try:
        company_handler.apply_company_filter(filter)
        filtered_df = company_handler.get_df()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )

    expected_columns = {col.strip().lower(): col for col in filtered_df.columns}
    if "mq assessment date" not in expected_columns:
        raise HTTPException(
            status_code=503,
            detail="Column 'MQ Assessment Date' not found in dataset. Check CSV structure.",
        )

    # Try ISIN matching first
    mask = filtered_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    history = filtered_df[mask]
    normalized_input = company_identifier
    
    # If no ISIN match, try normalized company name
    if history.empty:
        normalized_input = normalize_company_id(company_identifier)
        history = filtered_df[
            filtered_df["company name"].apply(normalize_company_id) == normalized_input
        ]

    if history.empty:
        raise HTTPException(
            status_code=404, 
            detail=f"No history found for company '{company_identifier}'."
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
# Endpoint: GET /company/{company_identifier}/performance-comparison - Compare Performance
# ------------------------------------------------------------------------------
@router.get(
    "/company/{company_identifier}/performance-comparison",
    response_model=Union[
        PerformanceComparisonResponse,
        PerformanceComparisonInsufficientDataResponse,
    ],
)
@limiter.limit("100/minute")
async def compare_company_performance(
    request: Request, 
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """
    Compare a company's latest performance against the previous year.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    
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
    
    filtered_df = company_handler.get_df()
    expected_columns = {col.strip().lower(): col for col in filtered_df.columns}
    if "mq assessment date" not in expected_columns:
        raise HTTPException(
            status_code=503,
            detail="Column 'MQ Assessment Date' not found in dataset. Check CSV structure.",
        )

    # Try ISIN matching first
    mask = filtered_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    history = filtered_df[mask]
    normalized_input = company_identifier
    
    # If no ISIN match, try normalized company name
    if history.empty:
        normalized_input = normalize_company_id(company_identifier)
        history = filtered_df[
            filtered_df["company name"].apply(normalize_company_id) == normalized_input
        ]

    if history.empty:
        raise HTTPException(
            status_code=404, 
            detail=f"Company '{company_identifier}' not found."
        )

    # Sort by assessment date to get chronological order
    history = history.sort_values("mq assessment date")
    
    if len(history) < 2:
        return PerformanceComparisonInsufficientDataResponse(
            company_id=normalized_input,
            message="Insufficient data for performance comparison. At least 2 assessment records are required.",
        )

    # Get the latest and previous records
    latest = history.iloc[-1]
    previous = history.iloc[-2]

    return PerformanceComparisonResponse(
        company_id=normalized_input,
        latest_assessment=CompanyDetail(
            company_id=normalized_input,
            name=latest.get("company name", "N/A"),
            sector=latest.get("sector", "N/A"),
            geography=latest.get("geography", "N/A"),
            latest_assessment_year=(
                int(
                    datetime.strptime(
                        latest.get("mq assessment date", "01/01/1900"),
                        "%d/%m/%Y",
                    ).year
                )
                if pd.notna(latest.get("mq assessment date"))
                else None
            ),
            management_quality_score=latest.get("level", None),
            carbon_performance_alignment_2035=str(
                latest.get("carbon performance alignment 2035", "N/A")
            ),
            emissions_trend=latest.get("performance compared to previous year", "Unknown"),
        ),
        previous_assessment=CompanyDetail(
            company_id=normalized_input,
            name=previous.get("company name", "N/A"),
            sector=previous.get("sector", "N/A"),
            geography=previous.get("geography", "N/A"),
            latest_assessment_year=(
                int(
                    datetime.strptime(
                        previous.get("mq assessment date", "01/01/1900"),
                        "%d/%m/%Y",
                    ).year
                )
                if pd.notna(previous.get("mq assessment date"))
                else None
            ),
            management_quality_score=previous.get("level", None),
            carbon_performance_alignment_2035=str(
                previous.get("carbon performance alignment 2035", "N/A")
            ),
            emissions_trend=previous.get("performance compared to previous year", "Unknown"),
        ),
    )

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_identifier}/export - Export Company Data
# ------------------------------------------------------------------------------
@router.get("/company/{company_identifier}/export")
@limiter.limit("100/minute")
async def export_company_data(
    request: Request,
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    format: str = Query("csv", description="Export format (csv or excel)"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """
    Export company data in CSV or Excel format.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    company_handler = CompanyDataHandler()
    try:
        company_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    
    filtered_df = company_handler.get_df()
    
    # Try ISIN matching first
    mask = filtered_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    company_data = filtered_df[mask]
    
    # If no ISIN match, try normalized company name
    if company_data.empty:
        normalized_input = normalize_company_id(company_identifier)
        company_data = filtered_df[
            filtered_df["company name"].apply(normalize_company_id) == normalized_input
        ]

    if company_data.empty:
        raise HTTPException(
            status_code=404, 
            detail=f"Company '{company_identifier}' not found."
        )

    # Create export data
    if format.lower() == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            company_data.to_excel(writer, sheet_name='Company Data', index=False)
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={normalize_company_id(company_identifier)}_data.xlsx"}
        )
    else:
        # Default to CSV
        output = io.StringIO()
        company_data.to_csv(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={normalize_company_id(company_identifier)}_data.csv"}
        )
