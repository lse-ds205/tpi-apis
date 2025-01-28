import os
import pandas as pd

from fastapi import FastAPI
df_assessments = pd.read_excel("./data/TPI ASCOR data - 13012025/ASCOR_assessments_results_trends_pathways.xlsx")

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

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/v1/country-data/{country}/{assessment_year}")
async def get_country_data(country: str, assessment_year: int):
    mask = (df_assessments["Country"] == country &
    (df_assessments["Assessment date"].dt.year))
    return {"Message": f"You requested data for {country} in {assessment_year}. Eventually, we will return the data here."}





