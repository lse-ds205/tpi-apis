"""
This module provides FastAPI endpoints for retrieving Carbon Performance (CP) assessments.
It automatically selects the latest TPI data folder, then searches for CP assessment files,
loads and normalizes the data, and exposes endpoints to retrieve and compare CP scores.
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
import re
from fastapi import APIRouter, HTTPException, Query, Path
import pandas as pd
from pathlib import Path as FilePath
from datetime import datetime
from typing import List, Optional, Dict, Union
from schemas import (
    CPAssessmentDetail,
    CPComparisonResponse,
    PerformanceComparisonInsufficientDataResponse,
)
from utils import (
    get_latest_data_dir,
    get_latest_assessment_file,
    get_latest_cp_file,
)

# -------------------------------------------------------------------------
# Constants and Data Loading
# -------------------------------------------------------------------------
BASE_DIR = FilePath(__file__).resolve().parent.parent
BASE_DATA_DIR = BASE_DIR / "data"
DATA_DIR = get_latest_data_dir(BASE_DATA_DIR)

cp_files = get_latest_cp_file("CP_Assessments_*.csv", DATA_DIR)

cp_df_list = [pd.read_csv(f) for f in cp_files]

for idx, df in enumerate(cp_df_list, start=1):
    df["assessment_cycle"] = idx

cp_df = pd.concat(cp_df_list, ignore_index=True)
cp_df.columns = cp_df.columns.str.strip().str.lower()

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
cp_router = APIRouter(prefix="/cp", tags=["CP Endpoints"])


# ------------------------------------------------------------------------------
# Endpoint: GET /latest - Latest CP Assessments with Pagination
# ------------------------------------------------------------------------------
@cp_router.get("/latest", response_model=List[CPAssessmentDetail])
def get_latest_cp_assessments(
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Results per page (max 100)"
    ),
):
    """ "
    Retrieve the latest CP assessment levels for all companies with pagination.

    Steps:
    1. Sort the DataFrame by 'assessment date'.
    2. Group by 'company name' and select the latest record for each.
    3. Apply pagination based on page/page_size.
    4. Return a list of CPAssessmentDetail objects.
    """
    latest_records = (
        cp_df.sort_values("assessment date").groupby("company name").tail(1)
    )

    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_records = latest_records.iloc[start_idx:end_idx]

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
        for _, row in paginated_records.iterrows()
    ]

    return results


# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id} - Company CP History
# ------------------------------------------------------------------------------
@cp_router.get(
    "/company/{company_id}", response_model=List[CPAssessmentDetail]
)
def get_company_cp_history(company_id: str):
    """
    Retrieve all CP assessments for a specific company across different assessment cycles.
    """
    company_history = cp_df[
        cp_df["company name"].str.strip().str.lower()
        == company_id.strip().lower()
    ]

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
            latest_assessment_year=pd.to_datetime(row["assessment date"]).year,
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
def get_company_cp_alignment(company_id: str):
    """
    Retrieves a company's carbon performance alignment status across target years
    """
    company_data = cp_df[
        cp_df["company name"].str.strip().str.lower()
        == company_id.strip().lower()
    ]

    # Error handling: Raise a 404 if no matching company is found.
    if company_data.empty:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_id}' not found."
        )

    latest_record = company_data.sort_values("assessment date").iloc[-1]

    return {
        "2025": latest_record.get("carbon performance 2025", "N/A"),
        "2027": latest_record.get("carbon performance 2027", "N/A"),
        "2035": latest_record.get("carbon performance 2035", "N/A"),
        "2050": latest_record.get("carbon performance 2050", "N/A"),
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
def compare_company_cp(company_id: str):
    """
    Compare the most recent CP assessment to the previous one for a company.
    """
    company_data = cp_df[
        cp_df["company name"].str.strip().str.lower()
        == company_id.strip().lower()
    ]

    # Error handling: If fewer than 2 records, return an insufficient data response.
    if len(company_data) < 2:
        available_years = [
            pd.to_datetime(date, errors="coerce").year
            for date in company_data["assessment date"]
        ]
        available_years = [
            year for year in available_years if year is not None
        ]

        return PerformanceComparisonInsufficientDataResponse(
            company_id=company_id,
            message="Insufficient data for comparison",
            available_assessment_years=available_years,
        )

    sorted_data = company_data.sort_values("assessment date", ascending=False)
    latest, previous = sorted_data.iloc[0], sorted_data.iloc[1]

    return CPComparisonResponse(
        company_id=company_id,
        current_year=pd.to_datetime(latest["assessment date"]).year,
        previous_year=pd.to_datetime(previous["assessment date"]).year,
        latest_cp_2025=latest.get("carbon performance 2025", "N/A"),
        previous_cp_2025=previous.get("carbon performance 2025", "N/A"),
        latest_cp_2035=latest.get("carbon performance 2035", "N/A"),
        previous_cp_2035=previous.get("carbon performance 2035", "N/A"),
    )
