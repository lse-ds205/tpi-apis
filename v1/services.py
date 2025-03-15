"""
This file contains the service layer for the ASCOR API.

As taught in DS205 Week 02, the service layer handles business logic
between the route handlers and data access.

See: https://lse-dsi.github.io/DS205/2024-2025/winter-term/weeks/week02/slides.html#/key-concepts
"""

import pandas as pd

from typing import Dict
from fastapi import HTTPException

from .models import Metric, Indicator, Area, Pillar, CountryDataResponse

class CountryDataProcessor:
    def __init__(self, df: pd.DataFrame, country: str, assessment_year: int):
        self.df = df
        self.country = country.lower()  # Converts the country name to lowercase
        self.assessment_year = assessment_year
        self.filtered_df = self.filter_data()  # Filters the DataFrame 
        
    def filter_data(self) -> pd.DataFrame:  # We are returning a dataframe
        self.df['Assessment date'] = pd.to_datetime(self.df['Assessment date'], errors='coerce')
        mask = (
            (self.df['Country'].str.lower() == self.country) & 
            (self.df['Assessment date'].dt.year == self.assessment_year)
        )
        filtered_df = self.df[mask]
        
        if filtered_df.empty:
            raise HTTPException(status_code=404, detail="Data not found")
        
        return filtered_df.iloc[0]  # Return the first matching row
    
    def process_column(self, col: str, pillar: str, area_dict: Dict[str, Dict]): 
        #This is the key function that processes the DataFrame

        # Split the column name by space
        parts = col.split() 

        # Note that this only applies to column names with at least 2 parts
        if len(parts) < 2:
            return
        
        # Realize that in the dataframe, the first word is the area/indicator/metric, second word tells me further information
        col_type, col_path = parts[0], parts[1]
        path_parts = col_path.split('.')

        #Exit if there are less than 2 words in the column -- dont apply to other columns such as "ID" or "Country"
        if len(path_parts) < 2: 
            return
        
        area_num = path_parts[1]
        area_key = f"{pillar}.{area_num}"
        
        if area_key not in area_dict:
            area_dict[area_key] = {
                'assessment': str(self.filtered_df.get(f"area {pillar}.{area_num}", "")),
                'indicators': {}
            }
        
        #If the column type is an indicator AND it has the form a.b.c
        if len(path_parts) >= 3 and col_type == 'indicator': 
            indicator_num = path_parts[2]
            indicator_key = f"{area_key}.{indicator_num}"
            area_dict[area_key]['indicators'][indicator_key] = {
                'assessment': str(self.filtered_df[col]),
                'metrics': []
            }
        
        elif len(path_parts) >= 4 and col_type == 'metric':
            indicator_num = path_parts[2]
            metric_num = path_parts[3]
            indicator_key = f"{area_key}.{indicator_num}"
            if indicator_key in area_dict[area_key]['indicators']:
                metric = Metric(name=f"{indicator_key}.{metric_num}", value=str(self.filtered_df[col]))
                area_dict[area_key]['indicators'][indicator_key]['metrics'].append(metric)

    def process_pillar(self, pillar: str) -> Pillar:  #We are returning a pillar
        areas = []
        area_dict: Dict[str, Dict] = {}
        pillar_cols = [col for col in self.filtered_df.index if f" {pillar}." in col]
        
        for col in pillar_cols:
            self.process_column(col, pillar, area_dict)
        
        for area_name, area_data in area_dict.items():
            areas.append(self.create_area(area_name, area_data))
        
        return Pillar(name=pillar, areas=areas)

    def create_area(self, area_name: str, area_data: Dict) -> Area:
        indicators = []
        for ind_name, ind_data in area_data['indicators'].items():
            metrics = ind_data['metrics'] if ind_data['metrics'] else []
            indicators.append(Indicator(name=ind_name, assessment=ind_data['assessment'], metrics=metrics))
        
        return Area(name=area_name, assessment=area_data['assessment'], indicators=indicators)
    
    def process_country_data(self) -> CountryDataResponse:
        pillars = [self.process_pillar(pillar) for pillar in ['EP', 'CP', 'CF']]
        return CountryDataResponse(country=self.country, assessment_year=self.assessment_year, pillars=pillars) 