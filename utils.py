"""
Utility functions for data loading and normalization.

This module provides helper functions used across the TPI API project, including:
- Selecting the latest available data directory and CSV files based on naming conventions
- Extracting embedded dates from filenames and folder names
- Normalizing company names into consistent, URL-safe identifiers
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
import re
from pathlib import Path
from datetime import datetime
from typing import List


# -------------------------------------------------------------------------
# Utility Functions for Data Loading, File Selection, and Normalization
# -------------------------------------------------------------------------
def get_latest_data_dir(
    base_data_dir: Path, prefix: str = "TPI sector data - All sectors - "
) -> Path:
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
    matching_dirs = [
        d
        for d in base_data_dir.iterdir()
        if d.is_dir() and d.name.startswith(prefix)
    ]

    if not matching_dirs:
        raise FileNotFoundError(
            "No data directories found with the specified prefix."
        )

    # Match directories with valid MMDDYYYY suffixes
    date_pattern = re.compile(rf"^{re.escape(prefix)}(\d{{8}})$")
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

    if not dirs_with_dates:
        # Fall back to lexicographic sort if no valid dates found
        matching_dirs.sort()
        return matching_dirs[-1]

    # Return the directory with the latest valid date
    dirs_with_dates.sort(key=lambda x: x[1])
    return dirs_with_dates[-1][0]


def get_latest_assessment_file(pattern: str, data_dir: Path) -> Path:
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
    files = list(data_dir.glob(pattern))

    if not files:
        raise FileNotFoundError("No company assessments files found.")

    date_pattern = re.compile(r"_(\d{8})\.csv$")

    def extract_date(file_path: Path):
        match = date_pattern.search(file_path.name)
        if match:
            date_str = match.group(1)
            try:
                return datetime.strptime(date_str, "%m%d%Y")
            except ValueError:
                return None
        return None

    files_with_dates = [(f, extract_date(f)) for f in files]

    files_with_dates = [(f, d) for f, d in files_with_dates if d is not None]

    if not files_with_dates:
        # Fall back to alphabetic order if no valid dates
        files.sort()
        return files[-1]
    files_with_dates.sort(key=lambda x: x[1])

    # Return the file with the latest valid date
    return files_with_dates[-1][0]


def get_latest_cp_file(pattern: str, data_dir: Path) -> List[Path]:
    """
    Finds and returns a sorted list of CP assessment files matching the pattern
    (e.g., CP_Assessments_*.csv) in the latest data directory.

    Parameters:
        pattern (str): Glob pattern to match the files (e.g., "CP_Assessments_*.csv").
        data_dir (Path): The directory containing the CSV files.

    Returns:
        List[Path]: A sorted list of file paths matching the pattern.

    Raises:
        FileNotFoundError: If no files matching the pattern are found.
    """
    files = sorted(data_dir.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No CP datasets found in {data_dir}")
    return files


def normalize_company_id(company_name: str) -> str:
    """
    Normalizes a company name into a lowercase, underscore-separated identifier.

    Steps:
        1. Strip leading/trailing whitespace
        2. Replace internal spaces with underscores
        3. Convert to lowercase

    Parameters:
        company_name (str): Raw company name.

    Returns:
        str: Normalized company identifier.
    """
    return company_name.strip().replace(" ", "_").lower()
