"""
This module provides FastAPI endpoints for retrieving company data and assessments.
It loads the company assessment dataset from a CSV file, normalizes the data,
and exposes endpoints for listing companies, retrieving company details, history, 
and comparing performance between assessment cycles.
"""

# Required Imports
import re 
from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from pathlib import Path as FilePath
from schemas import (
    CompanyBase, 
    CompanyDetail, 
    CompanyListResponse, 
    CompanyHistoryResponse, 
    PerformanceComparisonResponse,
    PerformanceComparisonInsufficientDataResponse  
)
from datetime import datetime
from typing import Union

# Create an API Router for Company endpoints
router = APIRouter(prefix="/company", tags=["Company Endpoints"])

# ------------------------------------------------------------------------------
# Data Loading and Normalization
# ------------------------------------------------------------------------------
"""
We automatically select the latest company assessments file so that future 
versions with updated data are handled without needing to modify the code.
"""

# Dynamic data directory selection.
def get_latest_data_dir(base_data_dir: FilePath, prefix: str = "TPI sector data - All sectors - ") -> FilePath:
    """
    Finds and returns the latest data directory whose name starts with the given prefix and ends with an 8-digit date.
    
    The folder names are expected to follow the pattern:
    TPI sector data - All sectors - MMDDYYYY
    
    Parameters:
        base_data_dir (Path): The base directory containing the data folders.
        prefix (str): The prefix of the data folder names.
    
    Returns:
        Path: The Path object corresponding to the latest data folder.
    
    Raises:
        FileNotFoundError: If no matching data directory is found.
    """
    # List all subdirectories in the base_data_dir that start with the prefix.
    matching_dirs = [d for d in base_data_dir.iterdir() if d.is_dir() and d.name.startswith(prefix)]
    if not matching_dirs:
        raise FileNotFoundError("No data directories found with the specified prefix.")
    
    # Define a regex to extract an 8-digit date (MMDDYYYY) from the folder name.
    date_pattern = re.compile(rf'^{re.escape(prefix)}(\d{{8}})$')
    
    dirs_with_dates = []
    for d in matching_dirs:
        match = date_pattern.match(d.name)
        if match:
            date_str = match.group(1)
            try:
                # Parse the date assuming MMDDYYYY format.
                d_date = datetime.strptime(date_str, "%m%d%Y")
                dirs_with_dates.append((d, d_date))
            except ValueError:
                continue
    
    # If no valid dates were extracted, fallback to alphabetical order.
    if not dirs_with_dates:
        matching_dirs.sort()
        return matching_dirs[-1]
    
    # Sort directories by the extracted date.
    dirs_with_dates.sort(key=lambda x: x[1])
    
    # Return the directory with the latest date.
    return dirs_with_dates[-1][0]

#Use the function to select the data directory 
"""""
Here, both the Base directory and the Data directory defined using uppercase letters to signal constants. 
As these remain constant throughout the script (and the project), we can safely consider them to be 
constant variables.
"""""
# Define the base directory and the base data directory.
BASE_DIR = FilePath(__file__).resolve().parent.parent
BASE_DATA_DIR = BASE_DIR / "data"

# Automatically select the latest data folder.
DATA_DIR = get_latest_data_dir(BASE_DATA_DIR)

def get_latest_assessment_file(pattern: str, data_dir: FilePath) -> FilePath:
    """
    Finds and returns the latest company assessments file based on the date embedded in the filename.
    
    The filenames are expected to follow the pattern:
    Company_Latest_Assessments*.csv
    with a date in MMDDYYYY format before the .csv extension.
    
    Parameters:
        pattern (str): Glob pattern to match the files.
        data_dir (Path): The directory containing the CSV files.
    
    Returns:
        Path: The Path object corresponding to the latest file.
    
    Raises:
        FileNotFoundError: If no files matching the pattern are found.
    """
    # Get list of files matching the pattern.
    files = list(data_dir.glob(pattern))
    if not files:
        raise FileNotFoundError("No company assessments files found.")
    
    # Define a regex to extract the date (MMDDYYYY) from the filename.
    date_pattern = re.compile(r'_(\d{8})\.csv$')
    
    def extract_date(file_path: FilePath):
        match = date_pattern.search(file_path.name)
        if match:
            date_str = match.group(1)
            try:
                # Parse the date assuming MMDDYYYY format.
                return datetime.strptime(date_str, "%m%d%Y")
            except ValueError:
                return None
        return None
    
    # Create a list of tuples (file, extracted_date) and filter out invalid dates.
    files_with_dates = [(f, extract_date(f)) for f in files]
    files_with_dates = [(f, d) for f, d in files_with_dates if d is not None]
    
    # If no file has a valid date, fallback to alphabetical sorting.
    if not files_with_dates:
        files.sort()
        return files[-1]
    
    # Sort the list by the extracted date.
    files_with_dates.sort(key=lambda x: x[1])
    
    # Return the file with the latest date.
    return files_with_dates[-1][0]

