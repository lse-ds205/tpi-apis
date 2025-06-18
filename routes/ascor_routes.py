import os
import pandas as pd

from fastapi import APIRouter, HTTPException, FastAPI, Request, Depends, Path
from schemas import CountryDataResponse
from services import CountryDataProcessor
from middleware.rate_limiter import limiter
from log_config import get_logger

logger = get_logger(__name__)

# Define the filepath 
filepath = "./data/TPI_ASCOR_data_13012025/ASCOR_assessments_results.xlsx"

# Try to load the data, or create a mock dataframe if the file is missing
try:
    logger.info(f"Attempting to load data from {filepath}")
    df_assessments = pd.read_excel(filepath, engine='openpyxl')
    logger.info(f"Successfully loaded data from {filepath}")
except FileNotFoundError as e:
    logger.warning(f"Data file not found: {e}. Creating mock data instead.")
    # Create a comprehensive mock DataFrame with all required fields for testing
    mock_data = {
        'Country': ['United Kingdom', 'France', 'Germany'],
        'Publication date': ['01/01/2023', '01/01/2023', '01/01/2023'],
        'Assessment date': ['01/01/2023', '01/01/2023', '01/01/2023'],
        
        # EP (Emissions Pledges) pillar
        'area EP.1': ['Good', 'Good', 'Medium'],
        'indicator EP.1.1': ['Good', 'Good', 'Medium'],
        'year metric EP.1.1.1': ['50%', '45%', '30%'],
        'source metric EP.1.1.1': ['Report', 'Report', 'Report'],
        'source indicator EP.1.1': ['Source 1', 'Source 1', 'Source 1'],
        
        # CP (Carbon Performance) pillar
        'area CP.1': ['Good', 'Medium', 'Poor'],
        'indicator CP.1.1': ['Good', 'Medium', 'Poor'],
        'year metric CP.1.1.1': ['60%', '40%', '20%'],
        'source metric CP.1.1.1': ['Report', 'Report', 'Report'],
        'source indicator CP.1.1': ['Source 2', 'Source 2', 'Source 2'],
        
        # CF (Climate Finance) pillar
        'area CF.1': ['Medium', 'Poor', 'Good'],
        'indicator CF.1.1': ['Medium', 'Poor', 'Good'],
        'year metric CF.1.1.1': ['35%', '15%', '55%'],
        'source metric CF.1.1.1': ['Report', 'Report', 'Report'],
        'source indicator CF.1.1': ['Source 3', 'Source 3', 'Source 3']
    }
    
    # Create DataFrame from mock data
    df_assessments = pd.DataFrame(mock_data)
    
    # Convert dates to the expected format
    df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'], format='%d/%m/%Y')
    df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'], format='%d/%m/%Y')
    
    logger.info("Created mock data with sample values for all three pillars (EP, CP, CF)")

# Load CP assessment file for ISIN-country mapping
CP_ISIN_FILE = "data/TPI_sector_data_All_sectors_08032025/CP_Assessments_08032025.csv"
cp_df = pd.read_csv(CP_ISIN_FILE)
cp_df.columns = cp_df.columns.str.strip().str.lower()

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
router = APIRouter(tags=["ASCOR Endpoints"])

@router.get("/countries")
@limiter.limit("100/minute")
async def get_countries(request: Request):
    """Get a list of all available countries in the dataset."""
    try:
        logger.info("Getting list of all countries")
        countries = df_assessments['Country'].unique().tolist()
        logger.info(f"Found {len(countries)} countries in the dataset")
        return {"countries": countries}
    except Exception as e:
        logger.exception(f"Error getting countries list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/country-data/{country_identifier}/{assessment_year}", response_model=CountryDataResponse)
@limiter.limit("100/minute")
async def get_country_data(
    request: Request,
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
    
    print(f"[ROUTE DEBUG] Received request: {country_identifier=}, {assessment_year=}")

    try:
        logger.info(f"Processing request for country: {country_identifier}, year: {assessment_year}")
        processor = CountryDataProcessor(df_assessments.copy(), country_identifier, assessment_year)
        result = processor.process_country_data()
        logger.info(f"Successfully processed data for {country_identifier}, {assessment_year}")
        # Use when debugging
        # logger.debug(f"[ROUTE DEBUG] Result to return: {result.model_dump()}")
        return result
    except ValueError as e:
        logger.error(f"Value error for {country_identifier}, {assessment_year}: {e}")
        print(f"[ROUTE DEBUG] ValueError: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error processing data for {country_identifier}, {assessment_year}: {e}")
        print(f"[ROUTE DEBUG] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected server error.")