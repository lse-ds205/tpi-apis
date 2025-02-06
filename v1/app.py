import os
import pandas as pd
import uvicorn

from .models import CountryData, Metric, ResponseData, Indicator, Area, Pillar
from fastapi import FastAPI, HTTPException
from typing import List, Optional

df_assessments = pd.read_excel(r"C:\Users\kbhatia2\Desktop\DS205\ascor-api\data\TPI ASCOR data - 13012025\ASCOR_assessments_results.xlsx")
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
        raise ValueError

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
    
    # Grab just the first element (there should only be one anyway)
    # and return it as a dictionary

    data = data.iloc[0]

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

    output = CountryData(**output_dict)
    return output

@app.get("/v1/country-metrics/{country}/{assessment_year}", response_model=List[Metric])
async def get_country_metrics(country: str, assessment_year: int):

    selected_row = (
        (df_assessments["Country"] == country) &
        (df_assessments['Assessment date'].dt.year == assessment_year)
    )

    # Filter the data
    data = df_assessments[selected_row]

    if data.empty:
        raise HTTPException(status_code=404, 
                            detail=f"There is no data for country: {country} and year: {assessment_year}")

    # Select just the metrics
    metric_columns = [col for col in df_assessments.columns 
                      if col.startswith('metric')]
    data = data[metric_columns]

    # JSON does not allow for NaN or NULL. 
    # The equivalent is just to leave an empty string instead
    data = data.fillna('')

    remap_area_column_names = {
        col: col.replace('metric ', '')
        for col in metric_columns
    }

    data = data.rename(columns=remap_area_column_names)

    data_as_dict = data.iloc[0].to_dict()

    list_metrics = []
    for name, value in data_as_dict.items():
        individual_metric = Metric(name=name, value=value)
        list_metrics.append(individual_metric)
    # Grab just the first element (there should only be one anyway)
    # and return it as a dictionary
    return list_metrics

@app.get("/v1/country-structure/{country}/{assessment_year}", response_model=ResponseData)
async def get_country_structure(country: str, assessment_year: int):
    selected_row = (
        (df_assessments["Country"] == country) &
        (df_assessments['Assessment date'].dt.year == assessment_year)
    )

    # Filter the data
    data = df_assessments[selected_row]

    if data.empty:
        raise HTTPException(status_code=404, 
                          detail=f"There is no data for country: {country} and year: {assessment_year}")

    # Get the first row as a Series
    data = data.iloc[0]
    
    # Helper function to extract metrics for an indicator
    def get_metrics(indicator_name: str) -> Optional[Metric]:
        metric_col = f"metric {indicator_name}"
        if metric_col in data.index and pd.notna(data[metric_col]):
            return Metric(name=indicator_name, value=str(data[metric_col]))
        return None

    # Helper function to create sub-indicators for a parent indicator
    def create_sub_indicators(parent_prefix: str) -> List[Indicator]:
        sub_indicators = []
        # Find all columns that start with the parent prefix and have an additional level
        sub_indicator_cols = [col for col in data.index 
                            if col.startswith(f"area {parent_prefix}.")
                            and len(col.replace(f"area {parent_prefix}.", "").split(".")) >= 1]
        
        for col in sub_indicator_cols:
            indicator_name = col.replace("area ", "")
            if pd.notna(data[col]):  # Only include if there's a value
                sub_indicators.append(
                    Indicator(
                        name=indicator_name,
                        assessment=str(data[col]),
                        metrics=get_metrics(indicator_name)
                    )
                )
        return sub_indicators

    # Helper function to create area indicators
    def create_area_indicators(area_prefix: str) -> List[Indicator]:
        indicators = []
        # Find direct child indicators of this area
        area_cols = [col for col in data.index 
                    if col.startswith(f"area {area_prefix}")]
        
        for col in area_cols:
            indicator_name = col.replace("area ", "")
            if pd.notna(data[col]):  # Only include if there's a value
                sub_indicators = create_sub_indicators(indicator_name)
                indicators.append(
                    Indicator(
                        name=indicator_name,
                        assessment=str(data[col]),
                        metrics=get_metrics(indicator_name),
                        indicators=sub_indicators if sub_indicators else None
                    )
                )
        return indicators

    # Create pillars
    pillars = []
    for pillar_name in ["EP", "CP", "CF"]:
        # Find all areas for this pillar
        area_prefixes = set(
            col.split(".")[0] + "." + col.split(".")[1]
            for col in data.index 
            if col.startswith(f"area {pillar_name}.")
        )
        
        areas = []
        for area_prefix in area_prefixes:
            clean_prefix = area_prefix.replace("area ", "")
            if f"area {clean_prefix}" in data.index:
                area_assessment = str(data[f"area {clean_prefix}"])
                areas.append(
                    Area(
                        name=clean_prefix,
                        assessment=area_assessment,
                        indicators=create_area_indicators(clean_prefix)
                    )
                )
        
        pillars.append(
            Pillar(
                name=pillar_name,
                areas=areas
            )
        )

    return ResponseData(pillars=pillars)