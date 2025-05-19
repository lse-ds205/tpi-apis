import os
import pandas as pd

from fastapi import APIRouter, HTTPException
from schemas import CountryDataResponse
from services import CountryDataProcessor

from fastapi import FastAPI, HTTPException
from fastapi import Path

# TODO: Handle the data loading in a better way
filepath = "./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx"
df_assessments = pd.read_excel(filepath, engine='openpyxl')

# Load CP assessment file for ISIN-country mapping
CP_ISIN_FILE = "data/TPI sector data - All sectors - 08032025/CP_Assessments_08032025.csv"
cp_df = pd.read_csv(CP_ISIN_FILE)
cp_df.columns = cp_df.columns.str.strip().str.lower()

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
router = APIRouter(prefix="/ascor", tags=["ASCOR Endpoints"])

@router.get("/country-data/{country_identifier}/{assessment_year}", response_model=CountryDataResponse)
async def get_country_data(
    country_identifier: str = Path(..., description="Country identifier (3-letter ISO code, name, or ID; case-insensitive)"),
    assessment_year: int = Path(..., description="Assessment year (e.g., 2023)")
) -> CountryDataResponse:
    """
    Retrieve ASCOR data for a given country and assessment year.
    The country_identifier can be a 3-letter ISO code (e.g., 'AUS'), a country name (e.g., 'Australia'), or a country ID (e.g., '8').
    If an ISO code is provided, it will be mapped to the country using the CP assessment file, then used to fetch ASCOR data.
    Matching is case-insensitive and will try ISO code, then ID, then name.
    """
    # Try ISO code mapping first (using Geography Code in CP file)
    iso_lower = country_identifier.strip().lower()
    match = cp_df[cp_df['geography code'].astype(str).str.strip().str.lower() == iso_lower]
    if not match.empty:
        mapped_country = match.iloc[0]['geography']
        country_identifier = mapped_country
    try:
        processor = CountryDataProcessor(df_assessments, country_identifier, assessment_year)
        return processor.process_country_data()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))