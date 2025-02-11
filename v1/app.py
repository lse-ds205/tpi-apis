import os
import pandas as pd

from fastapi import FastAPI
from .models import CountryData, Metrics, Indicators, Area, Pillars


df_assessments = pd.read_excel("./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx")
df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'])
df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'])

def __is_running_on_nuvolos():

    hostname = os.getenv("HOSTNAME")
    return hostname is not None and hostname.startswith('nv-')

if __is_running_on_nuvolos():
    app = FastAPI(root_path="/proxy/8000/")
else:
    app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/v1/country-data/{country}/{assessment_year}", response_model=CountryData)
async def get_country_data(country: str, assessment_year: int):

    #### filter data to match country-year request####

    selected_row = (
        (df_assessments["Country"] == country) &
        (df_assessments['Assessment date'].dt.year == assessment_year)
    )

    data = df_assessments[selected_row]

    data = data.fillna('')          #replace NAs as not valid in Json

    remap_column_names = {          #remove . in column names
        col: col.replace('.', '_')
        for col in data.columns
    }
    data.rename(columns = remap_column_names, inplace=True)


    #### functions to create different objects from dataset ####

    def get_area(pillar, data):
        pillar_name = pillar
        area_columns = [
            col for col in data.columns if pillar_name and 'area' in col
            ]

        for area in area_columns:
            area_list = []
            area_name = area[-4:]          #extracts just the part of column name describing area
            assesment = data[area]
            indicator = get_indicator(area, data)
            individual_area = Area(
                  name = area_name, assessment = assesment, indicators = indicator
                  )
            area_list.append(individual_area)
        
        return area_list

    def get_indicator(area, data):
        area_name = area 
        indicator_columns = [
            col for col in data.columns if area_name and 'indicator' in col
            ]

        for indicator in indicator_columns:
            indicator_list = []
            indicator_name = indicator[-6:]
            assesment = data[indicator]
            metrics = get_metric(indicator, data)
            individual_indicator = Indicators(
                  name = indicator_name, assessment = assesment, metrics = metrics
                                              )
            indicator_list.append(individual_indicator)

        return indicator_list
            
    def get_metric(indicator, data):
        indicator_name = indicator 
        metric_columns = [
            col for col in data.columns if indicator_name and 'metric' in col
            ]

        for metric in metric_columns:
            metric_list = []
            metric_name = metric[-8:]
            value = data[metric]
            individual_metric = Metrics(
                  name = metric_name, value = value
                                              )
            metric_list.append(individual_metric)
    
        return metric_list
    

    ### create pilar object and call functions to construct output dictionary ###

    pillar_names = ['EP', 'CP', 'CF']
   
    for pillar in pillar_names:
        pillars_list = []
        individual_pillar = Pillars(
            name = pillar, areas = get_area(pillar, data)
        )
        pillars_list.append(individual_pillar)

    output_dict = CountryData(
        country = country,
        assessment_year = assessment_year,
        pillars = pillars_list,
    )
    
    return output_dict 