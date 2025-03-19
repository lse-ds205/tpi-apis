"""
This module provides FastAPI endpoints for retrieving Carbon Performance (CP) assessments.
It automatically selects the latest TPI data folder, then searches for CP assessment files,
loads and normalizes the data, and exposes endpoints to retrieve and compare CP scores.
"""

# Required Imports 
import re
from fastapi import APIRouter, HTTPException, Query, Path
import pandas as pd
from pathlib import Path as FilePath
from datetime import datetime
from typing import List, Optional, Dict, Union
from schemas import (
    CPAssessmentDetail, 
    CPComparisonResponse, 
    PerformanceComparisonInsufficientDataResponse)

# Create an API Router for CP endpoints
cp_router = APIRouter(prefix="/cp", tags=["CP Endpoints"])

# ------------------------------------------------------------------------------
# Data Loading and Normalization
# ------------------------------------------------------------------------------
"""
We automatically select the latest data folder so that future versions 
(with updated dates in the folder name) are handled without needing code changes.
"""

def get_latest_data_dir(base_data_dir: FilePath, prefix: str = "TPI sector data - All sectors - ") -> FilePath:
    """
    Finds and returns the latest data directory whose name starts with the given prefix 
    and ends with an 8-digit date in MMDDYYYY format.

    Example folder naming pattern:
        TPI sector data - All sectors - MMDDYYYY

    Parameters:
        base_data_dir (Path): The base directory containing possible data folders.
        prefix (str): The prefix that data folder names should start with.

    Returns:
        Path: The Path object for the latest data folder.

    Raises:
        FileNotFoundError: If no matching data directory is found.
    """
    # List subdirectories that start with the prefix.
    matching_dirs = [d for d in base_data_dir.iterdir() if d.is_dir() and d.name.startswith(prefix)]
    if not matching_dirs:
        raise FileNotFoundError("No data directories found with the specified prefix.")

    # Regex to extract an 8-digit date (MMDDYYYY) from the folder name.
    date_pattern = re.compile(rf'^{re.escape(prefix)}(\d{{8}})$')
    dirs_with_dates = []

    for d in matching_dirs:
        match = date_pattern.match(d.name)
        if match:
            date_str = match.group(1)
            try:
                d_date = datetime.strptime(date_str, "%m%d%Y")
                dirs_with_dates.append((d, d_date))
            except ValueError:
                continue

    # Error handling: If no valid dates were extracted, fallback to alphabetical sorting.
    if not dirs_with_dates:
        matching_dirs.sort()
        return matching_dirs[-1]

    # Sort directories by extracted date and return the most recent.
    dirs_with_dates.sort(key=lambda x: x[1])
    return dirs_with_dates[-1][0]

def get_latest_cp_file(pattern: str, data_dir: FilePath) -> List[FilePath]:
    """
    Finds and returns a sorted list of CP assessment files matching the pattern 
    (e.g., CP_Assessments_*.csv) in the latest data directory. 
    You can modify this if you need to parse dates in the filenames as well.

    Parameters:
        pattern (str): Glob pattern to match the files (e.g., "CP_Assessments_*.csv").
        data_dir (Path): The directory containing the CSV files.

    Returns:
        List[Path]: A sorted list of file paths matching the pattern.

    Raises:
        FileNotFoundError: If no files matching the pattern are found.
    """
    files = sorted(data_dir.glob(pattern))
    # Error handling: Raise an error if no CP datasets match the pattern.
    if not files:
        raise FileNotFoundError(f"No CP datasets found in {data_dir}")
    return files

#Use the function to select the data directory 
"""""
Here, both the Base directory and the Data directory defined using uppercase letters to signal constants. 
As these remain constant throughout the script (and the project), we can safely consider them to be 
constant variables.
"""""
# Define the base directory and the base data directory.
BASE_DIR = FilePath(__file__).resolve().parent.parent
BASE_DATA_DIR = BASE_DIR / "data"

# Automatically select the latest data folder
DATA_DIR = get_latest_data_dir(BASE_DATA_DIR)

# Get all CP assessment files (you might adapt the pattern to your naming convention)
cp_files = get_latest_cp_file("CP_Assessments_*.csv", DATA_DIR)

# Read each CSV file into a DataFrame and store in a list
cp_df_list = [pd.read_csv(f) for f in cp_files]

# Optionally add a column to identify methodology/assessment cycle (if needed)
for idx, df in enumerate(cp_df_list, start=1):
    df['assessment_cycle'] = idx

# Concatenate all individual DataFrames into one master DataFrame
cp_df = pd.concat(cp_df_list, ignore_index=True)

# Standardize column names: remove extra spaces and convert to lowercase
cp_df.columns = cp_df.columns.str.strip().str.lower()

