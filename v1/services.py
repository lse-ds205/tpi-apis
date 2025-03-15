"""
This file contains the service layer for the ASCOR API.

As taught in DS205 Week 02, the service layer handles business logic
between the route handlers and data access.

See: https://lse-dsi.github.io/DS205/2024-2025/winter-term/weeks/week02/slides.html#/key-concepts
"""

import pandas as pd

from .models import Metric, MetricSource, Indicator, IndicatorSource, Area, Pillar, CountryDataResponse

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

        # Copy the dataframe to avoid SettingWithCopyWarning
        filtered_df = self.df[mask].copy()
        
        if filtered_df.empty:
            raise ValueError("No data found for the specified country and year")

        # JSON does not allow for NaN or NULL. 
        # The equivalent is just to leave an empty string instead
        filtered_df = filtered_df.fillna('')
        
        return filtered_df.iloc[0]  # Return the first matching row
    
    def create_pillar(self, pillar: str) -> Pillar:  #We are returning a pillar
        areas = []
        pillar_areas = [col.replace("area ", "") for col in self.filtered_df.index 
                        if f" {pillar}." in col and col.startswith("area")]

        for area in pillar_areas:
            areas.append(self.create_area(area))
        
        return Pillar(name=pillar, areas=areas)

    def create_area(self, area_name: str) -> Area:

        # Get the assessment for the area
        area_assessment = self.filtered_df[f"area {area_name}"]

        # Start with an empty list of indicators
        indicators = []

        # Get the relevant columns for the indicators
        area_indicators = [col.replace("indicator ", "") for col in self.filtered_df.index 
                           if f" {area_name}." in col and col.startswith("indicator")]
                
        # Process each indicator
        for indicator in area_indicators:
            indicators.append(self.create_indicator(indicator))

        return Area(name=area_name, assessment=area_assessment, indicators=indicators)
    
    def create_indicator(self, indicator_name: str) -> Indicator:
        # Get the assessment for the indicator
        indicator_assessment = self.filtered_df[f"indicator {indicator_name}"]

        indicator_source = f"source indicator {indicator_name}"
        if indicator_source in self.filtered_df.index:
            indicator_source = IndicatorSource(source_name=self.filtered_df[indicator_source])
        else:
            indicator_source = None

        # Start with an empty list of metrics
        metrics = []

        # Get the relevant columns for the metrics
        indicator_metrics = [col.replace("year metric ", "") for col in self.filtered_df.index 
                             if f" {indicator_name}." in col and col.startswith("year metric")]
        
        # Process each metric
        for metric in indicator_metrics:
            metrics.append(self.create_metric(metric))

        return Indicator(name=indicator_name, assessment=indicator_assessment, metrics=metrics, source=indicator_source)

    def create_metric(self, metric_name: str) -> Metric:

        # Get the value of the metric
        metric_value = str(self.filtered_df[f"year metric {metric_name}"])

        # Get the source of the metric
        metric_source = f"source metric {metric_name}"
        if metric_source in self.filtered_df.index:
            metric_source = MetricSource(source_name=self.filtered_df[metric_source])
        else:
            metric_source = None

        return Metric(name=metric_name, value=metric_value, source=metric_source)

    def process_country_data(self) -> CountryDataResponse:
        pillars = [self.create_pillar(pillar) for pillar in ['EP', 'CP', 'CF']]
        output_dict =  CountryDataResponse(country=self.country, assessment_year=self.assessment_year, pillars=pillars) 
        return output_dict