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
from fastapi import APIRouter, HTTPException, Query, Path
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
router = APIRouter(prefix="/company", tags=["Company Endpoints"])


# --------------------------------------------------------------------------
# Endpoint: GET /companies - List All Companies with Pagination
# --------------------------------------------------------------------------
@router.get("/companies", response_model=CompanyListResponse)
def get_all_companies(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Results per page"),
    region: str = Query(None, description="Filter by region/geography (case-insensitive)"),
    sector: str = Query(None, description="Filter by sector (case-insensitive)")
):
    """
    Retrieve a paginated list of all companies and their latest assessments.
    Optionally filter by region (geography) and/or sector.
    """
    # Error handling: Ensure that the company dataset is loaded and not empty.
    if company_df is None or company_df.empty:
        raise HTTPException(
            status_code=503, detail="Company dataset not loaded or empty"
        )

    filtered_df = company_df
    if region:
        filtered_df = filtered_df[filtered_df.get('geography', '').str.strip().str.lower() == region.strip().lower()]
    if sector:
        filtered_df = filtered_df[filtered_df.get('sector', '').str.strip().str.lower() == sector.strip().lower()]

    total_companies = len(filtered_df)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Apply pagination and replace any missing values with "N/A".
    paginated_data = filtered_df.iloc[start_idx:end_idx].fillna("N/A")

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
# Endpoint: GET /company/{company_identifier} - Retrieve Company Details
# ------------------------------------------------------------------------------
@router.get("/company/{company_identifier}", response_model=CompanyDetail)
def get_company_details(company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)")):
    """
    Retrieve company details for a given identifier.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    mask = company_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    company = company_df[mask]
    if company.empty:
        normalized_input = normalize_company_id(company_identifier)
        mask = company_df["company name"].apply(normalize_company_id) == normalized_input
        company = company_df[mask]
    if company.empty:
        raise HTTPException(404, f"Company '{company_identifier}' not found.")
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
def get_company_history(
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    region: str = Query(None, description="Filter by region/geography (case-insensitive)"),
    sector: str = Query(None, description="Filter by sector (case-insensitive)")
):
    """
    Retrieve company history for a given identifier.
    Optionally filter by region (geography) and/or sector.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    expected_columns = {col.strip().lower(): col for col in company_df.columns}
    if "mq assessment date" not in expected_columns:
        raise HTTPException(
            status_code=500,
            detail="Column 'MQ Assessment Date' not found in dataset. Check CSV structure.",
        )
    mask = company_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    history = company_df[mask]
    normalized_input = company_identifier
    if history.empty:
        normalized_input = normalize_company_id(company_identifier)
        mask = company_df["company name"].apply(normalize_company_id) == normalized_input
        history = company_df[mask]
    if region:
        history = history[history.get('geography', '').str.strip().str.lower() == region.strip().lower()]
    if sector:
        history = history[history.get('sector', '').str.strip().str.lower() == sector.strip().lower()]
    if history.empty:
        raise HTTPException(404, f"Company '{company_identifier}' not found.")
    return CompanyHistoryResponse(
        company_id=normalized_input,
        history=[
            CompanyDetail(
                company_id=normalized_input,
                name=row.get(expected_columns.get("company name"), "N/A"),
                sector=row.get(expected_columns.get("sector"), "N/A"),
                geography=row.get(expected_columns.get("geography"), "N/A"),
                latest_assessment_year=(
                    int(
                        datetime.strptime(
                            row.get(expected_columns.get("mq assessment date"), "01/01/1900"), "%d/%m/%Y"
                        ).year
                    )
                    if pd.notna(row.get(expected_columns.get("mq assessment date")))
                    else None
                ),
                management_quality_score=row.get(expected_columns.get("level"), "N/A"),
                carbon_performance_alignment_2035=str(row.get(expected_columns.get("carbon performance alignment 2035"), "N/A")),
                emissions_trend=row.get(expected_columns.get("performance compared to previous year"), "Unknown"),
            )
            for _, row in history.iterrows()
        ],
    )


# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_identifier}/performance-comparison - Compare Performance
# ------------------------------------------------------------------------------
@router.get("/company/{company_identifier}/performance-comparison", response_model=Union[PerformanceComparisonResponse, PerformanceComparisonInsufficientDataResponse])
def compare_company_performance(
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    region: str = Query(None, description="Filter by region/geography (case-insensitive)"),
    sector: str = Query(None, description="Filter by sector (case-insensitive)")
):
    """
    Compare company performance for a given identifier.
    Optionally filter by region (geography) and/or sector.
    The company_identifier can be a company name/id or an ISIN (case-insensitive).
    """
    expected_columns = {col.strip().lower(): col for col in company_df.columns}
    if "mq assessment date" not in expected_columns:
        raise HTTPException(
            status_code=500,
            detail="Column 'MQ Assessment Date' not found in dataset. Check CSV structure.",
        )
    mask = company_df["isins"].str.lower().str.split(";").apply(lambda x: company_identifier.lower() in [i.strip().lower() for i in x if i])
    history = company_df[mask]
    normalized_input = company_identifier
    if history.empty:
        normalized_input = normalize_company_id(company_identifier)
        mask = company_df["company name"].apply(normalize_company_id) == normalized_input
        history = company_df[mask]
    if region:
        history = history[history.get('geography', '').str.strip().str.lower() == region.strip().lower()]
    if sector:
        history = history[history.get('sector', '').str.strip().str.lower() == sector.strip().lower()]
    if history.empty:
        raise HTTPException(404, f"Company '{company_identifier}' not found.")
    if len(history) < 2:
        available_years = []
        for date_str in history[expected_columns["mq assessment date"]].dropna():
            dt = datetime.strptime(date_str, "%d/%m/%Y") if date_str else None
            if dt:
                available_years.append(dt.year)
        return PerformanceComparisonInsufficientDataResponse(
            company_id=normalized_input,
            message=f"Only one record exists for '{company_identifier}', so performance comparison is not possible.",
            available_assessment_years=available_years,
        )
    history = history.copy()
    history["assessment_year"] = history[expected_columns["mq assessment date"]].apply(
        lambda x: (int(datetime.strptime(x, "%d/%m/%Y").year) if pd.notna(x) else None)
    )
    history = history.sort_values(by="assessment_year", ascending=False)
    latest = history.iloc[0]
    previous = history.iloc[1]
    return PerformanceComparisonResponse(
        company_id=normalized_input,
        current_year=latest["assessment_year"],
        previous_year=previous["assessment_year"],
        latest_mq_score=str(latest.get(expected_columns.get("level"), "N/A")),
        previous_mq_score=str(previous.get(expected_columns.get("level"), "N/A")),
        latest_cp_alignment=str(latest.get(expected_columns.get("carbon performance alignment 2035"), "N/A")),
        previous_cp_alignment=str(previous.get(expected_columns.get("carbon performance alignment 2035"), "N/A")),
    )


@router.get("/company/{company_identifier}/cp-assessment-details")
def get_company_cp_assessment_details(
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)")
) -> dict:
    """
    Return underlying CP assessment data for the company. For companies in the 'Electricity Utilities' sector, include alignment from both the main CP assessment file and the regional CP assessment file, and include benchmarks from the sector benchmark file.
    """
    # Load CP assessment files
    CP_FILE = "data/TPI sector data - All sectors - 08032025/CP_Assessments_08032025.csv"
    CP_REGIONAL_FILE = "data/TPI sector data - All sectors - 08032025/CP_Assessments_Regional_08032025.csv"
    BENCHMARK_FILE = "data/TPI sector data - All sectors - 08032025/Sector_Benchmarks_08032025.csv"
    cp_df = pd.read_csv(CP_FILE)
    cp_regional_df = pd.read_csv(CP_REGIONAL_FILE)
    bench_df = pd.read_csv(BENCHMARK_FILE)
    # Normalize columns
    cp_df.columns = cp_df.columns.str.strip().str.lower()
    cp_regional_df.columns = cp_regional_df.columns.str.strip().str.lower()
    bench_df.columns = bench_df.columns.str.strip().str.lower()
    # Find the company in the CP file
    ident = company_identifier.strip().lower()
    match = cp_df[cp_df['isins'].astype(str).str.lower().str.split(';').apply(lambda x: ident in [i.strip().lower() for i in x if i])]
    if match.empty:
        match = cp_df[cp_df['company name'].astype(str).str.strip().str.lower() == ident]
    if match.empty:
        return {"error": f"Company '{company_identifier}' not found in CP assessment data."}
    company_row = match.iloc[0]
    sector = company_row.get('sector', None)
    geography = company_row.get('geography', None)
    # Main CP alignment
    cp_alignment = {k: company_row[k] for k in company_row.index if k.startswith('carbon performance alignment')}
    # Regional CP alignment (if Electric Utilities)
    regional_alignment = None
    if sector and sector.strip().lower() == 'electricity utilities':
        reg_match = cp_regional_df[(cp_regional_df['company name'].astype(str).str.strip().str.lower() == company_row['company name'].strip().lower()) & (cp_regional_df['geography'].astype(str).str.strip().str.lower() == geography.strip().lower())]
        if not reg_match.empty:
            reg_row = reg_match.iloc[0]
            regional_alignment = {k: reg_row[k] for k in reg_row.index if k.startswith('carbon performance regional alignment')}
    # Benchmarks (for sector and region if available)
    benchmarks = []
    if sector:
        sector_bench = bench_df[bench_df['sector name'].str.strip().str.lower() == sector.strip().lower()]
        if not sector_bench.empty:
            for _, row in sector_bench.iterrows():
                scenario = row.get('scenario name', 'Unknown')
                region = row.get('region', 'Unknown')
                release_date = row.get('release date', 'Unknown')
                years = {k: row[k] for k in row.index if k.isdigit() or (k.startswith('20') and k.isnumeric())}
                benchmarks.append({
                    "scenario": scenario,
                    "region": region,
                    "release date": release_date,
                    "years": years
                })
    # Get the most recent assessment date for the matched company
    date_series = match['assessment date'].dropna()
    if not date_series.empty:
        latest_date = pd.to_datetime(date_series, errors='coerce').max()
        assessment_date = latest_date.strftime("%Y-%m-%d") if pd.notnull(latest_date) else None
    else:
        assessment_date = None

    return {
        "company": company_row['company name'],
        "sector": sector,
        "geography": geography,
        "latest_cp_assessment_date": assessment_date,
        "cp_alignment": cp_alignment,
        "regional_alignment": regional_alignment,
        "benchmarks": benchmarks
    }


