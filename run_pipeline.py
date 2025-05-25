import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import TpiBase, AscorBase
from utils.database_creation_utils import get_engine
from data_validation import DataValidator
import re
from typing import Dict, List, Optional
from datetime import datetime
import sys

# Set up logging with a more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants and config
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
ASCOR_DATA_DIR = os.path.join(DATA_DIR, 'TPI_ASCOR_data_13012025')
TPI_DATA_DIR = os.path.join(DATA_DIR, 'TPI_sector_data_All_sectors_08032025')

# Debug mode - set to True for verbose logging
DEBUG = False

def debug_log(msg: str) -> None:
    """Helper function for debug logging."""
    if DEBUG:
        logger.debug(msg)

def drop_tables():
    """Drop all tables in both databases."""
    try:
        # Drop TPI tables
        logger.info("Dropping TPI database tables...")
        tpi_engine = get_engine('tpi_api')
        
        # Check if tables exist before dropping
        with tpi_engine.connect() as conn:
            tables = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).fetchall()
            
            if not tables:
                logger.info("No TPI tables found to drop.")
            else:
                TpiBase.metadata.drop_all(tpi_engine)
                logger.info(f"Successfully dropped {len(tables)} TPI tables.")

        # Drop ASCOR tables
        logger.info("Dropping ASCOR database tables...")
        ascor_engine = get_engine('ascor_api')
        
        with ascor_engine.connect() as conn:
            tables = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).fetchall()
            
            if not tables:
                logger.info("No ASCOR tables found to drop.")
            else:
                AscorBase.metadata.drop_all(ascor_engine)
                logger.info(f"Successfully dropped {len(tables)} ASCOR tables.")

    except Exception as e:
        logger.error(f"Failed to drop tables: {str(e)}")
        # Add some context to the error
        if "connection" in str(e).lower():
            logger.error("Database connection failed. Please check your database settings.")
        elif "permission" in str(e).lower():
            logger.error("Permission denied. Please check your database user permissions.")
        raise

