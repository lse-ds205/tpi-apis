"""
This module provides FastAPI endpoints for retrieving Carbon Performance (CP) assessments.
It automatically selects the latest TPI data folder, then searches for CP assessment files,
loads and normalizes the data, and exposes endpoints to retrieve and compare CP scores.
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
import io
import re
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import Response, JSONResponse, StreamingResponse
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
    get_company_carbon_intensity,
    CarbonPerformanceVisualizer
)

# -------------------------------------------------------------------------
# Constants and Data Loading
# -------------------------------------------------------------------------
BASE_DIR = FilePath(__file__).resolve().parent.parent
BASE_DATA_DIR = BASE_DIR / "data"
DATA_DIR = get_latest_data_dir(BASE_DATA_DIR)

# load all CP assessment CSVs
cp_files = get_latest_cp_file("CP_Assessments_*.csv", DATA_DIR)
cp_df_list = []
for idx, file_path in enumerate(cp_files, start=1):
    df = pd.read_csv(file_path)
    df["assessment_cycle"] = idx
    cp_df_list.append(df)

if not cp_df_list:
    raise RuntimeError("No Carbon Performance assessment files found in data directory")

cp_df = pd.concat(cp_df_list, ignore_index=True)
cp_df.columns = cp_df.columns.str.strip().str.lower()

bench_filename = "Sector_Benchmarks_08032025.csv"
bench_path = DATA_DIR / bench_filename
if not bench_path.exists():
    raise FileNotFoundError(f"Benchmark file not found at {bench_path}")
sector_bench_df = pd.read_csv(
    bench_path,
    dayfirst=True,
    engine="python",
    on_bad_lines="skip"  # skip malformed rows
)
sector_bench_df.columns = sector_bench_df.columns.str.strip().str.lower()


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
# Endpoint: GET /company/{company_identifier} - Company CP History
# ------------------------------------------------------------------------------
@cp_router.get("/company/{company_identifier}", response_model=List[CPAssessmentDetail])
def get_company_cp_history(company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)")):
    """
    Retrieve CP assessment history for a company.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    mask = cp_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    company_history = cp_df[mask]
    if company_history.empty:
        # Fallback to company name/id
        normalized_input = company_identifier.strip().lower()
        company_history = cp_df[cp_df["company name"].str.strip().str.lower() == normalized_input]
    if company_history.empty:
        raise HTTPException(404, f"Company '{company_identifier}' not found.")
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
# Endpoint: GET /company/{company_identifier}/alignment - Alignment Status
# ------------------------------------------------------------------------------
@cp_router.get("/company/{company_identifier}/alignment", response_model=Dict[str, str])
def get_company_cp_alignment(company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)")):
    """
    Retrieve CP alignment status for a company.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    mask = cp_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    company_data = cp_df[mask]
    if company_data.empty:
        normalized_input = company_identifier.strip().lower()
        company_data = cp_df[cp_df["company name"].str.strip().str.lower() == normalized_input]
    if company_data.empty:
        raise HTTPException(404, f"Company '{company_identifier}' not found.")
    latest_record = company_data.sort_values("assessment date").iloc[-1]
    return {
        "2025": latest_record.get("carbon performance 2025", "N/A"),
        "2027": latest_record.get("carbon performance 2027", "N/A"),
        "2035": latest_record.get("carbon performance 2035", "N/A"),
        "2050": latest_record.get("carbon performance 2050", "N/A"),
    }


# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_identifier}/comparison - Compare CP over Time
# ------------------------------------------------------------------------------
@cp_router.get(
    "/company/{company_identifier}/comparison",
    response_model=Union[
        CPComparisonResponse, PerformanceComparisonInsufficientDataResponse
    ],
)
def compare_company_cp(company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)")):
    """
    Compare CP performance for a company over time.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    mask = cp_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    company_data = cp_df[mask]
    if company_data.empty:
        normalized_input = company_identifier.strip().lower()
        company_data = cp_df[cp_df["company name"].str.strip().str.lower() == normalized_input]
    if len(company_data) < 2:
        available_years = [
            pd.to_datetime(date, errors="coerce").year
            for date in company_data["assessment date"]
        ]
        available_years = [year for year in available_years if year is not None]
        return PerformanceComparisonInsufficientDataResponse(
            company_id=company_identifier,
            message="Insufficient data for comparison",
            available_assessment_years=available_years,
        )
    sorted_data = company_data.sort_values("assessment date", ascending=False)
    latest, previous = sorted_data.iloc[0], sorted_data.iloc[1]
    return CPComparisonResponse(
        company_id=company_identifier,
        current_year=pd.to_datetime(latest["assessment date"]).year,
        previous_year=pd.to_datetime(previous["assessment date"]).year,
        latest_cp_2025=latest.get("carbon performance 2025", "N/A"),
        previous_cp_2025=previous.get("carbon performance 2025", "N/A"),
        latest_cp_2035=latest.get("carbon performance 2035", "N/A"),
        previous_cp_2035=previous.get("carbon performance 2035", "N/A"),
    )

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_identifier}/carbon-performance-graph" - Graph endpoint
# ------------------------------------------------------------------------------
@cp_router.get(
    "/company/{company_identifier}/carbon-performance-graph",
    responses={200: {"content": {"image/png": {}}, "description": "PNG graph"}}
)
def get_company_carbon_performance_graph(
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    include_sector_benchmarks: bool = Query(True, description="Include benchmarks"),
    as_image: bool = Query(True, description="Return PNG if true"),
    image_format: str = Query("png", description="png|jpeg"),
    width: int = Query(1000, ge=400, le=2000),
    height: int = Query(600, ge=300, le=1200),
    title: Optional[str] = Query(None, description="Custom title")
):
    """
    Generate a carbon performance graph for a company.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    mask = cp_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    sub = cp_df[mask]
    if sub.empty:
        normalized_input = company_identifier.strip().lower()
        sub = cp_df[cp_df["company name"].str.lower() == normalized_input]
        if sub.empty:
            raise HTTPException(404, f"Company '{company_identifier}' not found")
        company_id_for_graph = company_identifier
    else:
        company_id_for_graph = sub.iloc[-1]["company name"]
    data = get_company_carbon_intensity(company_id_for_graph, include_sector_benchmarks, cp_df, sector_bench_df)
    row = sub.sort_values("assessment_cycle").iloc[-1]
    target_years, target_values = [], []
    for col in row.index:
        m = re.search(r"carbon performance.*?(\d{4})$", col)
        if m:
            yr = int(m.group(1))
            val = pd.to_numeric(row[col], errors="coerce")
            if pd.notnull(val):
                target_years.append(yr)
                target_values.append(float(val))
    if target_years:
        yrs, vals = zip(*sorted(zip(target_years, target_values)))
        data["target_years"] = list(yrs)
        data["target_values"] = list(vals)
    chart_title = title or f"Carbon Performance for {company_id_for_graph}"
    fig_or_resp = CarbonPerformanceVisualizer.generate_carbon_intensity_graph(
        data, chart_title, width, height, as_image, image_format
    )
    if as_image:
        return fig_or_resp
    return JSONResponse(content=fig_or_resp)