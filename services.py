"""
This file contains the service layer for the ASCOR API.

As taught in DS205 Week 02, the service layer handles business logic
between the route handlers and data access.

See: https://lse-dsi.github.io/DS205/2024-2025/winter-term/weeks/week02/slides.html#/key-concepts
"""

import pandas as pd
from fastapi import APIRouter, HTTPException
from log_config import get_logger
from schemas import Metric, MetricSource, Indicator, IndicatorSource, Area, Pillar, CountryDataResponse

logger = get_logger(__name__)

class CountryDataProcessor:
    def __init__(self, df: pd.DataFrame, country_identifier: str, assessment_year: int):
        self.df = df
        self.country_identifier = str(country_identifier).strip().lower()
        self.assessment_year = assessment_year
        self.filtered_df = self.filter_data()
        
    def filter_data(self) -> pd.DataFrame:
        self.df['Publication date'] = pd.to_datetime(self.df['Publication date'], errors="coerce", dayfirst=True)
        self.df['Assessment date'] = pd.to_datetime(self.df['Assessment date'], errors="coerce", dayfirst=True)
        
        logger.debug(f"[FILTER] Filtering for: country={self.country_identifier}, assessment_year={self.assessment_year}")
        logger.debug(f"[FILTER] Unique countries: {self.df['Country'].unique()}")
        logger.debug(f"[FILTER] Unique years: {self.df['Assessment date'].dt.year.unique()}")
        
        # Try to match by ISIN (semicolon-separated, case-insensitive)
        if 'ISIN' in self.df.columns:
            mask_isin = self.df['ISIN'].astype(str).str.lower().str.split(';').apply(lambda x: self.country_identifier in [i.strip().lower() for i in x if i])
            filtered_df = self.df[mask_isin & (self.df['Assessment date'].dt.year == self.assessment_year)]
        else:
            filtered_df = pd.DataFrame()
        
        if filtered_df.empty:
            # Try to match by Country Id (as string)
            mask_id = self.df['Country Id'].astype(str).str.strip().str.lower() == self.country_identifier
            filtered_df = self.df[mask_id & (self.df['Assessment date'].dt.year == self.assessment_year)]
        
        if filtered_df.empty:
            # Fallback to Country name
            self.df['Country'] = self.df['Country'].astype(str).str.strip().str.lower()
            mask_name = self.df['Country'] == self.country_identifier
            filtered_df = self.df[mask_name & (self.df['Assessment date'].dt.year == self.assessment_year)]
        
        logger.debug(f"[FILTER] Rows matched: {len(filtered_df)}")
        
        if filtered_df.empty:
            logger.error(f"[FILTER] No match found for: {self.country_identifier=} {self.assessment_year=}")
            logger.error(f"[FILTER] Available country/year pairs:\n{self.df[['Country', 'Assessment date']].dropna().head(10)}")
            raise ValueError(f"No data found for country={self.country_identifier} in year={self.assessment_year}")
        
        filtered_df = filtered_df.fillna('')
        return filtered_df.iloc[0]
    
    def create_pillar(self, pillar: str) -> Pillar:
        areas = []
        pillar_areas = [col.replace("area ", "") for col in self.filtered_df.index 
                        if f" {pillar}." in col and col.startswith("area")]

        for area in pillar_areas:
            areas.append(self.create_area(area))
        
        return Pillar(name=pillar, areas=areas)

    def create_area(self, area_name: str) -> Area:
        area_assessment = self.filtered_df[f"area {area_name}"]

        indicators = []

        area_indicators = [col.replace("indicator ", "") for col in self.filtered_df.index 
                           if f" {area_name}." in col and col.startswith("indicator")]
                
        for indicator in area_indicators:
            indicators.append(self.create_indicator(indicator))

        return Area(name=area_name, assessment=area_assessment, indicators=indicators)
    
    def create_indicator(self, indicator_name: str) -> Indicator:
        indicator_assessment = self.filtered_df[f"indicator {indicator_name}"]

        indicator_source = f"source indicator {indicator_name}"
        if indicator_source in self.filtered_df.index:
            indicator_source = IndicatorSource(source_name=self.filtered_df[indicator_source])
        else:
            indicator_source = None

        metrics = []

        indicator_metrics = [col.replace("year metric ", "") for col in self.filtered_df.index 
                             if f" {indicator_name}." in col and col.startswith("year metric")]
        
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
        output_dict = CountryDataResponse(
            country=self.country_identifier, 
            assessment_year=self.assessment_year, 
            pillars=pillars
        )
        return output_dict


# --- Define Custom Exceptions (Optional but recommended) ---
class CompanyNotFoundError(Exception):
    """Custom exception for when company data cannot be found."""
    pass

class CompanyDataError(Exception):
    """Custom exception for errors during company data processing."""
    pass

def fetch_company_data(company_id: int) -> dict:
    """
    Fetches (simulated) company data by ID.

    Args:
        company_id: The ID of the company to fetch.

    Returns:
        A dictionary containing company data.

    Raises:
        CompanyNotFoundError: If the company data file is not found (simulated).
        CompanyDataError: If there's an error processing the data (simulated).
        Exception: For any other unexpected errors.
    """
    try:
        logger.info(f"Attempting to fetch data for company ID: {company_id}")
        # Simulate fetching company data which might fail
        if company_id == 999:  # Simulate a known processing error case
            raise ValueError("Simulated database error for company 999")
        if company_id < 0:
            # Simulate file not found more realistically
            raise FileNotFoundError(f"Simulated: Data file for company {company_id} not found.")

        # ... process data simulation ...
        company_data = {"id": company_id, "name": f"Company {company_id}"}
        logger.info(f"Successfully fetched data for company ID: {company_id}")
        return company_data

    except FileNotFoundError as e:
        # Log the specific error originating here
        logger.error(f"Data file not found for company ID {company_id}: {e}")
        raise CompanyNotFoundError(f"Company {company_id} data file not found.") from e
    except ValueError as e:
        # Log the specific error originating here
        logger.error(f"Data processing error for company ID {company_id}: {e}", exc_info=True)
        raise CompanyDataError("Internal error processing company data.") from e
    except Exception as e:
        logger.exception(f"Unexpected error fetching company ID {company_id}: {e}")
        raise
