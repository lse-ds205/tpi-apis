import os
import pandas as pd

from typing import List
from fastapi import FastAPI, HTTPException
from .models import Metric, Indicator, Area, Pillar, Metadata, ResponseData

df_assessments = pd.read_excel("./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx")
df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'])
df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'])

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}



@app.get("/v1/country-metrics/{country}/{assessment_year}", response_model=ResponseData)
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


    '''
    --------- Metrics
    '''
    # Select just the metrics
    metric_columns = [col for col in df_assessments.columns 
                        if col.startswith('metric')]
    metric_data = data[metric_columns]

    # JSON does not allow for NaN or NULL. 
    # The equivalent is just to leave an empty string instead
    metric_data = metric_data.fillna('')

    remap_area_column_names = {
        col: col.replace('metric ', '')
        for col in metric_columns
    }

    metric_data = metric_data.rename(columns=remap_area_column_names)

    metric_data_as_dict = metric_data.iloc[0].to_dict()

    list_metrics = []
    for name, value in metric_data_as_dict.items():
        individual_metric = Metric(name=name, value=value)
        list_metrics.append(individual_metric)
    # Grab just the first element (there should only be one anyway)
    # and return it as a dictionary

    '''
    --------- Indicators
    '''
    indicator_columns = [col for col in df_assessments.columns 
                        if col.startswith('indicator')]
    indicator_data = data[indicator_columns]

    indicator_data = indicator_data.fillna('')
    remap_area_column_names = {
        col: col.replace('indicator ', '')
        for col in indicator_columns
    }
    indicator_data = indicator_data.rename(columns=remap_area_column_names)
    indicator_data_as_dict = indicator_data.iloc[0].to_dict()
    list_indicators = []
    for indicator_name, indicator_value in indicator_data_as_dict.items():
        metrics = [metric for metric in list_metrics if indicator_name in metric.name]
        individual_indicator = Indicator(name = indicator_name, assessment=indicator_value, metrics = metrics)
        list_indicators.append(individual_indicator)

    '''
    ------ Areas
    '''
    area_columns = [col for col in df_assessments.columns 
                        if col.startswith('area')]
    area_data = data[area_columns]

    area_data = area_data.fillna('')
    remap_area_column_names = {
        col: col.replace('area ', '')
        for col in area_columns
    }
    area_data = indicator_data.rename(columns=remap_area_column_names)
    area_data_as_dict = area_data.iloc[0].to_dict()
    list_areas = []
    for area_name, area_value in area_data_as_dict.items():
        indicators = [indicator for indicator in list_indicators if area_name in indicator.name]
        individual_area = Area(name = area_name, assessment=area_value, indicators= indicators)
        list_areas.append(individual_area)

    '''
    ----- Pillars
    '''
    list_pillars = []
    for pillar in ["EP", "CP", "CF"]:
        areas = [area for area in list_areas if pillar in area.name]
        individual_pillar = Pillar(name=pillar, areas=areas)
        list_pillars.append(individual_pillar)

    metadata = Metadata(country=country, assessment_year=assessment_year)
    resp = ResponseData(metadata=metadata, pillars=list_pillars)
    return resp

