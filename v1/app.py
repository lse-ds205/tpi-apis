import os
import pandas as pd
import numpy as np

from .models_hierarchy import CountryData2
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

@app.get("/v1/country-data/{country}/{assessment_year}", response_model=CountryData2)
async def get_country_data(country: str, assessment_year: int) -> CountryData2:
    
    # Load the data
    df = pd.read_excel("./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx")

    # Convert the date columns to datetime type
    df['Assessment date'] = pd.to_datetime(df['Assessment date'], format='%d/%m/%Y')
    df['Publication date'] = pd.to_datetime(df['Publication date'], format='%d/%m/%Y')

    # Keep only relevant columns
    # df = df[[
    #    "area EP.1", "area EP.2", "area EP.3", "area CP.1", "area CP.2", "area CP.3", 
    #    "area CP.4", "area CP.5", "area CP.6", "area CF.1", "area CF.2", "area CF.3", 
    #    "area CF.4", "Country", "Assessment date"
    # ]]

    # Only keep the year in the "Assessment date" column
    df['Assessment date'] = df['Assessment date'].dt.year #converts the column entries to integers!

    # Filter for relevant rows
    df = df.loc[(df["Country"] == country) & (df["Assessment date"] == assessment_year)]

    # Filter out all NaNs
    df.replace(np.nan, "", inplace=True)

    # Rename the columns to remove the "area " prefix and replace the . with a _
    df.rename(columns=lambda x: x.replace("area ", "").replace(".", "_"), inplace=True)
    df.rename(columns={"Country": "country", "Assessment date": "assessment_year"}, inplace=True)

    # Convert dataframe to dictionary
    data = df.iloc[0]

    # Create dictionaries for each categorie of columns
    EP = {col: data[col] for col in data.index if col.startswith("EP")}
    CP = {col: data[col] for col in data.index if col.startswith("CP")}
    CF = {col: data[col] for col in data.index if col.startswith("CF")}

    # Create nested dictionaries (EP, CP and CF columns' dictionaries are nested in the output_dict dictionary)
    # The models which the output_dict is being passed to are nested analogously in models_hierarchy.py
    output_dict = {
    "country": country,
    "assessment_year": assessment_year,
    "EP": {"indicators": EP},
    "CP": {"indicators": CP},
    "CF": {"indicators": CF}
    }

    # Apply the model to the output to ensure output's correct data format
    output = CountryData2(**output_dict)

    return output
    