def create_tables():
    """Create all database tables."""
    try:
        # Ensure public schema exists and is set as search path for TPI
        tpi_engine = get_engine('tpi_api')
        with tpi_engine.connect() as conn:
            # Create schema if it doesn't exist
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS public;"))
            
            # Set search path
            conn.execute(text("SET search_path TO public;"))
            
            # Check if tables already exist
            existing_tables = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).fetchall()
            
            if existing_tables:
                logger.warning(f"Found {len(existing_tables)} existing tables in TPI database.")
                if not DEBUG:
                    raise ValueError("Tables already exist. Use drop_tables() first or set DEBUG=True to override.")
            
            conn.commit()
        logger.info("TPI: public schema ensured and search path set.")

        # Ensure public schema exists and is set as search path for ASCOR
        ascor_engine = get_engine('ascor_api')
        with ascor_engine.connect() as conn:
            # Create schema if it doesn't exist
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS public;"))
            
            # Set search path
            conn.execute(text("SET search_path TO public;"))
            
            # Check if tables already exist
            existing_tables = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).fetchall()
            
            if existing_tables:
                logger.warning(f"Found {len(existing_tables)} existing tables in ASCOR database.")
                if not DEBUG:
                    raise ValueError("Tables already exist. Use drop_tables() first or set DEBUG=True to override.")
            
            conn.commit()
        logger.info("ASCOR: public schema ensured and search path set.")

        # Create TPI tables explicitly
        with tpi_engine.connect() as conn:
            # Split the table creation into smaller chunks for better error handling
            tables = [
                # Company table
                """
                CREATE TABLE IF NOT EXISTS company (
                    company_name VARCHAR NOT NULL,
                    version VARCHAR NOT NULL,
                    geography VARCHAR,
                    isin VARCHAR,
                    ca100_focus VARCHAR,
                    size_classification VARCHAR,
                    geography_code VARCHAR,
                    sedol VARCHAR,
                    sector_name VARCHAR,
                    PRIMARY KEY (company_name, version)
                );
                """,
                # Company answer table
                """
                CREATE TABLE IF NOT EXISTS company_answer (
                    question_code VARCHAR NOT NULL,
                    company_name VARCHAR NOT NULL,
                    version VARCHAR NOT NULL,
                    question_text VARCHAR,
                    response VARCHAR,
                    PRIMARY KEY (question_code, company_name, version),
                    FOREIGN KEY (company_name, version) REFERENCES company(company_name, version)
                );
                """,
                # MQ assessment table
                """
                CREATE TABLE IF NOT EXISTS mq_assessment (
                    assessment_date DATE NOT NULL,
                    company_name VARCHAR NOT NULL,
                    version VARCHAR NOT NULL,
                    tpi_cycle INTEGER NOT NULL,
                    publication_date DATE,
                    level VARCHAR,
                    performance_change VARCHAR,
                    PRIMARY KEY (assessment_date, company_name, version, tpi_cycle),
                    FOREIGN KEY (company_name, version) REFERENCES company(company_name, version)
                );
                """,
                # CP assessment table
                """
                CREATE TABLE IF NOT EXISTS cp_assessment (
                    assessment_date DATE NOT NULL,
                    company_name VARCHAR NOT NULL,
                    version VARCHAR NOT NULL,
                    is_regional VARCHAR NOT NULL,
                    publication_date DATE,
                    assumptions VARCHAR,
                    cp_unit VARCHAR,
                    projection_cutoff DATE,
                    benchmark_id VARCHAR,
                    PRIMARY KEY (assessment_date, company_name, version, is_regional),
                    FOREIGN KEY (company_name, version) REFERENCES company(company_name, version)
                );
                """,
                # CP projection table
                """
                CREATE TABLE IF NOT EXISTS cp_projection (
                    cp_projection_year INTEGER NOT NULL,
                    cp_projection_value INTEGER,
                    assessment_date DATE NOT NULL,
                    company_name VARCHAR NOT NULL,
                    version VARCHAR NOT NULL,
                    is_regional VARCHAR NOT NULL,
                    PRIMARY KEY (cp_projection_year, assessment_date, company_name, version, is_regional),
                    FOREIGN KEY (assessment_date, company_name, version, is_regional) 
                        REFERENCES cp_assessment(assessment_date, company_name, version, is_regional)
                );
                """,
                # CP alignment table
                """
                CREATE TABLE IF NOT EXISTS cp_alignment (
                    cp_alignment_year INTEGER NOT NULL,
                    cp_alignment_value VARCHAR,
                    assessment_date DATE NOT NULL,
                    company_name VARCHAR NOT NULL,
                    version VARCHAR NOT NULL,
                    is_regional VARCHAR NOT NULL,
                    PRIMARY KEY (cp_alignment_year, assessment_date, company_name, version, is_regional),
                    FOREIGN KEY (assessment_date, company_name, version, is_regional) 
                        REFERENCES cp_assessment(assessment_date, company_name, version, is_regional)
                );
                """,
                # Sector benchmark table
                """
                CREATE TABLE IF NOT EXISTS sector_benchmark (
                    benchmark_id VARCHAR NOT NULL,
                    sector_name VARCHAR NOT NULL,
                    scenario_name VARCHAR NOT NULL,
                    region VARCHAR,
                    release_date DATE,
                    unit VARCHAR,
                    PRIMARY KEY (benchmark_id, sector_name, scenario_name)
                );
                """,
                # Benchmark projection table
                """
                CREATE TABLE IF NOT EXISTS benchmark_projection (
                    benchmark_projection_year INTEGER NOT NULL,
                    benchmark_projection_attribute FLOAT,
                    benchmark_id VARCHAR NOT NULL,
                    sector_name VARCHAR NOT NULL,
                    scenario_name VARCHAR NOT NULL,
                    PRIMARY KEY (benchmark_projection_year, benchmark_id, sector_name, scenario_name),
                    FOREIGN KEY (benchmark_id, sector_name, scenario_name) 
                        REFERENCES sector_benchmark(benchmark_id, sector_name, scenario_name)
                );
                """
            ]
            
            # Create tables one by one for better error handling
            for i, table_sql in enumerate(tables, 1):
                try:
                    conn.execute(text(table_sql))
                    debug_log(f"Created TPI table {i}/{len(tables)}")
                except Exception as e:
                    logger.error(f"Failed to create TPI table {i}: {str(e)}")
                    raise
            
            conn.commit()
        logger.info("TPI tables created successfully.")

        # Create ASCOR tables explicitly
        with ascor_engine.connect() as conn:
            # Split the table creation into smaller chunks for better error handling
            tables = [
                # Country table
                """
                CREATE TABLE IF NOT EXISTS country (
                    country_name VARCHAR NOT NULL,
                    iso VARCHAR,
                    region VARCHAR,
                    bank_lending_group VARCHAR,
                    imf_category VARCHAR,
                    un_party_type VARCHAR,
                    PRIMARY KEY (country_name)
                );
                """,
                # Assessment elements table
                """
                CREATE TABLE IF NOT EXISTS assessment_elements (
                    code VARCHAR NOT NULL,
                    text VARCHAR NOT NULL,
                    response_type VARCHAR NOT NULL,
                    type VARCHAR NOT NULL,
                    PRIMARY KEY (code)
                );
                """,
                # Assessment results table
                """
                CREATE TABLE IF NOT EXISTS assessment_results (
                    assessment_id INTEGER NOT NULL,
                    code VARCHAR NOT NULL,
                    response VARCHAR,
                    assessment_date DATE NOT NULL,
                    publication_date DATE,
                    source VARCHAR,
                    year INTEGER,
                    country_name VARCHAR NOT NULL,
                    PRIMARY KEY (assessment_id, code),
                    FOREIGN KEY (code) REFERENCES assessment_elements(code),
                    FOREIGN KEY (country_name) REFERENCES country(country_name)
                );
                """,
                # Assessment trends table
                """
                CREATE TABLE IF NOT EXISTS assessment_trends (
                    trend_id INTEGER NOT NULL,
                    country_name VARCHAR NOT NULL,
                    emissions_metric VARCHAR,
                    emissions_boundary VARCHAR,
                    units VARCHAR,
                    assessment_date DATE,
                    publication_date DATE,
                    last_historical_year INTEGER,
                    PRIMARY KEY (trend_id, country_name),
                    FOREIGN KEY (country_name) REFERENCES country(country_name)
                );
                """,
                # Trend values table
                """
                CREATE TABLE IF NOT EXISTS trend_values (
                    trend_id INTEGER NOT NULL,
                    country_name VARCHAR NOT NULL,
                    year INTEGER NOT NULL,
                    value FLOAT NOT NULL,
                    PRIMARY KEY (trend_id, country_name, year),
                    FOREIGN KEY (trend_id, country_name) REFERENCES assessment_trends(trend_id, country_name)
                );
                """,
                # Value per year table
                """
                CREATE TABLE IF NOT EXISTS value_per_year (
                    year INTEGER NOT NULL,
                    value FLOAT NOT NULL,
                    trend_id INTEGER NOT NULL,
                    country_name VARCHAR NOT NULL,
                    FOREIGN KEY (trend_id, country_name) REFERENCES assessment_trends(trend_id, country_name)
                );
                """,
                # Benchmarks table
                """
                CREATE TABLE IF NOT EXISTS benchmarks (
                    benchmark_id INTEGER NOT NULL,
                    publication_date DATE,
                    emissions_metric VARCHAR,
                    emissions_boundary VARCHAR,
                    units VARCHAR,
                    benchmark_type VARCHAR,
                    country_name VARCHAR,
                    PRIMARY KEY (benchmark_id),
                    FOREIGN KEY (country_name) REFERENCES country(country_name)
                );
                """,
                # Benchmark values table
                """
                CREATE TABLE IF NOT EXISTS benchmark_values (
                    year INTEGER NOT NULL,
                    benchmark_id INTEGER NOT NULL,
                    value FLOAT NOT NULL,
                    PRIMARY KEY (year, benchmark_id),
                    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(benchmark_id)
                );
                """
            ]
            
            # Create tables one by one for better error handling
            for i, table_sql in enumerate(tables, 1):
                try:
                    conn.execute(text(table_sql))
                    debug_log(f"Created ASCOR table {i}/{len(tables)}")
                except Exception as e:
                    logger.error(f"Failed to create ASCOR table {i}: {str(e)}")
                    raise
            
            conn.commit()
        logger.info("ASCOR tables created successfully.")

    except Exception as e:
        logger.error(f"Failed to create tables: {str(e)}")
        # Add some context to the error
        if "connection" in str(e).lower():
            logger.error("Database connection failed. Please check your database settings.")
        elif "permission" in str(e).lower():
            logger.error("Permission denied. Please check your database user permissions.")
        elif "already exists" in str(e).lower():
            logger.error("Some tables already exist. Use drop_tables() first or set DEBUG=True to override.")
        raise