# ------------------------------------------------------------------------------
# Endpoint: GET /latest - Fetch the Latest CP Assessments (with Pagination)
# ------------------------------------------------------------------------------
@cp_router.get("/latest", response_model=List[CPAssessmentDetail])
def get_latest_cp_assessments(
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    page_size: int = Query(10, ge=1, le=100, description="Results per page (max 100)")
):
    """"
    Fetches the latest CP assessment levels for all companies with pagination.

    Steps:
    1. Sort the DataFrame by 'assessment date'.
    2. Group by 'company name' and select the latest record for each.
    3. Apply pagination based on page/page_size.
    4. Return a list of CPAssessmentDetail objects.

    Parameters:
        page (int): The page number (starting at 1).
        page_size (int): The number of results per page (max 100).

    Returns:
        List[CPAssessmentDetail]: The latest CP assessment records, paginated.
    """
    latest_records = cp_df.sort_values('assessment date').groupby('company name').tail(1)
    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_records = latest_records.iloc[start_idx:end_idx]

    results = [
        CPAssessmentDetail(
            company_id=row['company name'],
            name=row['company name'],
            sector=row.get('sector', 'N/A'),
            geography=row.get('geography', 'N/A'),
            latest_assessment_year=pd.to_datetime(row['assessment date']).year,
            carbon_performance_2025=row.get('carbon performance 2025', 'N/A'),
            carbon_performance_2027=row.get('carbon performance 2027', 'N/A'),
            carbon_performance_2035=row.get('carbon performance 2035', 'N/A'),
            carbon_performance_2050=row.get('carbon performance 2050', 'N/A'),
        )
        for _, row in paginated_records.iterrows()
    ]

    return results

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id} - Retrieve Company CP History
# ------------------------------------------------------------------------------
@cp_router.get("/company/{company_id}", response_model=List[CPAssessmentDetail])
def get_company_cp_history(company_id: str):
    """"
    Retrieves all CP assessments for a specific company across different assessment cycles.

    Parameters:
        company_id (str): The normalized company identifier (lowercase, no extra spaces).

    Returns:
        List[CPAssessmentDetail]: All CP assessment records for the given company.

    Raises:
        HTTPException: If no records are found for the specified company.
    """
    # Case-insensitive match on 'company name'
    company_history = cp_df[cp_df["company name"].str.strip().str.lower() == company_id.strip().lower()]
    # Error handling: Raise a 404 if the company isn't found.
    if company_history.empty:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found.")

    return [
        CPAssessmentDetail(
            company_id=row['company name'],
            name=row['company name'],
            sector=row.get('sector', 'N/A'),
            geography=row.get('geography', 'N/A'),
            latest_assessment_year=pd.to_datetime(row['assessment date']).year,
            carbon_performance_2025=row.get('carbon performance 2025', 'N/A'),
            carbon_performance_2027=row.get('carbon performance 2027', 'N/A'),
            carbon_performance_2035=row.get('carbon performance 2035', 'N/A'),
            carbon_performance_2050=row.get('carbon performance 2050', 'N/A'),
        )
        for _, row in company_history.iterrows()
    ]

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/alignment - Check CP Alignment
# ------------------------------------------------------------------------------
@cp_router.get("/company/{company_id}/alignment", response_model=Dict[str, str])
def get_company_cp_alignment(company_id: str):
    """
    Check if a company aligns with 2025, 2027, 2035, or 2050 carbon targets.

    Parameters:
        company_id (str): The normalized company identifier.

    Returns:
        Dict[str, str]: A dictionary mapping each target year to the company's alignment status.

    Raises:
        HTTPException: If the company is not found.
    """
    company_data = cp_df[cp_df["company name"].str.strip().str.lower() == company_id.strip().lower()]
    # Error handling: Raise a 404 if no matching company is found.
    if company_data.empty:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found.")
    # Sort to ensure we get the most recent record
    latest_record = company_data.sort_values("assessment date").iloc[-1]
    return {
        "2025": latest_record.get('carbon performance 2025', 'N/A'),
        "2027": latest_record.get('carbon performance 2027', 'N/A'),
        "2035": latest_record.get('carbon performance 2035', 'N/A'),
        "2050": latest_record.get('carbon performance 2050', 'N/A'),
    }

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/comparison - Compare CP Over the Years
# ------------------------------------------------------------------------------
@cp_router.get("/company/{company_id}/comparison", response_model=Union[CPComparisonResponse, PerformanceComparisonInsufficientDataResponse])
def compare_company_cp(company_id: str):
    """
    Compares a company's CP alignment over the years.

    Parameters:
        company_id (str): The normalized company identifier.

    Returns:
        CPComparisonResponse: If at least two records are available for comparison.
        PerformanceComparisonInsufficientDataResponse: If only one or zero records exist.

    Raises:
        HTTPException: If no records are found at all for the company.
    """
    company_data = cp_df[cp_df["company name"].str.strip().str.lower() == company_id.strip().lower()]
    # Error handling: If fewer than 2 records, return an insufficient data response.
    if len(company_data) < 2:
        available_years = [
            pd.to_datetime(date, errors='coerce').year for date in company_data["assessment date"]
        ]
        available_years = [year for year in available_years if year is not None]  # Remove None values

        return PerformanceComparisonInsufficientDataResponse(
            company_id=company_id,
            message="Insufficient data for comparison",
            available_assessment_years=available_years
        )
    # Sort records in descending order by 'assessment date'
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
