"""

This module provides FastAPI endpoints for retrieving Management Quality (MQ) assessments.
It loads MQ datasets from CSV files, processes the data (including adding a methodology cycle identifier),
and exposes endpoints for fetching the latest assessments, assessments by methodology cycle, and trends by sector.

"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import re
from fastapi import APIRouter, HTTPException, Query, Path, Depends, Request
import pandas as pd
from pathlib import Path as FilePath
from datetime import datetime
from typing import List, Optional
from middleware.rate_limiter import limiter
from schemas import (
    MQAssessmentDetail,
    MQIndicatorsResponse,
    PaginatedMQResponse,
)
from data_utils import MQHandler
from filters import CompanyFilters, MQFilter
from utils import get_latest_data_dir, get_latest_assessment_file

# ------------------------------------------------------------------------------
# Constants and Data Loading
# ------------------------------------------------------------------------------
BASE_DIR = FilePath(__file__).resolve().parent.parent
BASE_DATA_DIR = BASE_DIR / "data"
DATA_DIR = get_latest_data_dir(BASE_DATA_DIR)

STAR_MAPPING = {
    "0STAR": 0.0,
    "1STAR": 1.0,
    "2STAR": 2.0,
    "3STAR": 3.0,
    "4STAR": 4.0,
    "5STAR": 5.0,
}

mq_files = sorted(DATA_DIR.glob("MQ_Assessments_Methodology_*.csv"))
if not mq_files:
    raise FileNotFoundError(f"No MQ datasets found in {DATA_DIR}")

mq_df_list = [pd.read_csv(f) for f in mq_files]

for idx, df in enumerate(mq_df_list, start=1):
    df["methodology_cycle"] = idx

mq_df = pd.concat(mq_df_list, ignore_index=True)
mq_df.columns = mq_df.columns.str.strip().str.lower()

# ------------------------------------------------------------------------------
# Router Initialization
# ------------------------------------------------------------------------------
mq_router = APIRouter(tags=["MQ Endpoints"])

# ------------------------------------------------------------------------------
# Endpoint: GET /latest - Latest MQ Assessments with Pagination
# ------------------------------------------------------------------------------
@mq_router.get("/latest", response_model=PaginatedMQResponse)
@limiter.limit("100/minute")
async def get_latest_mq_assessments(
    request: Request, 
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Number of results per page (max 100)"
    ),
    isin: str = Query(None, description="ISIN identifier"),
    company_filter: CompanyFilters = Depends(CompanyFilters),
    mq_filter: MQFilter = Depends(MQFilter)
):  
    """
    Fetches the latest Management Quality (MQ) assessment for all companies with pagination.

    This function:
    1. Sorts the full MQ dataset by the 'assessment date'.
    2. Groups the data by 'company name' and selects the latest record for each company.
    3. Applies pagination based on the provided page and page_size parameters.
    4. Maps STAR rating strings to numeric scores using a pre-defined dictionary.
    """
    mq_handler = MQHandler()

    if mq_handler.get_df().empty:
        raise HTTPException(status_code=503, detail="MQ dataset is not available.")
    
    try:
        mq_handler.apply_company_filter(company_filter)
        mq_handler.apply_mq_filter(mq_filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )

    # Handle ISIN filtering if provided
    if isin:
        mask = mq_df["isins"].str.lower().str.split(";").apply(lambda x: isin.lower() in [i.strip().lower() for i in x if i])
        latest_records = mq_df[mask]
        total_records = len(latest_records)
    else:
        latest_records = mq_handler.get_latest_assessments(page, page_size)
        total_records = len(latest_records)

    results = [
        MQAssessmentDetail(
            company_id=row["company name"],
            name=row["company name"],
            sector=row.get("sector", "N/A"),
            geography=row.get("geography", "N/A"),
            latest_assessment_year=pd.to_datetime(
                row["assessment date"], format="%d/%m/%Y"
            ).year,
            latest_publication_year=pd.to_datetime(
                row["publication date"], format="%d/%m/%Y"
            ).year,
            management_quality_score=STAR_MAPPING.get(
                row.get("level", "N/A"), None
            ),
        )
        for _, row in latest_records.iterrows()
    ]

    return PaginatedMQResponse(
        total_records=total_records,
        page=page,
        page_size=page_size,
        results=results,
    )


# ------------------------------------------------------------------------------
# Endpoint: GET /methodology/{methodology_id} - MQ Assessments by Cycle
# ------------------------------------------------------------------------------
@mq_router.get(
    "/methodology/{methodology_id}", response_model=PaginatedMQResponse
)
@limiter.limit("100/minute")
async def get_mq_by_methodology(
    request: Request, 
    methodology_id: int = Path(
        ..., ge=1, le=len(mq_files), description="Methodology cycle ID"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        10, ge=1, le=100, description="Records per page (max 100)"),
    company_filter: CompanyFilters = Depends(),
    mq_filter: MQFilter = Depends()
):
    """
    Returns MQ assessments based on a specific research methodology cycle with pagination.
    """
    mq_handler = MQHandler()

    if methodology_id > mq_handler.get_mq_files_length():
        raise HTTPException(status_code=404, detail="Invalid methodology cycle.")

    try:
        mq_handler.apply_company_filter(company_filter)
        mq_handler.apply_mq_filter(mq_filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    methodology_data = mq_handler.get_methodology_data(methodology_id)
    paginated_data = mq_handler.paginate(methodology_data, page, page_size)
    total_records = len(methodology_data)

    results = []
    for _, row in paginated_data.iterrows():
        try:
            assessment_year = pd.to_datetime(row["assessment date"], format="%d/%m/%Y").year
            publication_year = pd.to_datetime(row["publication date"], format="%d/%m/%Y").year
        except Exception:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid date format for company: {row.get('company name')}"
            )

        results.append(MQAssessmentDetail(
            company_id=row["company name"],
            name=row["company name"],
            sector=row.get("sector", "N/A"),
            geography=row.get("geography", "N/A"),
            latest_assessment_year=assessment_year,
            latest_publication_year=publication_year,
            management_quality_score=STAR_MAPPING.get(
                row.get("level", "N/A"), None
            ),
        ))

    return PaginatedMQResponse(
        total_records=total_records,
        page=page,
        page_size=page_size,
        results=results,
    )


# ------------------------------------------------------------------------------
# Endpoint: GET /sector-trends - MQ Trends by Sector
# ------------------------------------------------------------------------------
@mq_router.get("/sector-trends", response_model=List[dict])
@limiter.limit("100/minute")
async def get_mq_sector_trends(
    request: Request,
    company_filter: CompanyFilters = Depends(CompanyFilters),
    mq_filter: MQFilter = Depends(MQFilter)
):
    """
    Analyze MQ trends by sector across different methodology cycles.
    """
    mq_handler = MQHandler()
    
    try:
        mq_handler.apply_company_filter(company_filter)
        mq_handler.apply_mq_filter(mq_filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    
    trends_data = mq_handler.get_sector_trends()
    
    return trends_data


# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_identifier}/indicators - Company MQ Indicators
# ------------------------------------------------------------------------------
@mq_router.get("/company/{company_identifier}/indicators", response_model=MQIndicatorsResponse)
@limiter.limit("100/minute")
async def get_company_mq_indicators(
    request: Request,
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    company_filter: CompanyFilters = Depends(CompanyFilters),
    mq_filter: MQFilter = Depends(MQFilter)
):
    """
    Retrieve detailed MQ indicators for a specific company.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    mq_handler = MQHandler()
    
    try:
        mq_handler.apply_company_filter(company_filter)
        mq_handler.apply_mq_filter(mq_filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    
    # Try ISIN matching first
    mask = mq_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    company_data = mq_df[mask]
    
    if company_data.empty:
        # Fallback to company name/id
        normalized_input = company_identifier.strip().lower()
        company_data = mq_df[mq_df["company name"].str.strip().str.lower() == normalized_input]
    
    if company_data.empty:
        raise HTTPException(404, f"Company '{company_identifier}' not found.")
    
    # Get the latest record
    latest_record = company_data.sort_values("assessment date").iloc[-1]
    
    # Extract indicator columns (assuming they follow a pattern)
    indicators = {}
    for col in latest_record.index:
        if "indicator" in col.lower() or "question" in col.lower():
            indicators[col] = latest_record[col]
    
    return MQIndicatorsResponse(
        company_id=company_identifier,
        company_name=latest_record["company name"],
        assessment_date=latest_record["assessment date"],
        indicators=indicators
    )
