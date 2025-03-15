import pytest
import pandas as pd

from v1.app import app

from fastapi.testclient import TestClient

"""CONSTANTS

TODO: Create a config.py file to store these constants
"""

EXCEL_PATH = './data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx'

"""FIXTURES"""

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def df_assessments():
    """Database dependency"""
    df_assessments = pd.read_excel(EXCEL_PATH)
    df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'], format='%d/%m/%Y')
    df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'], format='%d/%m/%Y')
    try:
        yield df_assessments
    finally:
        # Any cleanup if needed
        pass