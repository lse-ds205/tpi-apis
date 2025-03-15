import os
import pandas as pd

from fastapi import FastAPI, HTTPException

from .models import CountryDataResponse
from .services import CountryDataProcessor

def __is_running_on_nuvolos():
    """
    If we are running this script from Nuvolos Cloud, 
    there will be an environment variable called HOSTNAME
    which starts with 'nv-'
    """

    hostname = os.getenv("HOSTNAME")
    return hostname is not None and hostname.startswith('nv-')

if __is_running_on_nuvolos():
    # Nuvolos alters the URL of the API (likely for security reasons)
    # Instead of https://A-BIG-IP-ADDRESS:8000/
    # The API is actually served at https://A-BIG-IP-ADDRESS/proxy/8000/
    app = FastAPI(root_path="/proxy/8000/")
else:
    # No need to set up anything else if running this on local machine
    app = FastAPI()

# TODO: Handle the data loading in a better way
filepath = "./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx"
df_assessments = pd.read_excel(filepath, engine='openpyxl')

@app.get("/")
async def read_root():
    return {"Hello": "World"} 

@app.get("/v1/country-data/{country}/{assessment_year}", response_model=CountryDataResponse)
async def get_country_data(country: str, assessment_year: int) -> CountryDataResponse:
    try:
        processor = CountryDataProcessor(df_assessments, country, assessment_year)
        return processor.process_country_data()
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
