from .base_pipeline import BasePipeline
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path
from utils.file_discovery import find_latest_directory, find_files_by_pattern
from typing import Dict

class ASCORPipeline(BasePipeline):
    """Pipeline for ASCOR database operations."""
    
    def __init__(self, data_dir: str, logger: logging.Logger):
        """Initialize ASCOR pipeline.
        
        Args:
            data_dir (str): Path to the data directory
            logger (logging.Logger): Logger instance to use
        """
        super().__init__('ascor_api', data_dir, logger)
        self.ascor_data_dir = self._find_latest_ascor_data_dir()

    def _find_latest_ascor_data_dir(self) -> str:
        """Find the latest ASCOR data directory based on date patterns."""
        data_path = Path(self.data_dir)
        selected_dir = find_latest_directory(data_path, 'ascor', self.logger)
        return str(selected_dir)

    def _find_ascor_files(self) -> dict:
        """Find ASCOR files dynamically."""
        data_path = Path(self.ascor_data_dir)
        
        # Define file patterns to look for
        file_patterns = {
            'countries': 'ASCOR_countries.*',
            'benchmarks': 'ASCOR_benchmarks.*',
            'indicators': 'ASCOR_indicators.*',
            'assessment_results': 'ASCOR_assessments_results.*',
            'assessment_trends': 'ASCOR_assessments_results_trends_pathways.*'
        }
        
        # Filter out the assessment_trends pattern from assessment_results
        # We need to be more specific to avoid conflicts
        file_patterns['assessment_results'] = 'ASCOR_assessments_results.xlsx'
        
        return find_files_by_pattern(data_path, file_patterns, self.logger)

    def _process_data(self):
        """Process ASCOR data from files into dataframes."""
        # Get all files dynamically
        files = self._find_ascor_files()
        
        # Country
        df_country = pd.read_excel(files['countries'])
        df_country.columns = df_country.columns.str.strip()
        country_df = df_country[[
            'Name',
            'Country ISO code',
            'Region',
            'World Bank lending group',
            'International Monetary Fund fiscal monitor category',
            'Type of Party to the United Nations Framework Convention on Climate Change'
        ]].copy()
        country_df.columns = [
            'country_name', 'iso', 'region',
            'bank_lending_group', 'imf_category', 'un_party_type'
        ]
        self.data['country'] = country_df

        # Store country data - it will be inserted via bulk_insert in populate_tables

        # Get list of valid country names for foreign key validation
        valid_countries = set(country_df['country_name'].str.strip())

        # Benchmarks
        df_bench = pd.read_excel(files['benchmarks'])
        df_bench.columns = df_bench.columns.str.strip().str.lower().str.replace(' ', '_')
        benchmarks_df = df_bench[[
            'id', 'publication_date', 'emissions_metric', 'emissions_boundary',
            'units', 'benchmark_type', 'country'
        ]].copy()
        benchmarks_df.columns = [
            'benchmark_id', 'publication_date', 'emissions_metric', 'emissions_boundary',
            'units', 'benchmark_type', 'country_name'
        ]

        # Filter out records with invalid country names
        invalid_countries = benchmarks_df[~benchmarks_df['country_name'].str.strip().isin(valid_countries)]
        if not invalid_countries.empty:
            self.logger.warning("Found benchmarks with invalid country names:")
            for country in invalid_countries['country_name'].unique():
                self.logger.warning(f"- {country}")
        benchmarks_df = benchmarks_df[benchmarks_df['country_name'].str.strip().isin(valid_countries)]

        value_columns = [col for col in df_bench.columns if col.isdigit()]
        benchmark_values_df = df_bench[['id'] + value_columns].melt(
            id_vars='id', var_name='year', value_name='value'
        ).dropna()
        benchmark_values_df.columns = ['benchmark_id', 'year', 'value']
        benchmark_values_df['year'] = benchmark_values_df['year'].astype(int)

        # Only keep benchmark values for valid benchmarks
        benchmark_values_df = benchmark_values_df[benchmark_values_df['benchmark_id'].isin(benchmarks_df['benchmark_id'])]

        self.data['benchmarks'] = benchmarks_df
        self.data['benchmark_values'] = benchmark_values_df

        # Assessment Elements
        df_elements = pd.read_excel(files['indicators'])
        df_elements.columns = df_elements.columns.str.strip().str.lower().str.replace(' ', '_')
        assessment_elements_df = df_elements[[
            'code', 'text', 'units_or_response_type', 'type'
        ]].copy()
        assessment_elements_df.columns = ['code', 'text', 'response_type', 'type']
        assessment_elements_df['response_type'] = assessment_elements_df['response_type'].fillna('Not specified')
        self.data['assessment_elements'] = assessment_elements_df

        # Assessment Results
        df_results = pd.read_excel(files['assessment_results'])
        df_results.columns = df_results.columns.str.strip()
        
        # Columns that represent coded responses (non-pillar only)
        response_cols = [col for col in df_results.columns if (
            col.startswith("indicator ") or
            col.startswith("metric ") or
            col.startswith("area ")
        )]
        
        # Prepare a list for parsed results
        rows = []
        
        for _, row in df_results.iterrows():
            assessment_id = row["Id"]
            country_name = row["Country"].strip()
            
            # Skip if country is not valid
            if country_name not in valid_countries:
                self.logger.warning(f"Skipping assessment results for invalid country: {country_name}")
                continue
                
            assessment_date = pd.to_datetime(row["Assessment date"], dayfirst=True).date()
            publication_date = pd.to_datetime(row["Publication date"], dayfirst=True).date()
            
            for col in response_cols:
                code = col.split(" ", 1)[1]  # Extract e.g., "EP.1.a"
                response = row[col] if pd.notna(row[col]) else None
                original_col = col  # e.g., 'indicator EP.1.a'
                
                # Look for optional year and source columns
                year_col = f"year {original_col}"
                year = str(int(row[year_col])) if year_col in df_results.columns and pd.notna(row[year_col]) else None
                
                source_col = f"source {original_col}"
                source = row[source_col] if source_col in df_results.columns and pd.notna(row[source_col]) else None
                
                rows.append({
                    "assessment_id": assessment_id,
                    "response": response,
                    "assessment_date": assessment_date,
                    "publication_date": publication_date,
                    "source": source,
                    "year": year,
                    "code": code,
                    "country_name": country_name
                })
        
        # Convert to DataFrame
        assessment_results_df = pd.DataFrame(rows)
        self.data['assessment_results'] = assessment_results_df

        # Assessment Trends
        df_trends = pd.read_excel(files['assessment_trends'])
        df_trends.columns = df_trends.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Select and rename relevant columns
        assessment_trends_df = df_trends[[
            'id', 'country', 'emissions_metric', 'emissions_boundary',
            'units', 'assessment_date', 'publication_date', 'last_historical_year'
        ]].copy()
        
        assessment_trends_df.columns = [
            'trend_id', 'country_name', 'emissions_metric', 'emissions_boundary',
            'units', 'assessment_date', 'publication_date', 'last_historical_year'
        ]
        
        # Filter out records with invalid country names
        invalid_countries = assessment_trends_df[~assessment_trends_df['country_name'].str.strip().isin(valid_countries)]
        if not invalid_countries.empty:
            self.logger.warning("Found assessment trends with invalid country names:")
            for country in invalid_countries['country_name'].unique():
                self.logger.warning(f"- {country}")
        assessment_trends_df = assessment_trends_df[assessment_trends_df['country_name'].str.strip().isin(valid_countries)]
        
        # Convert date and year fields to appropriate types
        assessment_trends_df["assessment_date"] = pd.to_datetime(assessment_trends_df["assessment_date"], dayfirst=True).dt.date
        assessment_trends_df["publication_date"] = pd.to_datetime(assessment_trends_df["publication_date"], dayfirst=True).dt.date
        assessment_trends_df["last_historical_year"] = assessment_trends_df["last_historical_year"].astype("Int64")
        
        self.data['assessment_trends'] = assessment_trends_df
        
        # Value per year table
        # Identify year columns (2021 to 2030)
        year_cols = [col for col in df_trends.columns if col.isdigit() and 2021 <= int(col) <= 2030]
        
        # Reshape into long format
        value_per_year_df = df_trends[["id", "country"] + year_cols].melt(
            id_vars=["id", "country"],
            value_vars=year_cols,
            var_name="year",
            value_name="value"
        )
        
        # Rename to match database schema
        value_per_year_df.columns = ["trend_id", "country_name", "year", "value"]
        value_per_year_df["year"] = value_per_year_df["year"].astype(int)
        value_per_year_df["value"] = pd.to_numeric(value_per_year_df["value"], errors="coerce")
        
        # Filter out records with invalid country names
        value_per_year_df = value_per_year_df[value_per_year_df['country_name'].str.strip().isin(valid_countries)]
        
        # Drop rows with missing values
        value_per_year_df = value_per_year_df.dropna(subset=["value"])
        
        # Only keep values for valid trends
        value_per_year_df = value_per_year_df[value_per_year_df['trend_id'].isin(assessment_trends_df['trend_id'])]
        
        self.data['value_per_year'] = value_per_year_df

        # Trend values table
        # Extract relevant columns for trend_values
        trend_values_df = df_trends[[
            "id", "country", "year_metric_ep1.a.i", "metric_ep1.a.i"
        ]].copy()
        trend_values_df.columns = ["trend_id", "country_name", "year", "value"]
        trend_values_df["year"] = pd.to_numeric(trend_values_df["year"], errors="coerce").astype("Int64")
        trend_values_df["value"] = pd.to_numeric(trend_values_df["value"].replace("No data", pd.NA), errors="coerce")
        trend_values_df = trend_values_df.dropna(subset=["year", "value"])
        
        # Filter out records with invalid country names
        trend_values_df = trend_values_df[trend_values_df['country_name'].str.strip().isin(valid_countries)]
        
        # Only keep values for valid trends
        trend_values_df = trend_values_df[trend_values_df['trend_id'].isin(assessment_trends_df['trend_id'])]
        
        self.data['trend_values'] = trend_values_df

    def _validate_data(self) -> dict:
        """Validate ASCOR data."""
        return self.validator.validate_ascor_data(self.data)

    def _get_source_files(self) -> Dict[str, str]:
        """Get a mapping of table names to their source files.
        
        Returns:
            Dict[str, str]: Dictionary mapping table names to source file paths
        """
        source_files = {}
        files = self._find_ascor_files()
        
        # Map files to their corresponding tables
        source_files['country'] = str(files['countries'])
        source_files['benchmarks'] = str(files['benchmarks'])
        source_files['benchmark_values'] = str(files['benchmarks'])
        source_files['assessment_elements'] = str(files['indicators'])
        source_files['assessment_results'] = str(files['assessment_results'])
        source_files['assessment_trends'] = str(files['assessment_trends'])
        source_files['value_per_year'] = str(files['assessment_trends'])
        
        return source_files

 