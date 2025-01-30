import os
import pandas as pd
import numpy as np

from .models import CountryData
from fastapi import FastAPI

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
    
    # Load the data
    df = pd.read_excel("./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx")

    # Convert the date columns to datetime type
    df['Assessment date'] = pd.to_datetime(df['Assessment date'], format='%d/%m/%Y')
    df['Publication date'] = pd.to_datetime(df['Publication date'], format='%d/%m/%Y')

    # Keep only relevant columns
    df = df[[
        "area EP.1", "area EP.2", "area EP.3", "area CP.1", "area CP.2", "area CP.3", 
        "area CP.4", "area CP.5", "area CP.6", "area CF.1", "area CF.2", "area CF.3", 
        "area CF.4", "Country", "Assessment date"
    ]]

    # Only keep the year in the "Assessment date" column
    df['Assessment date'] = df['Assessment date'].dt.year #converts the column entries to integers!

    # Filter for relevant rows
    df = df.loc[(df["Country"] == country) & (df["Assessment date"] == assessment_year)]

    # Filter out all NaNs
    df.replace(np.nan, "", inplace=True)

    # Rename the columns to remove the "area " prefix
    df.rename(columns=lambda x: x.replace("area ", ""), inplace=True)
    df.rename(columns={"Country": "country", "Assessment date": "assessment_year"}, inplace=True)

    # Convert dataframe to dictionary
    my_dict = df.to_dict(orient="records")

    # Silly non-data-driven response for now
    return my_dict
    