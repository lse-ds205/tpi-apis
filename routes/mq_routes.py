"""

This module provides FastAPI endpoints for retrieving Management Quality (MQ) assessments.
It loads MQ datasets from CSV files, processes the data (including adding a methodology cycle identifier),
and exposes endpoints for fetching the latest assessments, assessments by methodology cycle, and trends by sector.

"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import re
from fastapi import APIRouter, HTTPException, Query, Path
import pandas as pd
from pathlib import Path as FilePath
from datetime import datetime
from typing import List, Optional
from schemas import (
    MQAssessmentDetail,
    MQIndicatorsResponse,
    PaginatedMQResponse,
)
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
mq_router = APIRouter(prefix="/mq", tags=["MQ Endpoints"])


# ------------------------------------------------------------------------------
# Endpoint: GET /latest - Latest MQ Assessments with Pagination
# ------------------------------------------------------------------------------
@mq_router.get("/latest", response_model=PaginatedMQResponse)
def get_latest_mq_assessments(
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Number of results per page (max 100)"
    ),
):
    """
    Fetches the latest Management Quality (MQ) assessment for all companies with pagination.

    This function:
    1. Sorts the full MQ dataset by the 'assessment date'.
    2. Groups the data by 'company name' and selects the latest record for each company.
    3. Applies pagination based on the provided page and page_size parameters.
    4. Maps STAR rating strings to numeric scores using a pre-defined dictionary.
    """
    latest_records = (
        mq_df.sort_values("assessment date").groupby("company name").tail(1)
    )

    # Calculate pagination indices
    total_records = len(latest_records)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_records = latest_records.iloc[start_idx:end_idx]

    results = [
        MQAssessmentDetail(
            company_id=row["company name"],
            name=row["company name"],
            sector=row.get("sector", "N/A"),
            geography=row.get("geography", "N/A"),
            latest_assessment_year=pd.to_datetime(
                row["assessment date"], format="%d/%m/%Y"
            ).year,
            management_quality_score=STAR_MAPPING.get(
                row.get("level", "N/A"), None
            ),
        )
        for _, row in paginated_records.iterrows()
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
def get_mq_by_methodology(
    methodology_id: int = Path(
        ..., ge=1, le=len(mq_files), description="Methodology cycle ID"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        10, ge=1, le=100, description="Records per page (max 100)"
    ),
):
    """
    Returns MQ assessments based on a specific research methodology cycle with pagination.
    """
    methodology_data = mq_df[mq_df["methodology_cycle"] == methodology_id]

    # Apply pagination to the filtered data
    total_records = len(methodology_data)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_data = methodology_data.iloc[start_idx:end_idx]

    results = [
        MQAssessmentDetail(
            company_id=row["company name"],
            name=row["company name"],
            sector=row.get("sector", "N/A"),
            geography=row.get("geography", "N/A"),
            latest_assessment_year=pd.to_datetime(
                row["assessment date"], format="%d/%m/%Y"
            ).year,
            management_quality_score=STAR_MAPPING.get(
                row.get("level", "N/A"), None
            ),
        )
        for _, row in paginated_data.iterrows()
    ]

    return PaginatedMQResponse(
        total_records=total_records,
        page=page,
        page_size=page_size,
        results=results,
    )


# ------------------------------------------------------------------------------
# Endpoint: GET /trends/sector/{sector_id} - MQ Trends by Sector
# ------------------------------------------------------------------------------
@mq_router.get(
    "/trends/sector/{sector_id}", response_model=PaginatedMQResponse
)
def get_mq_trends_sector(
    sector_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        10, ge=1, le=100, description="Records per page (max 100)"
    ),
):
    """
    Fetches MQ trends for all companies in a given sector with pagination.
    """
    sector_data = mq_df[
        mq_df["sector"].str.strip().str.lower() == sector_id.strip().lower()
    ]

    # Error handling: If no records are found for the given sector, raise an HTTP 404 error.
    if sector_data.empty:
        raise HTTPException(
            status_code=404, detail=f"Sector '{sector_id}' not found."
        )

    sector_data = sector_data.sort_values("assessment date", ascending=False)

    # Apply pagination logic.
    total_records = len(sector_data)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_data = sector_data.iloc[start_idx:end_idx]

    results = [
        MQAssessmentDetail(
            company_id=row["company name"],
            name=row["company name"],
            sector=sector_id,
            geography=row.get("geography", "N/A"),
            latest_assessment_year=pd.to_datetime(
                row["assessment date"], format="%d/%m/%Y"
            ).year,
            management_quality_score=STAR_MAPPING.get(
                row.get("level", "N/A"), None
            ),
        )
        for _, row in paginated_data.iterrows()
    ]

    return PaginatedMQResponse(
        total_records=total_records,
        page=page,
        page_size=page_size,
        results=results,
    )
