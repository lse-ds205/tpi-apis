# tests/test_helpers.py
import re
import pytest
from datetime import datetime
from pathlib import Path
from utils import (
    get_latest_data_dir,
    get_latest_assessment_file,
    get_latest_cp_file,
    normalize_company_id,
)


# ------------------------------------------------------------------------------
# Tests for get_latest_data_dir
# ------------------------------------------------------------------------------
def test_get_latest_data_dir_with_valid_dirs(tmp_path):
    """Test that the latest directory is correctly selected based on date."""
    prefix = "TPI sector data - All sectors - "
    d1 = tmp_path / f"{prefix}01012021"
    d1.mkdir()
    d2 = tmp_path / f"{prefix}12312021"
    d2.mkdir()

    latest = get_latest_data_dir(tmp_path, prefix)
    assert latest == d2


def test_get_latest_data_dir_with_no_valid_dirs(tmp_path):
    """Test that FileNotFoundError is raised when no matching dirs exist."""
    with pytest.raises(FileNotFoundError):
        get_latest_data_dir(tmp_path, "Nonexistent Prefix")


# ------------------------------------------------------------------------------
# Tests for get_latest_assessment_file
# ------------------------------------------------------------------------------
def test_get_latest_assessment_file_with_valid_files(tmp_path):
    """
    Verify that get_latest_assessment_file picks the file with the latest date
    based on the naming pattern: Company_Latest_Assessments_*.csv
    """
    # Create two files with valid date suffixes
    f1 = tmp_path / "Company_Latest_Assessments_01012021.csv"
    f1.touch()
    f2 = tmp_path / "Company_Latest_Assessments_12312021.csv"
    f2.touch()

    latest_file = get_latest_assessment_file(
        "Company_Latest_Assessments_*.csv", tmp_path
    )
    assert latest_file == f2


def test_get_latest_assessment_file_no_matches(tmp_path):
    """
    If no files match the pattern, the function should raise FileNotFoundError.
    """
    with pytest.raises(FileNotFoundError):
        get_latest_assessment_file(
            "Company_Latest_Assessments_*.csv", tmp_path
        )


def test_get_latest_assessment_file_invalid_date(tmp_path):
    """
    If filenames have invalid or no date, fallback to alphabetical sorting.
    'abc' > '99999999' alphabetically, so f1 is returned.
    """
    f1 = tmp_path / "Company_Latest_Assessments_abc.csv"
    f1.touch()
    f2 = tmp_path / "Company_Latest_Assessments_99999999.csv"
    f2.touch()

    latest_file = get_latest_assessment_file(
        "Company_Latest_Assessments_*.csv", tmp_path
    )
    assert latest_file == f1


# ------------------------------------------------------------------------------
# Tests for get_latest_cp_file
# ------------------------------------------------------------------------------
def test_get_latest_cp_file_with_valid_files(tmp_path):
    """Ensure we get a sorted list of CP files matching the pattern CP_Assessments_*.csv."""
    f1 = tmp_path / "CP_Assessments_01012021.csv"
    f2 = tmp_path / "CP_Assessments_02012021.csv"
    f1.touch()
    f2.touch()

    files = get_latest_cp_file("CP_Assessments_*.csv", tmp_path)
    assert len(files) == 2
    assert files[0] == f1
    assert files[1] == f2


def test_get_latest_cp_file_no_matches(tmp_path):
    """Test that FileNotFoundError is raised when no CP files are found."""
    with pytest.raises(FileNotFoundError):
        get_latest_cp_file("CP_Assessments_*.csv", tmp_path)


# ------------------------------------------------------------------------------
# Tests for normalize_company_id
# ------------------------------------------------------------------------------
def test_normalize_company_id_basic():
    """Test basic company ID normalization."""
    assert normalize_company_id("  3M  ") == "3m"
    assert normalize_company_id("Apple Inc") == "apple_inc"
    assert normalize_company_id("MICROSOFT  ") == "microsoft"


def test_normalize_company_id_empty_string():
    """Test behavior when input string is empty or only spaces."""
    assert normalize_company_id("") == ""
    assert normalize_company_id("   ") == ""


def test_normalize_company_id_with_punctuation():
    """
    Ensure punctuation is preserved but spaces are replaced with underscores.
    """
    assert normalize_company_id("Johnson & Johnson") == "johnson_&_johnson"
    assert normalize_company_id("3M.Co") == "3m.co"
