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
        # Bryan's version (to be reconciled)
        pillars = [self.process_pillar(pillar) for pillar in ['EP', 'CP', 'CF']]

        # data = df_assessments[selected_row]

        # if data.empty:
        #     raise HTTPException(status_code=404, detail="Data not found for the specified country and year")

        # # JSON does not allow for NaN or NULL. 
        # # The equivalent is just to leave an empty string instead
        # data = data.fillna('')

        # # Create areas, indicators, and metrics
        # def create_metrics(indicator_name):
        #     metrics = []
        #     for col in column_headings:
        #         if col.startswith(f"metric {indicator_name}."):
        #             metric_name = col
        #             metric_value = data.iloc[0][col]
        #             source_col = f"source {col}"
        #             metric_source = MetricSource(source_name=data.iloc[0][source_col]) if source_col in data else None
        #             if metric_value != '':
        #                 metrics.append(Metric(name=metric_name, value=metric_value, source=metric_source))
        #     return metrics

        # def create_indicators(area_name):
        #     indicators = []
        #     for col in column_headings:
        #         if col.startswith(f"indicator {area_name}."):
        #             indicator_name = col
        #             metrics = create_metrics(col.split(" ")[1])
        #             source_col = f"source {col}"
        #             indicator_source = IndicatorSource(source_name=data.iloc[0][source_col]) if source_col in data else None
        #             if metrics:  # Only add indicators with non-empty metrics
        #                 indicators.append(Indicator(name=indicator_name, metrics=metrics, source=indicator_source))
        #     return indicators

        # def create_areas():
        #     areas = []
        #     for col in column_headings:
        #         if col.startswith("area "):
        #             area_name = col.replace("area ", "")
        #             indicators = create_indicators(area_name)
        #             if indicators:  # Only add areas with non-empty indicators
        #                 areas.append(Area(name=area_name, indicators=indicators))
        #     return areas

        # areas = create_areas()

        output_dict =  CountryDataResponse(country=self.country, assessment_year=self.assessment_year, pillars=pillars) 
        return output_dict