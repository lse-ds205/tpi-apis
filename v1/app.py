import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from .models import CountryData 

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
async def get_country_data(country: str, assessment_year: int) -> CountryData:
   
    # Load the data in ASCOR_assessment_results.xlsx
    filepath = "./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx" # Specify the correct path to the file
    df_assessments = pd.read_excel(filepath)

    # Convert the date columns to datetime type so we can filter by year later
    df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'])
    df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'])

    # Filter the data for the specified country and year
    requirement = (df_assessments['Country'] == country) & (df_assessments['Assessment date'].dt.year == assessment_year)
    df_filtered = df_assessments[requirement]

    # if df_filtered.empty:
    #     raise HTTPException(status_code=404, detail="Data not found for the specified country and year")

    # Extract the relevant columns
    area_columns = [col for col in df_filtered.columns if col.startswith(('area')) and not any(suffix in col for suffix in ['.a', '.b', '.c', '.d', '.e', '.i', '.ii'])]

    # JSON does not allow for NaN or NULL. 
    # The equivalent is just to leave an empty string instead
    df_filtered = df_filtered.fillna('')


    # Add country and assessment_year to the result
    df_filtered['country'] = country
    df_filtered['assessment_year'] = assessment_year
    
    remap_area_column_names = {
        col: col.replace('area ', '').replace('.', '_')
        for col in area_columns
    }

    df_filtered = df_filtered.rename(columns=remap_area_column_names)

    # Grab just the first element (there should only be one anyway) and return it as a dictionary
    output_dict = df_filtered.iloc[0].to_dict()

    output = CountryData(**output_dict)

    return output