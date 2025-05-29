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
from data_utils import CPHandler
from fastapi import APIRouter, HTTPException, Query, Path, Request, Depends
from fastapi.responses import Response, JSONResponse, StreamingResponse
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
from filters import CompanyFilters
from utils import (
    get_latest_data_dir,
    get_latest_assessment_file,
    get_latest_cp_file,
    get_company_carbon_intensity,
    CarbonPerformanceVisualizer
)

# -------------------------------------------------------------------------
# Data Loading
# -------------------------------------------------------------------------
CP_DATA_DIR = os.getenv("CP_DATA_DIR", "data/")

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
# Endpoint: GET /company/{company_identifier} - Company CP History
# ------------------------------------------------------------------------------
@cp_router.get("/company/{company_identifier}", response_model=List[CPAssessmentDetail])
@limiter.limit("100/minute")
async def get_company_cp_history(
    request: Request, 
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """
    Retrieve CP assessment history for a company.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    cp_handler = CPHandler(prefix=CP_DATA_DIR)
    try:
        cp_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    
    # Try ISIN matching first
    mask = cp_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    company_history = cp_df[mask]
    
    if company_history.empty:
        # Fallback to company name/id using handler
        try:
            company_history = cp_handler.get_company_history(company_identifier)
        except:
            # Final fallback to direct name matching
            normalized_input = company_identifier.strip().lower()
            company_history = cp_df[cp_df["company name"].str.strip().str.lower() == normalized_input]

    # Error handling: Raise a 404 if the company isn't found.
    if company_history.empty:
        raise HTTPException(404, f"Company '{company_identifier}' not found.")
    
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
# Endpoint: GET /company/{company_identifier}/alignment - Alignment Status
# ------------------------------------------------------------------------------
@cp_router.get("/company/{company_identifier}/alignment", response_model=Dict[str, str])
@limiter.limit("100/minute")
async def get_company_cp_alignment(
    request: Request,
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """
    Retrieve the latest CP alignment status for a company.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    cp_handler = CPHandler(prefix=CP_DATA_DIR)
    try:
        cp_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    
    # Try ISIN matching first
    mask = cp_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    company_data = cp_df[mask]
    
    if company_data.empty:
        # Fallback to company name/id
        normalized_input = company_identifier.strip().lower()
        company_data = cp_df[cp_df["company name"].str.strip().str.lower() == normalized_input]
    
    if company_data.empty:
        raise HTTPException(404, f"Company '{company_identifier}' not found.")
    
    # Get the latest record
    latest_record = company_data.sort_values("assessment date").iloc[-1]
    
    alignment_data = {}
    for col in latest_record.index:
        if "carbon performance" in col and col not in ["carbon performance 2025", "carbon performance 2027", "carbon performance 2035", "carbon performance 2050"]:
            alignment_data[col] = str(latest_record[col])
    
    return alignment_data


# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_identifier}/comparison - Compare CP Performance
# ------------------------------------------------------------------------------
@cp_router.get("/company/{company_identifier}/comparison", response_model=Union[CPComparisonResponse, PerformanceComparisonInsufficientDataResponse])
@limiter.limit("100/minute")
async def compare_company_cp_performance(
    request: Request,
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """
    Compare a company's latest CP performance against the previous assessment.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    cp_handler = CPHandler(prefix=CP_DATA_DIR)
    try:
        cp_handler.apply_company_filter(filter)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error filtering company data: {str(e)}"
        )
    
    # Try ISIN matching first
    mask = cp_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    company_history = cp_df[mask]
    
    if company_history.empty:
        # Fallback to company name/id
        normalized_input = company_identifier.strip().lower()
        company_history = cp_df[cp_df["company name"].str.strip().str.lower() == normalized_input]
    
    if company_history.empty:
        raise HTTPException(404, f"Company '{company_identifier}' not found.")
    
    # Sort by assessment date
    company_history = company_history.sort_values("assessment date")
    
    if len(company_history) < 2:
        return PerformanceComparisonInsufficientDataResponse(
            company_id=company_identifier,
            message="Insufficient data for CP performance comparison. At least 2 assessment records are required.",
        )
    
    # Get latest and previous records
    latest = company_history.iloc[-1]
    previous = company_history.iloc[-2]
    
    return CPComparisonResponse(
        company_id=company_identifier,
        latest_assessment=CPAssessmentDetail(
            company_id=latest["company name"],
            name=latest["company name"],
            sector=latest.get("sector", "N/A"),
            geography=latest.get("geography", "N/A"),
            latest_assessment_year=pd.to_datetime(latest["assessment date"],dayfirst=True).year,
            carbon_performance_2025=latest.get("carbon performance 2025", "N/A"),
            carbon_performance_2027=latest.get("carbon performance 2027", "N/A"),
            carbon_performance_2035=latest.get("carbon performance 2035", "N/A"),
            carbon_performance_2050=latest.get("carbon performance 2050", "N/A"),
        ),
        previous_assessment=CPAssessmentDetail(
            company_id=previous["company name"],
            name=previous["company name"],
            sector=previous.get("sector", "N/A"),
            geography=previous.get("geography", "N/A"),
            latest_assessment_year=pd.to_datetime(previous["assessment date"],dayfirst=True).year,
            carbon_performance_2025=previous.get("carbon performance 2025", "N/A"),
            carbon_performance_2027=previous.get("carbon performance 2027", "N/A"),
            carbon_performance_2035=previous.get("carbon performance 2035", "N/A"),
            carbon_performance_2050=previous.get("carbon performance 2050", "N/A"),
        ),
    )


# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_identifier}/carbon-intensity - Carbon Intensity Data
# ------------------------------------------------------------------------------
@cp_router.get("/company/{company_identifier}/carbon-intensity")
@limiter.limit("100/minute")
async def get_company_carbon_intensity_data(
    request: Request,
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """
    Retrieve carbon intensity data for a company including historical values, sector means, and benchmarks.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    try:
        # Try ISIN matching first
        mask = cp_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
        company_data = cp_df[mask]
        
        if company_data.empty:
            # Fallback to company name/id
            normalized_input = company_identifier.strip().lower()
            company_data = cp_df[cp_df["company name"].str.strip().str.lower() == normalized_input]
        
        if company_data.empty:
            raise HTTPException(404, f"Company '{company_identifier}' not found.")
        
        # Get the latest record for sector information
        latest_record = company_data.sort_values("assessment date").iloc[-1]
        sector = latest_record.get("sector", "")
        
        # Get carbon intensity data using the utility function
        carbon_intensity_data = get_company_carbon_intensity(
            company_identifier, 
            sector, 
            cp_df, 
            sector_bench_df
        )
        
        return carbon_intensity_data
        
    except Exception as e:
        raise HTTPException(500, f"Error retrieving carbon intensity data: {str(e)}")


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