@router.get("/company/{company_identifier}/cp-comparison-sheet")
def get_cp_comparison_sheet(
    company_identifier: str = Path(..., description="Company identifier (name/id or ISIN, case-insensitive)"),
    format: str = Query('csv', description="File format: 'csv' or 'xlsx'"),
    preview: bool = Query(False, description="If true, return the table as JSON for preview in docs")
):
    """
    Download a sheet comparing company values (from CP_Assessments_Regional) and sector benchmark (from Sector_Benchmarks) for each year.
    The table has columns: Year, Company Value, Sector Benchmark.
    """
    # Load data
    REG_FILE = "data/TPI sector data - All sectors - 08032025/CP_Assessments_Regional_08032025.csv"
    BENCHMARK_FILE = "data/TPI sector data - All sectors - 08032025/Sector_Benchmarks_08032025.csv"
    reg_df = pd.read_csv(REG_FILE)
    bench_df = pd.read_csv(BENCHMARK_FILE)
    reg_df.columns = reg_df.columns.str.strip().str.lower()
    bench_df.columns = bench_df.columns.str.strip().str.lower()
    # Find the company in the regional CP file
    ident = company_identifier.strip().lower()
    match = reg_df[reg_df['isins'].astype(str).str.lower().str.split(';').apply(lambda x: ident in [i.strip().lower() for i in x if i])]
    if match.empty:
        match = reg_df[reg_df['company name'].astype(str).str.strip().str.lower() == ident]
    if match.empty:
        raise HTTPException(404, f"Company '{company_identifier}' not found in regional CP assessment data.")
    company_row = match.iloc[0]
    sector = company_row.get('sector', None)
    # Find the sector benchmark row (first match)
    bench_match = bench_df[bench_df['sector name'].str.strip().str.lower() == str(sector).strip().lower()]
    if bench_match.empty:
        raise HTTPException(404, f"Sector '{sector}' not found in sector benchmark data.")
    bench_row = bench_match.iloc[0]
    # Find year columns (intersection of both files)
    year_cols = [col for col in reg_df.columns if col.isdigit() and col in bench_row.index]
    years = sorted([int(y) for y in year_cols])
    data = {
        'Year': years,
        'Company Value': [company_row[str(y)] if str(y) in company_row else None for y in years],
        'Sector Benchmark': [bench_row[str(y)] if str(y) in bench_row else None for y in years],
    }
    df = pd.DataFrame(data)
    if preview:
        df = df.replace([np.inf, -np.inf], np.nan)
        return df.where(pd.notnull(df), None).to_dict(orient='records')
    if format == 'xlsx':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename=cp_comparison.xlsx'})
    else:
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(output, media_type='text/csv', headers={'Content-Disposition': 'attachment; filename=cp_comparison.csv'})
