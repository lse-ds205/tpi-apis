import os
import pandas as pd

from fastapi import FastAPI
from typing import List

from pydantic import BaseModel, Field
from typing import Literal





# Load the data
filepath = "./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx" # Specify the correct path to the file
df_assessments = pd.read_excel(filepath)

# Convert the date columns to datetime type so we can filter by year later
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

@app.get("/v1/country-data/{country}/{assessment_year}", response_model = CountryData)
async def get_country_data(country: str, assessment_year: int) -> CountryData:

    data = df_assessments[(df_assessments["Country"] == country) & (df_assessments["Assessment date"].dt.year == assessment_year)]

    #filter for the area columns
    area_columns = [col for col in data.columns if col.startswith("area")]
    data = data[area_columns]
    data['country'] = country
    data['assessment_year'] = assessment_year

    #JSON does not allow for NaN or NULL
    data = data.fillna("")

    #rename columns
    remap_area_column_names = {
        col: col.replace('area ', '').replace(".", "_") for col in area_columns
    }

    data = data.rename(columns=remap_area_column_names)

    #Grab just the first row and return it as a dictionary.
    #Even though there should only be one row anyway, we specify it because we want to convert to dictionary
    output_dict = data.iloc[0].to_dict()

    output = CountryData(**output_dict)

    return output