import os
import pandas as pd

from fastapi import APIRouter, HTTPException, FastAPI, Request
from schemas import CountryDataResponse
from services import CountryDataProcessor
from middleware.rate_limiter import limiter


# TODO: Handle the data loading in a better way
filepath = "./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx"
df_assessments = pd.read_excel(filepath, engine='openpyxl')

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
router = APIRouter(prefix="/ascor", tags=["ASCOR Endpoints"])

@router.get("/country-data/{country}/{assessment_year}", response_model=CountryDataResponse)
@limiter.limit("100/minute")
async def get_country_data(request: Request, country: str, assessment_year: int) -> CountryDataResponse:
    try:
        processor = CountryDataProcessor(df_assessments, country, assessment_year)
        return processor.process_country_data()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))