import os
import pandas as pd

from fastapi import FastAPI
from typing import List
from .models import CountryData, Pillar, Area, Indicator, Metric
import re

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

    #remember which columns are area, indicator, metric
    area_cols = [re.sub(".*?\s", "", col) for col in data.columns if col.startswith("area")]
    indicator_cols = [re.sub(".*?\s", "", col) for col in data.columns if col.startswith("indicator")]
    metric_cols =  [re.sub(".*?\s", "", col) for col in data.columns if col.startswith("metric")] 

    #remove unecessary columns
    data = data[[col for col in data.columns if col.startswith(("area", "indicator", "metric"))]]

    #rename columns so they align with output
    remap_column_names = {col: re.sub(".*?\s", "", col) for col in data.columns}
    data = data.rename(columns=remap_column_names)

    #get flat Pandas series of country data
    data = data.iloc[0]
    data = data.fillna("")

    #get metric
    metrics = [{'name': metric, 'value': data[f'{metric}']} for metric in metric_cols]

    #get indicator
    indicators = [{'name': indicator, 'assessment': data[f"{indicator}"],
                   'metrics': next((met for met in metrics if met["name"].startswith(indicator)), "")} for indicator in indicator_cols]   

    #get area
    areas = [{'name': area, 'assessment': data[f"{area}"],
              'indicators': [ind for ind in indicators if ind["name"].startswith(area)]} for area in area_cols]

    #get pillar
    pillars = [{'name': pillar, 'areas': areas} for pillar in ["EP","CP","CF"]]

    output_dict = {'pillars': [pillar for pillar in pillars]}



    output = CountryData(**output_dict)

    return output