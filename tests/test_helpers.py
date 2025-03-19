# tests/test_helpers.py
import re
import pytest
from datetime import datetime
from pathlib import Path
from routes.company_routes import get_latest_data_dir

def test_get_latest_data_dir_with_valid_dirs(tmp_path):
    """
    Create temporary directories to simulate data folders,
    and verify that get_latest_data_dir returns the one with the latest date.
    """
    prefix = "TPI sector data - All sectors - "
    # Create two temporary directories with valid dates in their names.
    d1 = tmp_path / f"{prefix}01012021"
    d1.mkdir()
    d2 = tmp_path / f"{prefix}12312021"
    d2.mkdir()
    # Test function should return d2 because it is later.
    latest = get_latest_data_dir(tmp_path, prefix)
    assert latest == d2

def test_get_latest_data_dir_with_no_valid_dirs(tmp_path):
    """
    If no directories match the prefix, function should raise FileNotFoundError.
    """
    with pytest.raises(FileNotFoundError):
        get_latest_data_dir(tmp_path, "Nonexistent Prefix")
