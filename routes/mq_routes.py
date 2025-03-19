"""

This module provides FastAPI endpoints for retrieving Management Quality (MQ) assessments.
It loads MQ datasets from CSV files, processes the data (including adding a methodology cycle identifier),
and exposes endpoints for fetching the latest assessments, assessments by methodology cycle, and trends by sector.

"""

# Required Imports 
import re
from fastapi import APIRouter, HTTPException, Query, Path
import pandas as pd
from pathlib import Path as FilePath
from datetime import datetime
from typing import List, Optional
from schemas import (
    MQAssessmentDetail,
    MQIndicatorsResponse,
    PaginatedMQResponse
)
# Create an API Router for MQ endpoints
mq_router = APIRouter(prefix="/mq", tags=["MQ Endpoints"])

# ------------------------------------------------------------------------------
# Data Loading and Normalization
# ------------------------------------------------------------------------------
"""
We automatically select the MQ data folder so that future 
versions with updated data are handled without needing to modify the code.
"""

# Dynamic data directory selection.
def get_latest_data_dir(base_data_dir: FilePath, prefix: str = "TPI sector data - All sectors - ") -> FilePath:
    """
    Finds and returns the latest data directory whose name starts with the given prefix 
    and ends with an 8-digit date in MMDDYYYY format.

    Folder naming pattern:
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

    # If no valid dates found, fallback to alphabetical sorting.
    if not dirs_with_dates:
        matching_dirs.sort()
        return matching_dirs[-1]

    # Sort directories by extracted date and return the most recent.
    dirs_with_dates.sort(key=lambda x: x[1])
    return dirs_with_dates[-1][0]

"""""
Here, both the Base directory and the Data directory defined using uppercase letters to signal constants. 
As these remain constant throughout the script (and the project), we can safely consider them to be 
constant variables.
"""""
# Base directories
BASE_DIR = FilePath(__file__).resolve().parent.parent
BASE_DATA_DIR = BASE_DIR / "data"

# Automatically select the latest data folder so future versions (with updated dates)
# are handled without needing to modify the code.
DATA_DIR = get_latest_data_dir(BASE_DATA_DIR)

# Find and load all MQ CSV files in the latest data directory.
mq_files = sorted(DATA_DIR.glob("MQ_Assessments_Methodology_*.csv"))
if not mq_files:
    raise FileNotFoundError(f"No MQ datasets found in {DATA_DIR}")

# Read each CSV file into a DataFrame and store in a list.
mq_df_list = [pd.read_csv(f) for f in mq_files]

# Add a column to each DataFrame to identify its methodology cycle.
# This is useful for filtering or grouping by the research cycle.
for idx, df in enumerate(mq_df_list, start=1):
    df['methodology_cycle'] = idx

# Concatenate all individual DataFrames into one master DataFrame.
mq_df = pd.concat(mq_df_list, ignore_index=True)

# Standardize column names: remove extra spaces and convert to lowercase.
mq_df.columns = mq_df.columns.str.strip().str.lower()

# Mapping of STAR levels (string) to numeric scores.
STAR_MAPPING = {
    "0STAR": 0.0,
    "1STAR": 1.0,
    "2STAR": 2.0,
    "3STAR": 3.0,
    "4STAR": 4.0,
    "5STAR": 5.0,
}

# ------------------------------------------------------------------------------
# Endpoint: Fetch Latest MQ Assessments (With Pagination)
# ------------------------------------------------------------------------------
@mq_router.get("/latest", response_model=PaginatedMQResponse)
def get_latest_mq_assessments(
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of results per page (max 100)")
):
    """
    Fetches the latest Management Quality (MQ) assessment for all companies with pagination.

    This function:
    1. Sorts the full MQ dataset by the 'assessment date'.
    2. Groups the data by 'company name' and selects the latest record for each company.
    3. Applies pagination based on the provided page and page_size parameters.
    4. Maps STAR rating strings to numeric scores using a pre-defined dictionary.

    Parameters:
        page (int): The page number (starting from 1).
        page_size (int): The number of results per page (max 100).

    Returns:
        PaginatedMQResponse: Contains the total number of records, current page, page size, 
                             and a list of MQAssessmentDetail objects.
    """
    # Sort the DataFrame by 'assessment date' and get the latest record for each company.
    latest_records = mq_df.sort_values('assessment date').groupby('company name').tail(1)
    # Calculate pagination indices
    total_records = len(latest_records)
    start_idx = (page - 1) * page_size # Starting index for the current page
    end_idx = start_idx + page_size # Ending index for the current page
    paginated_records = latest_records.iloc[start_idx:end_idx]
    # Map each record to the response model, converting STAR levels to numeric scores.
    results = [
        MQAssessmentDetail(
            company_id=row['company name'],
            name=row['company name'],
            sector=row.get('sector', 'N/A'),
            geography=row.get('geography', 'N/A'),
            latest_assessment_year=pd.to_datetime(row['assessment date']).year,
            management_quality_score=STAR_MAPPING.get(row.get('level', 'N/A'), None)
        )
        for _, row in paginated_records.iterrows()
    ]

    return PaginatedMQResponse(
        total_records=total_records,
        page=page,
        page_size=page_size,
        results=results
    )

# ------------------------------------------------------------------------------
# Endpoint: Fetch MQ Assessments by Methodology Cycle (With Pagination)
# ------------------------------------------------------------------------------
@mq_router.get("/methodology/{methodology_id}", response_model=PaginatedMQResponse)
def get_mq_by_methodology(
    methodology_id: int = Path(..., ge=1, le=len(mq_files), description="Methodology cycle ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Records per page (max 100)")
):
    """
    Returns MQ assessments based on a specific research methodology cycle with pagination.

    Parameters:
        methodology_id (int): The research cycle identifier (must be between 1 and the number of files).
        page (int): The page number for pagination.
        page_size (int): The number of records per page (max 100).

    Returns:
        PaginatedMQResponse: A paginated list of MQAssessmentDetail objects for the specified methodology cycle.
    """
    # Filter the DataFrame for the specified methodology cycle.
    methodology_data = mq_df[mq_df['methodology_cycle'] == methodology_id]
    # Apply pagination to the filtered data 
    total_records = len(methodology_data)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_data = methodology_data.iloc[start_idx:end_idx]
    # Map the filtered records to the response model.
    results = [
        MQAssessmentDetail(
            company_id=row['company name'],
            name=row['company name'],
            sector=row.get('sector', 'N/A'),
            geography=row.get('geography', 'N/A'),
            latest_assessment_year=pd.to_datetime(row['assessment date']).year,
            management_quality_score=STAR_MAPPING.get(row.get('level', 'N/A'), None)
        )
        for _, row in paginated_data.iterrows()
    ]

    return PaginatedMQResponse(
        total_records=total_records,
        page=page,
        page_size=page_size,
        results=results
    )

# ------------------------------------------------------------------------------
# Endpoint: Fetch MQ Trends by Sector (With STAR mapping & Pagination)
# ------------------------------------------------------------------------------
@mq_router.get("/trends/sector/{sector_id}", response_model=PaginatedMQResponse)
def get_mq_trends_sector(
    sector_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Records per page (max 100)")
):
    """
    Fetches MQ trends for all companies in a given sector with pagination.

    Parameters:
        sector_id (str): The sector identifier.
        page (int): The page number.
        page_size (int): The number of results per page (max 100).

    Returns:
        PaginatedMQResponse: Contains the paginated list of MQAssessmentDetail objects for the sector.
    
    Raises:
        HTTPException: If the specified sector is not found in the data.
    """
    # Normalize the input sector identifier for case-insensitive comparison and filter the DataFrame.
    sector_data = mq_df[mq_df["sector"].str.strip().str.lower() == sector_id.strip().lower()]
    # Error handling: If no records are found for the given sector, raise an HTTP 404 error.
    if sector_data.empty:
        raise HTTPException(status_code=404, detail=f"Sector '{sector_id}' not found.")
    # Sort the filtered data by 'assessment date' in descending order (latest first).
    sector_data = sector_data.sort_values("assessment date", ascending=False)
    # Apply pagination logic.
    total_records = len(sector_data)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_data = sector_data.iloc[start_idx:end_idx]
    # Map the paginated records to the MQAssessmentDetail response model.
    results = [
        MQAssessmentDetail(
            company_id=row['company name'],
            name=row['company name'],
            sector=sector_id,
            geography=row.get('geography', 'N/A'),
            latest_assessment_year=pd.to_datetime(row['assessment date']).year,
            management_quality_score=STAR_MAPPING.get(row.get('level', 'N/A'), None)
        )
        for _, row in paginated_data.iterrows()
    ]
    return PaginatedMQResponse(
        total_records=total_records,
        page=page,
        page_size=page_size,
        results=results
    )