import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from .models import CountryData 

app = FastAPI()

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
    df_filtered = df_assessments[(df_assessments['Country'] == country) & (df_assessments['Assessment date'].dt.year == assessment_year)]

    if df_filtered.empty:
        raise HTTPException(status_code=404, detail="Data not found for the specified country and year")
    
    # Extract the relevant columns
    key_columns = [col for col in df_filtered.columns if col.startswith(('area EP.', 'area CP.', 'area CF.', 'indicator EP.', 'indicator CP.', 'indicator CF.')) and not any(suffix in col for suffix in ['.a', '.b', '.c', '.d', '.e', '.i', '.ii'])]
    # output_dict = df_filtered[key_columns].iloc[0].to_dict()
    df_filtered = df_filtered[key_columns]

    # Rename columns to match the expected keys
    df_filtered.rename(columns={
        'area EP.1': 'EP.1',
        'area EP.2': 'EP.2',
        'area EP.3': 'EP.3',
        'area CP.1': 'CP.1',
        'area CP.2': 'CP.2',
        'area CP.3': 'CP.3',
        'area CP.4': 'CP.4',
        'area CP.5': 'CP.5',
        'area CP.6': 'CP.6',
        'area CF.1': 'CF.1',
        'area CF.2': 'CF.2',
        'area CF.3': 'CF.3',
        'area CF.4': 'CF.4'
    }, inplace=True)

    output_dict = df_filtered.iloc[0].to_dict()

    # Replace missing values with an empty string
    output_dict = {k: (v if pd.notna(v) else "") for k, v in output_dict.items()}

    # Add country and assessment_year to the result
    output_dict['country'] = country
    output_dict['assessment_year'] = assessment_year

    output = CountryData(country=output_dict['country'],
                         assessment_year=output_dict['assessment_year'],
                         EP_1=output_dict['EP.1'],
                         EP_2=output_dict['EP.2'],
                         EP_3=output_dict['EP.3'],
                         CP_1=output_dict['CP.1'],
                         CP_2=output_dict['CP.2'],
                         CP_3=output_dict['CP.3'],
                         CP_4=output_dict['CP.4'],
                         CP_5=output_dict['CP.5'],
                         CP_6=output_dict['CP.6'],
                         CF_1=output_dict['CF.1'],
                         CF_2=output_dict['CF.2'],
                         CF_3=output_dict['CF.3'],
                         CF_4=output_dict['CF.4'])
    
    return output