def populate_tpi():
    """Populate TPI database with data."""
    try:
        engine = get_engine('tpi_api')
        logger.info('Populating TPI tables...')
        
        # Initialize data validator
        validator = DataValidator()
        
        # Dictionary to store all dataframes for validation
        tpi_data = {}

        # Company
        # Define paths to company files
        file_5 = os.path.join(TPI_DATA_DIR, 'Company_Latest_Assessments_5.0.csv')
        file_4 = os.path.join(TPI_DATA_DIR, 'Company_Latest_Assessments.csv')

        # Load both files
        df_5 = pd.read_csv(file_5)
        df_4 = pd.read_csv(file_4)

        # Map metadata columns
        meta_cols_common = {
            'Company Name': 'company_name',
            'Geography': 'geography',
            'ISINs': 'isin',
            'CA100 Focus Company': 'ca100_focus',
            'Large/Medium Classification': 'size_classification',
            'Geography Code': 'geography_code',
            'SEDOL': 'sedol',
            'Sector': 'sector_name'
        }

        # Process version 5.0 data
        df_5_meta = df_5[list(meta_cols_common.keys())].copy()
        df_5_meta.columns = list(meta_cols_common.values())
        df_5_meta['version'] = '5.0'

        # Process version 4.0 data
        df_4_meta = df_4[list(meta_cols_common.keys())].copy()
        df_4_meta.columns = list(meta_cols_common.values())
        df_4_meta['version'] = '4.0'

        # Get all companies from MQ Assessment files
        mq_files = [
            'MQ_Assessments_Methodology_1_08032025.csv',
            'MQ_Assessments_Methodology_2_08032025.csv',
            'MQ_Assessments_Methodology_3_08032025.csv',
            'MQ_Assessments_Methodology_4_08032025.csv',
            'MQ_Assessments_Methodology_5_08032025.csv'
        ]

        mq_companies = []
        for mq_file in mq_files:
            methodology_version = mq_file.split('_')[3]
            version = f"{methodology_version}.0"
            
            df_mq = pd.read_csv(os.path.join(TPI_DATA_DIR, mq_file))
            df_mq.columns = df_mq.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Get unique companies from this file
            companies = df_mq['company_name'].unique()
            for company in companies:
                mq_companies.append({
                    'company_name': company.strip(),
                    'version': version,
                    'geography': None,
                    'isin': None,
                    'ca100_focus': None,
                    'size_classification': None,
                    'geography_code': None,
                    'sedol': None,
                    'sector_name': None
                })

        # Convert MQ companies to DataFrame
        df_mq_meta = pd.DataFrame(mq_companies)

        # Combine all company data
        all_companies = pd.concat([df_5_meta, df_4_meta, df_mq_meta], ignore_index=True)
        
        # Drop duplicates keeping the first occurrence (which will be from the latest assessments files)
        all_companies = all_companies.drop_duplicates(subset=['company_name', 'version'], keep='first')
        tpi_data['company'] = all_companies

        # Insert company data first since it's referenced by other tables
        all_companies.to_sql('company', engine, if_exists='append', index=False)
        logger.info('TPI: company table populated.')

        # Create a set of valid company-version combinations for foreign key validation
        valid_companies = set(zip(all_companies['company_name'].str.strip(), all_companies['version']))

        # Company Answers - using MQ Assessments files
        company_answers = []
        for mq_file in mq_files:
            # Extract methodology version from filename
            methodology_version = mq_file.split('_')[3]  # Gets the number after 'Methodology_'
            version = f"{methodology_version}.0"  # Convert to version format (e.g., "1.0")
            
            df_mq = pd.read_csv(os.path.join(TPI_DATA_DIR, mq_file))
            df_mq.columns = df_mq.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Extract questions and their codes
            questions = [col for col in df_mq.columns if col.startswith('q') and '|' in col]
            records = []
            for q in questions:
                code, text = q.split('|', 1)
                for _, row in df_mq.iterrows():
                    company_name = row['company_name'].strip()
                    # Skip if company-version combination is not valid
                    if (company_name, version) not in valid_companies:
                        logger.warning(f"Skipping company answer for invalid company-version combination: {company_name} (v{version})")
                        continue
                    records.append({
                        'question_code': code.strip(),
                        'question_text': text.strip(),
                        'response': row[q],
                        'company_name': company_name,
                        'version': version
                    })
            company_answers.append(pd.DataFrame(records))
        
        company_answer_df = pd.concat(company_answers, ignore_index=True)
        
        # Drop null responses (required for NOT NULL constraint)
        company_answer_df = company_answer_df.dropna(subset=['response'])
        
        # Keep only the last occurrence of each question-company-version combination
        company_answer_df = company_answer_df.drop_duplicates(
            subset=['question_code', 'company_name', 'version'],
            keep='last'
        )
        tpi_data['company_answer'] = company_answer_df

        # MQ Assessment
        mq_records = []
        for mq_file in mq_files:
            # Extract methodology version from filename
            methodology_version = mq_file.split('_')[3]  # Gets the number after 'Methodology_'
            tpi_cycle = int(methodology_version)  # Convert to integer for tpi_cycle
            version = f"{methodology_version}.0"
            
            df_mq = pd.read_csv(os.path.join(TPI_DATA_DIR, mq_file))
            df_mq.columns = df_mq.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Process the data
            df_mq['tpi_cycle'] = tpi_cycle
            df_mq['version'] = version
            df_mq['company_name'] = df_mq['company_name'].str.strip()
            
            # Filter out invalid company-version combinations
            invalid_companies = df_mq[~df_mq.apply(lambda x: (x['company_name'], x['version']) in valid_companies, axis=1)]
            if not invalid_companies.empty:
                logger.warning("Found MQ assessments with invalid company-version combinations:")
                for company in invalid_companies['company_name'].unique():
                    logger.warning(f"- {company} (v{version})")
            df_mq = df_mq[df_mq.apply(lambda x: (x['company_name'], x['version']) in valid_companies, axis=1)]
            
            df_mq['assessment_date'] = pd.to_datetime(df_mq['assessment_date'], dayfirst=True, errors='coerce')
            df_mq['publication_date'] = pd.to_datetime(df_mq['publication_date'], errors='coerce')
            df_mq['level'] = pd.to_numeric(df_mq['level'], errors='coerce')
            df_mq['performance_change'] = df_mq['performance_compared_to_previous_year'].astype(str)
            
            # Select and reorder columns to match table schema
            mq_records.append(df_mq[[
                'assessment_date', 'company_name', 'version', 'tpi_cycle',
                'publication_date', 'level', 'performance_change'
            ]])
        
        # Combine all records
        mq_df = pd.concat(mq_records, ignore_index=True)
        
        # Drop rows with missing assessment dates
        mq_df = mq_df.dropna(subset=['assessment_date'])
        
        # Convert dates to date objects
        mq_df['assessment_date'] = mq_df['assessment_date'].dt.date
        mq_df['publication_date'] = mq_df['publication_date'].dt.date
        tpi_data['mq_assessment'] = mq_df

        # CP Assessment
        cp_dir = TPI_DATA_DIR
        
        # Dynamically find CP files
        cp_files = {}
        for fname in os.listdir(cp_dir):
            if fname.startswith("CP_Assessments_Regional"):
                cp_files["1"] = os.path.join(cp_dir, fname)
            elif fname.startswith("CP_Assessments"):
                cp_files["0"] = os.path.join(cp_dir, fname)
        
        # Process and insert data
        assessment_records = []
        alignment_records = []
        projection_records = []
        
        for is_regional, path in cp_files.items():
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip()
            df["company_name"] = df["Company Name"].str.strip()
            
            # Filter out invalid company-version combinations
            invalid_companies = df[~df.apply(lambda x: (x["company_name"], "5.0") in valid_companies, axis=1)]
            if not invalid_companies.empty:
                logger.warning("Found CP assessments with invalid company-version combinations:")
                for company in invalid_companies["company_name"].unique():
                    logger.warning(f"- {company} (v5.0)")
            df = df[df.apply(lambda x: (x["company_name"], "5.0") in valid_companies, axis=1)]
            
            df["assessment_date"] = pd.to_datetime(df["Assessment Date"], dayfirst=True, errors='coerce')
            df["publication_date"] = pd.to_datetime(df["Publication Date"], errors='coerce')
            df["projection_cutoff"] = pd.to_datetime(df["History to Projection cutoff year"], errors='coerce')
            df["assumptions"] = df.get("Assumptions")
            df["cp_unit"] = df["CP Unit"]
            df["benchmark_id"] = df.get("Benchmark ID")
            df["is_regional"] = is_regional
            
            # Create assessment records
            assessment_df = df[[
                "company_name", "assessment_date", "publication_date",
                "assumptions", "cp_unit", "projection_cutoff", "benchmark_id", "is_regional"
            ]].copy()
            assessment_df["version"] = "5.0"
            assessment_df = assessment_df.dropna(subset=["assessment_date"])
            assessment_records.append(assessment_df)
            
            # Process alignment columns
            align_cols = [col for col in df.columns if col.startswith("Carbon Performance Alignment ")]
            for col in align_cols:
                year = int(col.split()[-1])
                temp = df[["company_name", "assessment_date"]].copy()
                temp["cp_alignment_year"] = year
                temp["cp_alignment_value"] = df[col]
                temp["is_regional"] = is_regional
                temp["version"] = "5.0"
                temp = temp.dropna(subset=["cp_alignment_value"])
                alignment_records.append(temp)
            
            # Process projection columns
            year_cols = [col for col in df.columns if re.fullmatch(r"\d{4}", col)]
            for col in year_cols:
                year = int(col)
                temp = df[["company_name", "assessment_date"]].copy()
                temp["cp_projection_year"] = year
                temp["cp_projection_value"] = df[col]
                temp["is_regional"] = is_regional
                temp["version"] = "5.0"
                temp = temp.dropna(subset=["cp_projection_value"])
                projection_records.append(temp)
        
        # Store CP data in tpi_data dictionary
        if assessment_records:
            tpi_data['cp_assessment'] = pd.concat(assessment_records)
        if alignment_records:
            tpi_data['cp_alignment'] = pd.concat(alignment_records)
        if projection_records:
            tpi_data['cp_projection'] = pd.concat(projection_records)

        # Sector Benchmark
        df_sector = pd.read_csv(os.path.join(TPI_DATA_DIR, 'Sector_Benchmarks_08032025.csv'))
        df_sector.columns = df_sector.columns.str.strip().str.lower().str.replace(' ', '_')
        sector_benchmark_df = df_sector[['benchmark_id', 'sector_name', 'scenario_name', 'region', 'release_date', 'unit']].copy()
        sector_benchmark_df['release_date'] = pd.to_datetime(sector_benchmark_df['release_date'], dayfirst=True)
        tpi_data['sector_benchmark'] = sector_benchmark_df
        
        # Prepare benchmark_projection
        value_columns = [col for col in df_sector.columns if col.isdigit()]
        benchmark_projection_df = df_sector[['benchmark_id', 'sector_name', 'scenario_name'] + value_columns].melt(
            id_vars=['benchmark_id', 'sector_name', 'scenario_name'],
            var_name='benchmark_projection_year',
            value_name='benchmark_projection_attribute'
        ).dropna()
        benchmark_projection_df['benchmark_projection_year'] = benchmark_projection_df['benchmark_projection_year'].astype(int)
        tpi_data['benchmark_projection'] = benchmark_projection_df

        # Validate TPI data before insertion
        validation_results = validator.validate_tpi_data(tpi_data)
        
        if validation_results['errors']:
            logger.error("Data validation failed with the following errors:")
            for error in validation_results['errors']:
                logger.error(f"- {error}")
            raise ValueError("Data validation failed. Please check the errors above.")
        
        if validation_results['warnings']:
            logger.warning("Data validation completed with warnings:")
            for warning in validation_results['warnings']:
                logger.warning(f"- {warning}")
        
        # If validation passes, proceed with database insertion
        for table_name, df in tpi_data.items():
            if table_name != 'company':  # Skip company table as it's already inserted
                df.to_sql(table_name, engine, if_exists='append', index=False)
                logger.info(f'TPI: {table_name} table populated.')

        logger.info('TPI database population completed successfully.')

    except Exception as e:
        logger.error(f"Failed to populate TPI database: {str(e)}")
        raise

