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
    # Filter data using pandas boolean indexing
    mask = (df_assessments["Country"] == country) & (df_assessments['Assessment date'].dt.year == assessment_year)
    data = df_assessments[mask].iloc[0] if not df_assessments[mask].empty else None

    if data is None:
        raise HTTPException(status_code=404, 
                          detail=f"No data found for country: {country} and year: {assessment_year}")

    def get_metrics(indicator_name: str) -> Optional[Metric]:
        # Find all metric columns for this indicator
        metric_cols = [col for col in data.index 
                      if col.startswith(f'metric {indicator_name}')]
        
        # Return first valid metric if any exist
        valid_metrics = [
            Metric(name=col.replace('metric ', ''), value=str(data[col]))
            for col in metric_cols
            if pd.notna(data[col]) and data[col] != ""
        ]
        return valid_metrics[0] if valid_metrics else None

    def create_indicators_for_area(area_name: str) -> List[Indicator]:
        # Find all indicators for this area using pandas string methods
        indicator_cols = data.index[data.index.str.startswith(f'indicator {area_name}')]
        
        indicators = []
        for col in indicator_cols:
            if pd.notna(data[col]):
                base_name = col.replace('indicator ', '')
                metric = get_metrics(base_name)
                
                # Create indicator with or without metrics
                indicator_dict = {
                    "name": base_name,
                    "assessment": str(data[col])
                }
                if metric:
                    indicator_dict["metrics"] = metric
                
                indicators.append(Indicator(**indicator_dict))
        
        return indicators

    # Create pillars using list comprehension
    pillars = [
        Pillar(
            name=pillar_name,
            areas=[
                Area(
                    name=col.replace('area ', ''),
                    assessment=str(data[col]),
                    indicators=create_indicators_for_area(col.replace('area ', ''))
                )
                for col in data.index[data.index.str.startswith(f'area {pillar_name}.')]
                if pd.notna(data[col])
            ]
        )
        for pillar_name in ["EP", "CP", "CF"]
        if any(col.startswith(f'area {pillar_name}.') for col in data.index)
    ]

    return ResponseData(pillars=pillars)