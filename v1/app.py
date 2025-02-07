# address: http://localhost:8000/v1/country-data/Italy/2024

import os
import pandas as pd

from typing import List

from fastapi import FastAPI, HTTPException

from .models import CountryData, Metric, Indicator, Area, Pillar

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

# FORMATIVE 3: i have created 4 different end points for metrics, indicators, areas and pillars
# by breaking it down it means the user can specify what level of detail they are interested in 

# this end point retrieves indicators and their nested metrics 
@app.get("/v1/country-indicators/{country}/{assessment_year}", response_model=List[Indicator])
async def get_country_indicators(country: str, assessment_year: int):
    selected_data = df_assessments.loc[
        (df_assessments["Country"].str.strip() == country.strip()) & 
        (df_assessments["Assessment date"].dt.year == assessment_year)
    ]

    if selected_data.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {country} in {assessment_year}")

    indicator_columns = [col for col in df_assessments.columns if col.startswith('indicator ')]
    metric_columns = [col for col in df_assessments.columns if col.startswith('metric ')]

    indicators = []

    for indicator_col in indicator_columns:
        indicator_name = indicator_col.replace("indicator ", "")
        row = selected_data[selected_data[indicator_col].notna()]

        if row.empty:
            continue  

        row = row.iloc[0]  
        metric_data = '' 

        for metric_col in metric_columns:
            metric_name = ".".join(metric_col.replace("metric ", "").split(".")[:3])
            
            if metric_name == indicator_name:
                metric_data = Metric(name=metric_name, value=str(row[metric_col]))  
                break  

        indicators.append(Indicator(
            name=indicator_name,
            assessment=str(row[indicator_col]),
            metric= metric_data if isinstance(metric_data, Metric) else ""
        ))

    return indicators


# this end point retrieves areas and their nested indicators and metrics 
@app.get("/v1/country-areas/{country}/{assessment_year}", response_model=List[Area])
async def get_country_areas(country: str, assessment_year: int):
    selected_data = df_assessments.loc[
        (df_assessments["Country"].str.strip() == country.strip()) & 
        (df_assessments["Assessment date"].dt.year == assessment_year)
    ]

    if selected_data.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {country} in {assessment_year}")

    area_columns = [col for col in df_assessments.columns if col.startswith('area ')]
    indicator_columns = [col for col in df_assessments.columns if col.startswith('indicator ')]
    metric_columns = [col for col in df_assessments.columns if col.startswith('metric ')]

    areas = []

    for area_col in area_columns:
        area_name = area_col.replace("area ", "")
        area_row = selected_data[selected_data[area_col].notna()]

        if area_row.empty:
            continue  
        
        area_row = area_row.iloc[0]  
        indicators = []

        for indicator_col in indicator_columns:
            indicator_name = indicator_col.replace("indicator ", "")

            if indicator_name.split('.')[:2] != area_name.split('.'):
                continue  

            indicator_row = selected_data[selected_data[indicator_col].notna()]
            if indicator_row.empty:
                continue  

            indicator_row = indicator_row.iloc[0]  
            metric_data = ''  
            for metric_col in metric_columns:
                metric_name = ".".join(metric_col.replace("metric ", "").split(".")[:3])
                
                if metric_name == indicator_name:
                    metric_data = Metric(name=metric_name, value=str(indicator_row[metric_col]))  
                    break  

            indicators.append(Indicator(
                name=indicator_name,
                assessment=str(indicator_row[indicator_col]),
                metric= metric_data if isinstance(metric_data, Metric) else ""  
            ))

        areas.append(Area(
            name=area_name,
            assessment=str(area_row[area_col]),
            indicators=indicators
        ))

    return areas



# pillar end point

# what is the best way to then embed pillars in dictionary
@app.get("/v1/country-pillars/{country}/{assessment_year}", response_model=List[Pillar])
async def get_country_pillars(country: str, assessment_year: int):
    selected_data = df_assessments.loc[
        (df_assessments["Country"].str.strip() == country.strip()) & 
        (df_assessments["Assessment date"].dt.year == assessment_year)
    ]

    if selected_data.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {country} in {assessment_year}")

    area_columns = [col for col in df_assessments.columns if col.startswith('area ')]
    indicator_columns = [col for col in df_assessments.columns if col.startswith('indicator ')]
    metric_columns = [col for col in df_assessments.columns if col.startswith('metric ')]

    pillar_names = sorted(set(area_col.replace("area ", "").split('.')[0] for area_col in area_columns))
    pillars = []

    for pillar_name in pillar_names:
        areas = []

        for area_col in area_columns:
            area_name = area_col.replace("area ", "")

            if not area_name.startswith(pillar_name):
                continue  

            area_row = selected_data[selected_data[area_col].notna()]
            if area_row.empty:
                continue  

            area_row = area_row.iloc[0]  
            indicators = []

            for indicator_col in indicator_columns:
                indicator_name = indicator_col.replace("indicator ", "")

                if not indicator_name.startswith(area_name):
                    continue  

                indicator_row = selected_data[selected_data[indicator_col].notna()]
                if indicator_row.empty:
                    continue  

                indicator_row = indicator_row.iloc[0]  
                metric_data = ''

                for metric_col in metric_columns:
                    metric_name = ".".join(metric_col.replace("metric ", "").split(".")[:3])

                    if metric_name == indicator_name:
                        metric_data = Metric(name=metric_name, value=str(indicator_row[metric_col]))  
                        break  

                
                indicator_dict = {
                    "name": indicator_name,
                    "assessment": str(indicator_row[indicator_col]),
                    "metric": metric_data if isinstance(metric_data, Metric) else ""
                }
                indicators.append(Indicator(**indicator_dict)) 

            
            area_dict = {
                "name": area_name,
                "assessment": str(area_row[area_col]),
                "indicators": indicators
            }
            areas.append(Area(**area_dict))  

       
        pillar_dict = {
            "name": pillar_name,
            "areas": areas
        }
        if areas:
            pillars.append(Pillar(**pillar_dict)) 

    return pillars
