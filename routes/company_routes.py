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
from fastapi import APIRouter, HTTPException, Query
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
from utils import (
    get_latest_data_dir,
    get_latest_assessment_file,
    normalize_company_id,
)

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
router = APIRouter(prefix="/company", tags=["Company Endpoints"])


# --------------------------------------------------------------------------
# Endpoint: GET /companies - List All Companies with Pagination
# --------------------------------------------------------------------------
@router.get("/companies", response_model=CompanyListResponse)
def get_all_companies(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Results per page"),
):
    """
    Retrieve a paginated list of all companies and their latest assessments.

    Steps:
    1. Validate that the dataset is loaded and not empty
    2. Apply pagination
    3. Normalize each company record, generating a unique ID
    """
    # Error handling: Ensure that the company dataset is loaded and not empty.
    if company_df is None or company_df.empty:
        raise HTTPException(
            status_code=503, detail="Company dataset not loaded or empty"
        )

    total_companies = len(company_df)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Apply pagination and replace any missing values with "N/A".
    paginated_data = company_df.iloc[start_idx:end_idx].fillna("N/A")

    # Map each row to a company dictionary with a normalized unique ID.
    companies = [
        {
            "company_id": normalize_company_id(row["company name"]),
            "name": row["company name"],  # Original company name
            "sector": row.get("sector", None),
            "geography": row.get("geography", None),
            "latest_assessment_year": row.get("latest assessment year", None),
        }
        for _, row in paginated_data.iterrows()
    ]
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
def get_company_details(company_id: str):
    """
    Retrieve the latest MQ & CP scores for a specific company.

    Raises 404 if the company is not found
    """
    normalized_input = normalize_company_id(company_id)
    mask = (
        company_df["company name"].apply(normalize_company_id)
        == normalized_input
    )
    company = company_df[mask]

    # Error handling: If the company is not found, raise a 404 error.
    if company.empty:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_id}' not found."
        )

    latest_record = company.iloc[-1].fillna("N/A")

    return CompanyDetail(
        company_id=normalized_input,
        name=latest_record.get("company name", "N/A"),
        sector=latest_record.get("sector", "N/A"),
        geography=latest_record.get("geography", "N/A"),
        latest_assessment_year=latest_record.get(
            "latest assessment year", None
        ),
        management_quality_score=latest_record.get("level", None),
        carbon_performance_alignment_2035=str(
            latest_record.get("carbon performance alignment 2035", "N/A")
        ),
        emissions_trend=latest_record.get(
            "performance compared to previous year", "Unknown"
        ),
    )


# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/history - Retrieve Company History
# ------------------------------------------------------------------------------
@router.get(
    "/company/{company_id}/history", response_model=CompanyHistoryResponse
)
def get_company_history(company_id: str):
    """
    Retrieve a company's historical MQ & CP scores.

    - Checks for 'mq assessment date' column.
    - Filters records by company ID.
    - Returns a list of historical assessment details.
    """
    expected_columns = {col.strip().lower(): col for col in company_df.columns}

    # Error handling: Check if the essential column "mq assessment date" exists.
    if "mq assessment date" not in expected_columns:
        raise HTTPException(
            status_code=500,
            detail="Column 'MQ Assessment Date' not found in dataset. Check CSV structure.",
        )

    normalized_input = normalize_company_id(company_id)
    mask = (
        company_df["company name"].apply(normalize_company_id)
        == normalized_input
    )
    history = company_df[mask]

    # Error handling: If no records are found, raise a 404 error.
    if history.empty:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_id}' not found."
        )

    return CompanyHistoryResponse(
        company_id=normalized_input,
        history=[
            CompanyDetail(
                company_id=normalized_input,
                name=row.get(expected_columns.get("company name"), "N/A"),
                sector=row.get(expected_columns.get("sector"), "N/A"),
                geography=row.get(expected_columns.get("geography"), "N/A"),
                # Convert the assessment date to an integer year; use a default if not present.
                latest_assessment_year=(
                    int(
                        datetime.strptime(
                            row.get(
                                expected_columns.get("mq assessment date"),
                                "01/01/1900",
                            ),
                            "%d/%m/%Y",
                        ).year
                    )
                    if pd.notna(
                        row.get(expected_columns.get("mq assessment date"))
                    )
                    else None
                ),
                management_quality_score=row.get(
                    expected_columns.get("level"), "N/A"
                ),
                carbon_performance_alignment_2035=str(
                    row.get(
                        expected_columns.get(
                            "carbon performance alignment 2035"
                        ),
                        "N/A",
                    )
                ),  # Ensuring string conversion
                emissions_trend=row.get(
                    expected_columns.get(
                        "performance compared to previous year"
                    ),
                    "Unknown",
                ),
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
def compare_company_performance(company_id: str):
    """
    Compare a company's latest performance against the previous year.

    - Requires at least two records to compare.
    - Returns 'insufficient data' if only one record exists.
    """
    expected_columns = {col.strip().lower(): col for col in company_df.columns}

    # Error handling: Check if the essential column "mq assessment date" exists.
    if "mq assessment date" not in expected_columns:
        raise HTTPException(
            status_code=500,
            detail="Column 'MQ Assessment Date' not found in dataset. Check CSV structure.",
        )

    normalized_input = normalize_company_id(company_id)
    mask = (
        company_df["company name"].apply(normalize_company_id)
        == normalized_input
    )
    history = company_df[mask]

    # Error handling: If no records are found for the company, raise a 404 error.
    if history.empty:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_id}' not found."
        )

    if len(history) < 2:
        # Safely parse available dates as DD/MM/YYYY, skipping unparseable ones
        available_years = []
        for date_str in history[
            expected_columns["mq assessment date"]
        ].dropna():
            dt = datetime.strptime(date_str, "%d/%m/%Y") if date_str else None
            if dt:
                available_years.append(dt.year)

        return PerformanceComparisonInsufficientDataResponse(
            company_id=normalized_input,
            message=f"Only one record exists for '{company_id}', so performance comparison is not possible.",
            available_assessment_years=available_years,
        )

    # Convert 'MQ Assessment Date' to integer year (DD/MM/YYYY)
    history = history.copy()
    history["assessment_year"] = history[
        expected_columns["mq assessment date"]
    ].apply(
        lambda x: (
            int(datetime.strptime(x, "%d/%m/%Y").year) if pd.notna(x) else None
        )
    )
    history = history.sort_values(by="assessment_year", ascending=False)
    latest = history.iloc[0]
    previous = history.iloc[1]

    return PerformanceComparisonResponse(
        company_id=normalized_input,
        current_year=latest["assessment_year"],
        previous_year=previous["assessment_year"],
        latest_mq_score=str(latest.get(expected_columns.get("level"), "N/A")),
        previous_mq_score=str(
            previous.get(expected_columns.get("level"), "N/A")
        ),
        latest_cp_alignment=str(
            latest.get(
                expected_columns.get("carbon performance alignment 2035"),
                "N/A",
            )
        ),
        previous_cp_alignment=str(
            previous.get(
                expected_columns.get("carbon performance alignment 2035"),
                "N/A",
            )
        ),
    )
