import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from .models import CountryData

file_path = './data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx'
df_assessments = pd.read_excel(file_path)
df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'], format='%d/%m/%Y')
df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'], format='%d/%m/%Y')


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

@app.get("/v1/country-data/{country}/{assessment_year}", response_model=CountryData)
async def get_country_data(country: str, assessment_year: int):
    mask = (
        (df_assessments['Country'] == country) &
        (df_assessments['Assessment date'].dt.year == assessment_year)
    )

    if not df_assessments[mask].empty:
        data = df_assessments[mask].iloc[0]
        EP = {col: data[col] for col in data.index if col.startswith("EP")}
        CP = {col: data[col] for col in data.index if col.startswith("CP")}
        CF = {col: data[col] for col in data.index if col.startswith("CF")}

        output_dict = {
            "country": country,
            "assessment_year": assessment_year,
            "EP": {"indicators": EP},
            "CP": {"indicators": CP},
            "CF": {"indicators": CF}
        }
        return output_dict
    else:
        raise HTTPException(status_code=404, detail="Data not found for the specified country and year")