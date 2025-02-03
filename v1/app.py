import os
import pandas as pd

from fastapi import FastAPI, HTTPException

from .models import CountryData

df_assessments = pd.read_excel("./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx")
df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'])
df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'])

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

    selected_row = (
        (df_assessments["Country"] == country) &
        (df_assessments['Assessment date'].dt.year == assessment_year)
    )

    # Filter the data
    data = df_assessments[selected_row]

    if data.empty:
        raise HTTPException(status_code=404, 
                            detail=f"There is no data for country: {country} and year: {assessment_year}")

    # Selected and filter columns
    area_columns = [col for col in df_assessments.columns if col.startswith("area")]
    data = data[area_columns]

    # JSON does not allow for NaN or NULL. 
    # The equivalent is just to leave an empty string instead
    data = data.fillna('')

    #Rename columns
    data['country'] = country
    data['assessment_year'] = assessment_year

    remap_area_column_names = {
        col: col.replace('area ', '').replace('.', '_')
        for col in area_columns
    }

    data = data.rename(columns=remap_area_column_names)
    output_dict = data.iloc[0].to_dict()

    output = CountryData(**output_dict)

    # Grab just the first element (there should only be one anyway)
    # and return it as a dictionary
    return output
