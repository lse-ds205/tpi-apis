import pandas as pd
import logging
from pathlib import Path
import shutil
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
    Base,
    ASCORTrendsPathways,
    ASCORAssessments,
    ASCORBenchmarks,
    ASCORCountries,
    ASCORIndicators,
    Company,
    ManagementQualityAssessment,
    CarbonPerformanceAssessment,
    SectorBenchmarks
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup data directories
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
ASCOR_RAW_DIR = RAW_DATA_DIR / "TPI ASCOR data - 13012025"
SECTOR_RAW_DIR = RAW_DATA_DIR / "TPI sector data - All sectors - 08032025"
ASCOR_PROCESSED_DIR = PROCESSED_DATA_DIR / "TPI ASCOR data - 13012025"
SECTOR_PROCESSED_DIR = PROCESSED_DATA_DIR / "TPI sector data - All sectors - 08032025"

# Create processed directories
for directory in [ASCOR_PROCESSED_DIR, SECTOR_PROCESSED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

def move_to_processed(file_path: Path, is_ascor: bool = True) -> None:
    """Move a file from raw to processed directory after successful processing."""
    if not file_path.exists():
        logger.warning(f"File {file_path} does not exist")
        return
    
    # Determine target processed directory
    processed_dir = ASCOR_PROCESSED_DIR if is_ascor else SECTOR_PROCESSED_DIR
    processed_file = processed_dir / file_path.name
    
    # Add timestamp to processed file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    processed_file = processed_file.parent / f"{processed_file.stem}_{timestamp}{processed_file.suffix}"
    
    try:
        shutil.move(str(file_path), str(processed_file))
        logger.info(f"Moved {file_path} to {processed_file}")
    except Exception as e:
        logger.error(f"Error moving file {file_path}: {str(e)}")

def clean_nan_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean NaN values from a dictionary."""
    return {k: v for k, v in data.items() if pd.notna(v)}

def parse_date(date_str: str) -> datetime:
    """Parse a date string into a datetime object."""
    if pd.isna(date_str):
        return None
    try:
        return pd.to_datetime(date_str, format='%d/%m/%Y')
    except Exception:
        return None

# ASCOR Data Processing Functions
def process_trends_pathways_row(row: pd.Series) -> Dict[str, Any]:
    """Process a single row of trends and pathways data."""
    basic_info = {
        'country': row['Country'],
        'emissions_metric': row['Emissions metric'],
        'emissions_boundary': row['Emissions boundary'],
        'units': row['Units'],
        'assessment_date': parse_date(row['Assessment date']),
        'publication_date': parse_date(row['Publication date']),
        'last_historical_year': float(row['Last historical year']) if not pd.isna(row['Last historical year']) else None
    }
    
    trends_columns = [col for col in row.index if 'metric EP1.a' in col]
    trends_data = {col: row[col] for col in trends_columns}
    trends_data = clean_nan_values(trends_data)
    
    year_columns = [col for col in row.index if col.isdigit()]
    pathways_data = {col: row[col] for col in year_columns}
    pathways_data = clean_nan_values(pathways_data)
    
    return {**basic_info, 'trends_data': trends_data, 'pathways_data': pathways_data}

def process_assessments_row(row: pd.Series) -> Dict[str, Any]:
    """Process a single row of assessments data."""
    return {
        'country_id': int(row['Country Id']) if not pd.isna(row['Country Id']) else None,
        'country': row['Country'],
        'assessment_date': parse_date(row['Assessment date']),
        'publication_date': parse_date(row['Publication date']),
        'notes': row['Notes'] if not pd.isna(row['Notes']) else None
    }

def process_benchmarks_row(row: pd.Series) -> Dict[str, Any]:
    """Process a single row of benchmarks data."""
    if 'Sector name' in row.index:
        # This is a TPI Sector Benchmark
        return {
            'sector_name': str(row['Sector name']),
            'scenario_name': str(row['Scenario name']),
            'region': str(row['Region']),
            'release_date': parse_date(row['Release date']),
            'unit': str(row['Unit']),
        }
    elif 'Country' in row.index:
        # This is an ASCOR Country Benchmark
        return {
            'country': str(row['Country']),
            'publication_date': parse_date(row['Publication date']),
            'emissions_metric': str(row['Emissions metric']),
            'emissions_boundary': str(row['Emissions boundary']),
            'units': str(row['Units']),
            'benchmark_type': str(row['Benchmark type']),
        }
    else:
        logger.warning(f"Unknown benchmark format for row: {row}")
        return None

def process_countries_row(row: pd.Series) -> Dict[str, Any]:
    """Process a single row of countries data."""
    return {
        'country_id': int(row['Id']),
        'country': str(row['Name']),
        'region': str(row['Region']),
        'income_group': str(row['World Bank lending group'])
    }

def process_indicators_row(row: pd.Series) -> Dict[str, Any]:
    """Process a single row of indicators data."""
    return {
        'indicator_id': str(row['Id']),
        'indicator_name': str(row['Code']),
        'indicator_description': str(row['Text']),
        'indicator_category': str(row['Type']),
        'indicator_type': str(row['Units or response type']) if not pd.isna(row['Units or response type']) else 'N/A'
    }

# Sector Data Processing Functions
def process_company_row(row: pd.Series) -> Dict[str, Any]:
    """Process a single row of company data."""
    return {
        'company_id': str(row['Company Name']),
        'name': str(row['Company Name']),
        'sector': str(row['Sector']) if not pd.isna(row['Sector']) else None,
        'geography': str(row['Geography']) if not pd.isna(row['Geography']) else None,
        'latest_assessment_year': int(row['CP Assessment Date'].split('/')[-1]) if not pd.isna(row['CP Assessment Date']) else None
    }

def process_mq_assessment_row(row: pd.Series) -> Dict[str, Any]:
    """Process a single row of MQ assessment data."""
    # Handle non-numeric values in 'Level' column for management_quality_score
    level_value = row['Level']
    if pd.notna(level_value):
        if isinstance(level_value, str) and 'STAR' in level_value:
            level_value = float(level_value.replace('STAR', '').strip())
        else:
            try:
                level_value = float(level_value)
            except ValueError:
                logger.warning(f"Could not convert MQ Level '{level_value}' to float for company {row.get('Company Name')}. Setting to None.")
                level_value = None
    else:
        level_value = None
    
    return {
        'company_id': str(row['Company Name']),
        'assessment_year': int(row['Assessment Date'].split('/')[-1]) if not pd.isna(row['Assessment Date']) else None,
        'management_quality_score': level_value,
    }

def process_cp_assessment_row(row: pd.Series) -> Dict[str, Any]:
    """Process a single row of CP assessment data."""
    # Safely access columns, defaulting to None if missing
    carbon_performance_2025 = str(row.get('Carbon Performance Alignment 2025', None)) if pd.notna(row.get('Carbon Performance Alignment 2025', None)) else None
    carbon_performance_2027 = str(row.get('Carbon Performance Alignment 2027', None)) if pd.notna(row.get('Carbon Performance Alignment 2027', None)) else None
    carbon_performance_2035 = str(row.get('Carbon Performance Alignment 2035', None)) if pd.notna(row.get('Carbon Performance Alignment 2035', None)) else None
    carbon_performance_2050 = str(row.get('Carbon Performance Alignment 2050', None)) if pd.notna(row.get('Carbon Performance Alignment 2050', None)) else None
    
    return {
        'company_id': str(row['Company Name']),
        'assessment_year': int(row['Assessment Date'].split('/')[-1]) if not pd.isna(row['Assessment Date']) else None,
        'carbon_performance_2025': carbon_performance_2025,
        'carbon_performance_2027': carbon_performance_2027,
        'carbon_performance_2035': carbon_performance_2035,
        'carbon_performance_2050': carbon_performance_2050,
        'emissions_trend': None  # Not available in the data
    }

def migrate_data() -> None:
    """
    Migrate all data to database.
    """
    # Database connection
    db_url = "postgresql://postgres:postgres@localhost:5432/tpi_db"
    
    try:
        # Create database engine
        engine = create_engine(db_url)
        
        # Create tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Process ASCOR data
            for trends_pathways_file in ASCOR_RAW_DIR.glob("ASCOR_assessments_results_trends_pathways*.xlsx"):
                trends_pathways_df = pd.read_excel(trends_pathways_file)
                for _, row in trends_pathways_df.iterrows():
                    data = process_trends_pathways_row(row)
                    db_item = ASCORTrendsPathways(**data)
                    db.add(db_item)
                db.commit()
                logger.info(f"Migrated {len(trends_pathways_df)} records to ASCOR_assessments_results_trends_pathways table")
                move_to_processed(trends_pathways_file, is_ascor=True)
            
            # Process ASCOR_assessments_results
            for assessments_file in ASCOR_RAW_DIR.glob("ASCOR_assessments_results*.xlsx"):
                assessments_df = pd.read_excel(assessments_file)
                records_migrated_count = 0
                for _, row in assessments_df.iterrows():
                    data = process_assessments_row(row)
                    if not data: # Should not happen
                        continue

                    db_assessment_item = ASCORAssessments(**data)
                    db.add(db_assessment_item)
                    records_migrated_count += 1
                db.commit()
                logger.info(f"Migrated {records_migrated_count} records from {assessments_file.name}")
                move_to_processed(assessments_file, is_ascor=True)
            
            # Process ASCOR_benchmarks (Country Benchmarks)
            for benchmarks_file in ASCOR_RAW_DIR.glob("ASCOR_benchmarks*.xlsx"):
                benchmarks_df = pd.read_excel(benchmarks_file)
                records_migrated_count = 0
                for _, row in benchmarks_df.iterrows():
                    data = process_benchmarks_row(row)
                    if data and 'country' in data: # Ensure it's an ASCOR benchmark
                        db_benchmark_item = ASCORBenchmarks(**data)
                        db.add(db_benchmark_item)
                        records_migrated_count += 1
                db.commit()
                logger.info(f"Migrated {records_migrated_count} records to ASCOR_benchmarks table from {benchmarks_file.name}")
                move_to_processed(benchmarks_file, is_ascor=True)
            
            # Process ASCOR_countries
            for countries_file in ASCOR_RAW_DIR.glob("ASCOR_countries*.xlsx"):
                countries_df = pd.read_excel(countries_file)
                for _, row in countries_df.iterrows():
                    data = process_countries_row(row)
                    db_item = ASCORCountries(**data)
                    db.add(db_item)
                db.commit()
                logger.info(f"Migrated {len(countries_df)} records to ASCOR_countries table")
                move_to_processed(countries_file, is_ascor=True)
            
            # Process ASCOR_indicators
            for indicators_file in ASCOR_RAW_DIR.glob("ASCOR_indicators*.xlsx"):
                indicators_df = pd.read_excel(indicators_file)
                for _, row in indicators_df.iterrows():
                    data = process_indicators_row(row)
                    db_item = ASCORIndicators(**data)
                    db.add(db_item)
                db.commit()
                logger.info(f"Migrated {len(indicators_df)} records to ASCOR_indicators table")
                move_to_processed(indicators_file, is_ascor=True)
            
            # Process Company data
            for companies_file in SECTOR_RAW_DIR.glob("Company_Latest_Assessments*.csv"):
                companies_df = pd.read_csv(companies_file)
                for _, row in companies_df.iterrows():
                    data = process_company_row(row)
                    # Upsert logic
                    existing = db.query(Company).filter_by(company_id=data['company_id']).first()
                    if existing:
                        for key, value in data.items():
                            setattr(existing, key, value)
                        existing.updated_at = datetime.now()
                    else:
                        db_item = Company(**data)
                        db.add(db_item)
                db.commit()
                logger.info(f"Upserted {len(companies_df)} records to companies table")
                move_to_processed(companies_file, is_ascor=False)
            
            # Process all MQ assessment files
            for mq_file in SECTOR_RAW_DIR.glob("MQ_Assessments_Methodology_*.csv"):
                methodology_cycle_str = mq_file.stem.split('_')[-1]
                try:
                    methodology_cycle = int(methodology_cycle_str)
                except ValueError:
                    logger.error(f"Could not parse methodology_cycle from filename {mq_file.name}. Skipping file.")
                    continue
                
                mq_df = pd.read_csv(mq_file)
                records_migrated_count = 0
                for _, row in mq_df.iterrows():
                    data = process_mq_assessment_row(row)
                    if not data: # Should not happen if parsing is correct
                        continue

                    data['methodology_cycle'] = methodology_cycle # Add cycle from filename
                    db_mq_assessment_item = ManagementQualityAssessment(**data)
                    db.add(db_mq_assessment_item)
                    records_migrated_count += 1
                db.commit()
                logger.info(f"Migrated {records_migrated_count} MQ records from {mq_file.name}")
                move_to_processed(mq_file, is_ascor=False)
            
            # Process CP assessments
            for cp_file in SECTOR_RAW_DIR.glob("CP_Assessments_08032025*.csv"):
                cp_df = pd.read_csv(cp_file)
                for _, row in cp_df.iterrows():
                    data = process_cp_assessment_row(row)
                    db_item = CarbonPerformanceAssessment(**data)
                    db.add(db_item)
                db.commit()
                logger.info(f"Migrated {len(cp_df)} records to cp_assessments table")
                move_to_processed(cp_file, is_ascor=False)
            
            # Process CP Regional assessments
            for cp_regional_file in SECTOR_RAW_DIR.glob("CP_Assessments_Regional_*.csv"):
                cp_regional_df = pd.read_csv(cp_regional_file)
                for _, row in cp_regional_df.iterrows():
                    data = process_cp_assessment_row(row)
                    db_item = CarbonPerformanceAssessment(**data)
                    db.add(db_item)
                db.commit()
                logger.info(f"Migrated {len(cp_regional_df)} records to cp_assessments table from regional data")
                move_to_processed(cp_regional_file, is_ascor=False)
            
            # Process Sector Benchmarks file
            for sector_benchmarks_file in SECTOR_RAW_DIR.glob("Sector_Benchmarks_*.csv"):
                sector_benchmarks_df = pd.read_csv(sector_benchmarks_file)
                records_migrated_count = 0
                for _, row in sector_benchmarks_df.iterrows():
                    data = process_benchmarks_row(row)
                    if data and 'sector_name' in data: # Ensure it's a Sector benchmark
                        db_benchmark_item = SectorBenchmarks(**data)
                        db.add(db_benchmark_item)
                        records_migrated_count += 1
                db.commit()
                logger.info(f"Migrated {records_migrated_count} records to sector_benchmarks table from {sector_benchmarks_file.name}")
                move_to_processed(sector_benchmarks_file, is_ascor=False)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error during migration: {str(e)}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_data() 