def populate_ascor():
    """Populate ASCOR database with data."""
    try:
        engine = get_engine('ascor_api')
        logger.info('Populating ASCOR tables...')
        
        # Initialize data validator
        validator = DataValidator()
        
        # Dictionary to store all dataframes for validation
        ascor_data = {}

        # Country
        df_country = pd.read_excel(os.path.join(ASCOR_DATA_DIR, 'ASCOR_countries.xlsx'))
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
        ascor_data['country'] = country_df

        # Insert country data first since it's referenced by other tables
        country_df.to_sql('country', engine, if_exists='append', index=False)
        logger.info('ASCOR: country table populated.')

        # Get list of valid country names for foreign key validation
        valid_countries = set(country_df['country_name'].str.strip())

        # Benchmarks
        df_bench = pd.read_excel(os.path.join(ASCOR_DATA_DIR, 'ASCOR_benchmarks.xlsx'))
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
            logger.warning("Found benchmarks with invalid country names:")
            for country in invalid_countries['country_name'].unique():
                logger.warning(f"- {country}")
            benchmarks_df = benchmarks_df[benchmarks_df['country_name'].str.strip().isin(valid_countries)]

        value_columns = [col for col in df_bench.columns if col.isdigit()]
        benchmark_values_df = df_bench[['id'] + value_columns].melt(
            id_vars='id', var_name='year', value_name='value'
        ).dropna()
        benchmark_values_df.columns = ['benchmark_id', 'year', 'value']
        benchmark_values_df['year'] = benchmark_values_df['year'].astype(int)

        # Only keep benchmark values for valid benchmarks
        benchmark_values_df = benchmark_values_df[benchmark_values_df['benchmark_id'].isin(benchmarks_df['benchmark_id'])]

        ascor_data['benchmarks'] = benchmarks_df
        ascor_data['benchmark_values'] = benchmark_values_df

        # Assessment Elements
        df_elements = pd.read_excel(os.path.join(ASCOR_DATA_DIR, 'ASCOR_indicators.xlsx'))
        df_elements.columns = df_elements.columns.str.strip().str.lower().str.replace(' ', '_')
        assessment_elements_df = df_elements[[
            'code', 'text', 'units_or_response_type', 'type'
        ]].copy()
        assessment_elements_df.columns = ['code', 'text', 'response_type', 'type']
        assessment_elements_df['response_type'] = assessment_elements_df['response_type'].fillna('Not specified')
        ascor_data['assessment_elements'] = assessment_elements_df

        # Assessment Results
        df_results = pd.read_excel(os.path.join(ASCOR_DATA_DIR, 'ASCOR_assessments_results.xlsx'))
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
                logger.warning(f"Skipping assessment results for invalid country: {country_name}")
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
        ascor_data['assessment_results'] = assessment_results_df

        # Assessment Trends
        df_trends = pd.read_excel(os.path.join(ASCOR_DATA_DIR, 'ASCOR_assessments_results_trends_pathways.xlsx'))
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
            logger.warning("Found assessment trends with invalid country names:")
            for country in invalid_countries['country_name'].unique():
                logger.warning(f"- {country}")
            assessment_trends_df = assessment_trends_df[assessment_trends_df['country_name'].str.strip().isin(valid_countries)]
        
        # Convert date and year fields to appropriate types
        assessment_trends_df["assessment_date"] = pd.to_datetime(assessment_trends_df["assessment_date"], dayfirst=True).dt.date
        assessment_trends_df["publication_date"] = pd.to_datetime(assessment_trends_df["publication_date"], dayfirst=True).dt.date
        assessment_trends_df["last_historical_year"] = assessment_trends_df["last_historical_year"].astype("Int64")
        
        ascor_data['assessment_trends'] = assessment_trends_df
        
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
        
        ascor_data['value_per_year'] = value_per_year_df

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
        
        ascor_data['trend_values'] = trend_values_df

        # Validate ASCOR data before insertion
        validation_results = validator.validate_ascor_data(ascor_data)
        
        if validation_results['errors']:
            logger.error("Data validation failed with the following errors:")
            for error in validation_results['errors']:
                logger.error(f"- {error}")
            raise ValueError("Data validation failed. Please check the errors above.")
        
        if validation_results['warnings']:
            logger.warning("Data validation completed with warnings:")
            for warning in validation_results['warnings']:
                logger.warning(f"- {warning}")
        
        # If validation passes, proceed with database insertion
        for table_name, df in ascor_data.items():
            if table_name != 'country':  # Skip country table as it's already inserted
                df.to_sql(table_name, engine, if_exists='append', index=False)
                logger.info(f'ASCOR: {table_name} table populated.')

        logger.info('ASCOR database population completed successfully.')

    except Exception as e:
        logger.error(f"Failed to populate ASCOR database: {str(e)}")
        raise

