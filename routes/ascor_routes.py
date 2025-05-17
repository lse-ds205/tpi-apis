import os
import pandas as pd

from fastapi import APIRouter, HTTPException
from schemas import CountryDataResponse
from services import CountryDataProcessor

from fastapi import FastAPI, HTTPException

# TODO: Handle the data loading in a better way
filepath = "./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx"
df_assessments = pd.read_excel(filepath, engine='openpyxl')

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
router = APIRouter(prefix="/ascor", tags=["ASCOR Endpoints"])

@router.get("/country-data/{country}/{assessment_year}", response_model=CountryDataResponse)
async def get_country_data(country: str, assessment_year: int) -> CountryDataResponse:
    print(f"[ROUTE DEBUG] Received request: {country=}, {assessment_year=}")

    try:
        processor = CountryDataProcessor(df_assessments, country, assessment_year)
        result = processor.process_country_data()
        print("[ROUTE DEBUG] Result to return:", result.model_dump())
        return result
    except ValueError as e:
        print(f"[ROUTE DEBUG] ValueError: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[ROUTE DEBUG] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected server error.")