# Define the path for the company assessments CSV file.
latest_file = get_latest_assessment_file("Company_Latest_Assessments*.csv", DATA_DIR)
# Load the company dataset into a DataFrame.
company_df = pd.read_csv(latest_file)
# Standardize column names: strip extra spaces and convert to lowercase.
company_df.columns = company_df.columns.str.strip().str.lower()

# Normalize the "company name" column to ensure consistent casing and no extra spaces.
expected_column = "company name"
company_df[expected_column] = company_df[expected_column].str.strip().str.lower()

# ------------------------------------------------------------------------------
# Endpoint: GET /companies - List All Companies with Pagination
# ------------------------------------------------------------------------------
@router.get("/companies", response_model=CompanyListResponse)
def get_all_companies(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Results per page"),
):
    """
    Retrieve a paginated list of all companies and their latest assessments.

    This function:
    1. Checks that the company dataset is loaded and not empty.
    2. Applies pagination to the DataFrame.
    3. Normalizes and maps each company record to a CompanyBase model,
       generating a unique company ID by replacing spaces with underscores.

    Parameters:
        page (int): The page number (starting from 1).
        per_page (int): The number of results per page (max 100).

    Returns:
        CompanyListResponse: Contains total companies, current page, results per page,
                             and a list of company records.
    """
    # Error handling: Ensure that the company dataset is loaded and not empty.
    if company_df is None or company_df.empty:
        raise HTTPException(status_code=503, detail="Company dataset not loaded or empty")
    
    total_companies = len(company_df)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    # Apply pagination and replace any missing values with "N/A".
    paginated_data = company_df.iloc[start_idx:end_idx].fillna("N/A")

    # Map each row to a company dictionary with a normalized unique ID.
    companies = [
        {
            "company_id": row["company name"].replace(" ", "_").lower(),  # Unique ID generated from the name
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
        companies=[CompanyBase(**company) for company in companies]
    )

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id} - Retrieve Company Details
# ------------------------------------------------------------------------------
@router.get("/company/{company_id}", response_model=CompanyDetail)
def get_company_details(company_id: str):
    """
    Retrieve the latest MQ & CP scores for a specific company.

    Parameters:
        company_id (str): The normalized company identifier.

    Returns:
        CompanyDetail: A detailed record of the company including MQ and CP metrics.

    Raises:
        HTTPException: If the company is not found.
    """
    # Normalize the search by comparing lower-case strings
    company = company_df[company_df["company name"].str.strip().str.lower() == company_id.strip().lower()]
    # Error handling: If the company is not found, raise a 404 error.
    if company.empty:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found.")
    # Select the latest assessment record and replace any NaN values.
    latest_record = company.iloc[-1].fillna("N/A")  

    return CompanyDetail(
        company_id=company_id,
        name=latest_record.get("company name", "N/A"),
        sector=latest_record.get("sector", "N/A"),
        geography=latest_record.get("geography", "N/A"),
        latest_assessment_year=latest_record.get("latest assessment year", None),
        management_quality_score=latest_record.get("level", None),
        carbon_performance_alignment_2035=str(latest_record.get("carbon performance alignment 2035", "N/A")),
        emissions_trend=latest_record.get("performance compared to previous year", "Unknown"),
    )

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/history - Retrieve Company History
# ------------------------------------------------------------------------------
@router.get("/company/{company_id}/history", response_model=CompanyHistoryResponse)
def get_company_history(company_id: str):
    """
    Retrieve a company's historical MQ & CP scores.

    The function:
    1. Ensures consistent column naming.
    2. Verifies that the key "mq assessment date" exists.
    3. Filters records for the specified company in a case-insensitive manner.
    
    Parameters:
        company_id (str): The normalized company identifier.

    Returns:
        CompanyHistoryResponse: Contains the company ID and a list of historical CompanyDetail records.

    Raises:
        HTTPException: If the required "mq assessment date" column is missing or if the company is not found.
    """
    # Create a mapping of normalized column names to original column names.
    expected_columns = {col.strip().lower(): col for col in company_df.columns}
    # Error handling: Check if the essential column "mq assessment date" exists.
    if "mq assessment date" not in expected_columns:
        raise HTTPException(status_code=500, detail="Column 'MQ Assessment Date' not found in dataset. Check CSV structure.")
    # Filter records for the specified company (case-insensitive).
    history = company_df[company_df["company name"].str.strip().str.lower() == company_id.strip().lower()]
    # Error handling: If no records are found, raise a 404 error.
    if history.empty:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found.")

    return CompanyHistoryResponse(
        company_id=company_id,
        history=[
            CompanyDetail(
                company_id=company_id,
                name=row.get(expected_columns.get("company name"), "N/A"),
                sector=row.get(expected_columns.get("sector"), "N/A"),
                geography=row.get(expected_columns.get("geography"), "N/A"),
                # Convert the assessment date to an integer year; use a default if not present.
                latest_assessment_year=int(datetime.strptime(row.get(expected_columns.get("mq assessment date"), "01/01/1900"), "%d/%m/%Y").year)
                if pd.notna(row.get(expected_columns.get("mq assessment date"))) else None,
                management_quality_score=row.get(expected_columns.get("level"), "N/A"),
                carbon_performance_alignment_2035=str(row.get(expected_columns.get("carbon performance alignment 2035"), "N/A")),  # Ensuring string conversion
                emissions_trend=row.get(expected_columns.get("performance compared to previous year"), "Unknown"),
            )
            for _, row in history.iterrows()
        ]
    )

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/performance-comparison - Compare Performance
# ------------------------------------------------------------------------------
@router.get(
    "/company/{company_id}/performance-comparison",
    response_model=Union[PerformanceComparisonResponse, PerformanceComparisonInsufficientDataResponse]
)
def compare_company_performance(company_id: str):
    """
    Compare a company's latest performance against the previous year.

    This endpoint:
    1. Dynamically maps expected column names.
    2. Ensures the "mq assessment date" column is present.
    3. Filters and normalizes the dataset for the specified company.
    4. Compares the two most recent records, if available.

    Parameters:
        company_id (str): The normalized company identifier.

    Returns:
        PerformanceComparisonResponse if two or more records exist,
        PerformanceComparisonInsufficientDataResponse if insufficient data is available.

    Raises:
        HTTPException: If required columns are missing or the company is not found.
    """
    # Create a mapping of normalized column names to original column names.
    expected_columns = {col.strip().lower(): col for col in company_df.columns}
    # Error handling: Check if the essential column "mq assessment date" exists.
    if "mq assessment date" not in expected_columns:
        raise HTTPException(status_code=500, detail="Column 'MQ Assessment Date' not found in dataset. Check CSV structure.")
    # Normalize the search for the specified company.
    history = company_df[company_df["company name"].str.strip().str.lower() == company_id.strip().lower()]
    # Error handling: If no records are found for the company, raise a 404 error.
    if history.empty:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found.")
    if len(history) < 2:
        # Safely parse available dates as DD/MM/YYYY, skipping unparseable ones
        available_years = []
        for date_str in history[expected_columns["mq assessment date"]].dropna():
            dt = datetime.strptime(date_str, "%d/%m/%Y") if date_str else None
            if dt:
                available_years.append(dt.year)

        return PerformanceComparisonInsufficientDataResponse(
            company_id=company_id,
            message=f"Only one record exists for '{company_id}', so performance comparison is not possible.",
            available_assessment_years=available_years
        )

    # Convert 'MQ Assessment Date' to integer year (DD/MM/YYYY)
    history = history.copy()
    history["assessment_year"] = history[expected_columns["mq assessment date"]].apply(
        lambda x: int(datetime.strptime(x, "%d/%m/%Y").year) if pd.notna(x) else None
    )
    history = history.sort_values(by="assessment_year", ascending=False)
    latest = history.iloc[0]
    previous = history.iloc[1]

    return PerformanceComparisonResponse(
        company_id=company_id,
        current_year=latest["assessment_year"],
        previous_year=previous["assessment_year"],
        latest_mq_score=str(latest.get(expected_columns.get("level"), "N/A")),
        previous_mq_score=str(previous.get(expected_columns.get("level"), "N/A")),
        latest_cp_alignment=str(latest.get(expected_columns.get("carbon performance alignment 2035"), "N/A")),
        previous_cp_alignment=str(previous.get(expected_columns.get("carbon performance alignment 2035"), "N/A")),
    )