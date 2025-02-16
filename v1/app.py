import os
import pandas as pd
import numpy as np

# Refer to python file in which model is specified and from which this model is imported (file should be in the same directory)
from .models_hierarchy import CountryData1, CountryData2 # CountryData is the model's name
from fastapi import FastAPI, HTTPException
from typing import List

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

# Route with 1-level nested dictionary (Week 2 class)
@app.get("/v1/country-data-1/{country}/{assessment_year}", response_model=CountryData1)
async def get_country_data(country: str, assessment_year: int) -> CountryData1:
    
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
    output = CountryData1(**output_dict) # By using ** we easily can apply the entire output_dict to the model instead of having to map every single element of the model (e.g., country or EP_1) to a specific output value inside the output_dict

    return output

# Route with multiple layers (Week 2 and 3 Formative Exercise)
@app.get("/v1/country-data-2/{country}/{assessment_year}", response_model=CountryData2)
async def get_country_data(country: str, assessment_year: int) -> CountryData2:
    
    # Load the data
    df = pd.read_excel("./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx")

    # Convert the date columns to datetime type
    df['Assessment date'] = pd.to_datetime(df['Assessment date'], format='%d/%m/%Y')
    df['Publication date'] = pd.to_datetime(df['Publication date'], format='%d/%m/%Y')

    # Only keep the year in the "Assessment date" column
    df['Assessment date'] = df['Assessment date'].dt.year #converts the column entries to integers!

    # Filter for relevant rows
    df = df.loc[(df["Country"] == country) & (df["Assessment date"] == assessment_year)]

    # Filter out all NaNs
    df.replace(np.nan, "", inplace=True)

    # Rename the columns to remove the "area " prefix and replace the . with a _
    df.rename(columns=lambda x: x.replace(".", "_"), inplace=True)

    # Drop all columns which don't contain a EP,CP or CF
    df_filtered = df.filter(regex="EP|CP|CF")

    # Drop all columns which contain a "source" and a "year" in their names because they don't fit the "metrics", "indicators", "areas" and "pillars" logic
    columns_to_drop = [col for col in df_filtered.columns if any(x in col for x in ["source", "year"])]
    df_filtered = df_filtered.drop(columns=columns_to_drop)

    # Rename the columns so that the EP/CP/CF code is at the beginning of the column name
    def rename_columns(col_name):
        # Split the column name into parts
        parts = col_name.split()
        
        # Check if there are multiple parts and if the last part starts with EP, CP, or CF
        if len(parts) > 1 and any(parts[-1].startswith(code) for code in ["EP", "CP", "CF"]):
            # Reorder: code + string
            return f"{parts[-1]} {' '.join(parts[:-1])}"
        else:
            # Return the original column name if it doesn't match the pattern
            return col_name

    # Apply the function to rename the columns
    df_filtered.columns = [rename_columns(col) for col in df_filtered.columns]

    # Convert dataframe to pandas series
    data = df.iloc[0]

    # Let client know if his request was un-servable
    if data.empty:
        raise HTTPException(status_code=404, 
                            detail=f"This combination of {country} and {year} is unavailable.")

    # Initiate the nested output list
    pillars = []
    pillars_values = ["EP", "CP", "CF"]

    # Populate the output list
    for pillar in pillars_values:
        areas = []
        for area in data.index:
            if area.startswith(pillar) and "area" in area.split():
                indicators = []
                for indicator in data.index:
                    if indicator.startswith(area.split()[0]) and "indicator" in indicator.split():
                        metrics = []
                        for metric in data.index:
                            if metric.startswith(indicator.split()[0]) and "metric" in metric.split():
                                metrics.append({
                                    "name": metric.split()[0],
                                    "value": data[metric]
                                })
                        indicators.append({
                            "name": indicator.split()[0],
                            "assessment": data[indicator],
                            "metrics": metrics
                        })
                areas.append({
                    "name": area.split()[0],
                    "assessment": data[area],
                    "indicators": indicators
                })
        pillars.append({
            "name": pillar,
            "areas": areas
        })

    # Apply the model to the output to ensure output's correct data format
    output = CountryData2(pillars = pillars)

    return output
    