def run_pipeline():
    """Run the complete data pipeline.
    
    This function orchestrates the entire data pipeline process:
    1. Drops existing tables (if any)
    2. Creates new tables with proper schemas
    3. Populates TPI database with company and assessment data
    4. Populates ASCOR database with country and assessment data
    
    The pipeline includes data validation at each step and provides
    detailed logging of the process.
    """
    start_time = datetime.now()
    logger.info(f"Starting pipeline at {start_time}")
    
    try:
        # Drop all tables
        logger.info("Step 1/4: Dropping existing tables...")
        drop_tables()
        
        # Create all tables
        logger.info("Step 2/4: Creating new tables...")
        create_tables()
        
        # Populate TPI database
        logger.info("Step 3/4: Populating TPI database...")
        populate_tpi()
        
        # Populate ASCOR database
        logger.info("Step 4/4: Populating ASCOR database...")
        populate_ascor()
        
        # Calculate and log execution time
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Pipeline completed successfully in {duration}")
        
        # Log some basic stats
        if DEBUG:
            _log_pipeline_stats()
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        # Add some context to the error
        if "connection" in str(e).lower():
            logger.error("Database connection failed. Please check your database settings.")
        elif "permission" in str(e).lower():
            logger.error("Permission denied. Please check your database user permissions.")
        elif "validation" in str(e).lower():
            logger.error("Data validation failed. Please check the data files and validation rules.")
        raise

def _log_pipeline_stats():
    """Log some basic statistics about the populated databases."""
    try:
        # TPI stats
        tpi_engine = get_engine('tpi_api')
        with tpi_engine.connect() as conn:
            company_count = conn.execute(text("SELECT COUNT(*) FROM company")).scalar()
            assessment_count = conn.execute(text("SELECT COUNT(*) FROM mq_assessment")).scalar()
            logger.debug(f"TPI Stats:")
            logger.debug(f"- Companies: {company_count}")
            logger.debug(f"- Assessments: {assessment_count}")
        
        # ASCOR stats
        ascor_engine = get_engine('ascor_api')
        with ascor_engine.connect() as conn:
            country_count = conn.execute(text("SELECT COUNT(*) FROM country")).scalar()
            result_count = conn.execute(text("SELECT COUNT(*) FROM assessment_results")).scalar()
            logger.debug(f"ASCOR Stats:")
            logger.debug(f"- Countries: {country_count}")
            logger.debug(f"- Assessment Results: {result_count}")
            
    except Exception as e:
        logger.warning(f"Failed to log pipeline stats: {str(e)}")

if __name__ == '__main__':
    try:
        run_pipeline()
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}")
        sys.exit(1) 