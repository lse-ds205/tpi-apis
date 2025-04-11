import os
import pandas as pd

from fastapi import APIRouter, HTTPException, Depends
from schemas import CountryDataResponse
from services import CountryDataProcessor
from log_config import get_logger

from fastapi import FastAPI, HTTPException

logger = get_logger(__name__)

# Define the filepath - using absolute path for reliable loading
filepath = "/Users/rishisiddharth/Desktop/LSE_2024_2045/classes/DS205W/Summative1_logging/tpi_apis/data/TPI_ASCOR_data_13012025/ASCOR_assessments_results.xlsx"

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

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
router = APIRouter(prefix="/ascor", tags=["ASCOR Endpoints"])

@router.get("/countries")
async def get_countries():
    """Get a list of all available countries in the dataset."""
    try:
        logger.info("Getting list of all countries")
        countries = df_assessments['Country'].unique().tolist()
        logger.info(f"Found {len(countries)} countries in the dataset")
        return {"countries": countries}
    except Exception as e:
        logger.exception(f"Error getting countries list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/country-data/{country}/{assessment_year}", response_model=CountryDataResponse)
async def get_country_data(country: str, assessment_year: int) -> CountryDataResponse:
    try:
        logger.info(f"Processing request for country: {country}, year: {assessment_year}")
        processor = CountryDataProcessor(df_assessments, country, assessment_year)
        result = processor.process_country_data()
        logger.info(f"Successfully processed data for {country}, {assessment_year}")
        return result
    except ValueError as e:
        logger.error(f"Value error for {country}, {assessment_year}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error processing data for {country}, {assessment_year}: {e}")
        raise HTTPException(status_code=500, detail=str(e))