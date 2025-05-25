import pandas as pd
import os
import logging
from utils.database_creation_utils import get_engine
import re
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

data_dir = os.path.join(os.path.dirname(__file__), 'data')
ascor_data_dir = os.path.join(data_dir, 'TPI_ASCOR_data_13012025')
tpi_data_dir = os.path.join(data_dir, 'TPI_sector_data_All_sectors_08032025')

def populate_ascor():
    engine = get_engine('ascor_api')
    logger.info('Populating ASCOR tables...')

    # Country
    df_country = pd.read_excel(os.path.join(ascor_data_dir, 'ASCOR_countries.xlsx'))
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
    country_df.to_sql('country', engine, if_exists='append', index=False)
    logger.info('ASCOR: country table populated.')

    # Benchmarks
    df_bench = pd.read_excel(os.path.join(ascor_data_dir, 'ASCOR_benchmarks.xlsx'))
    df_bench.columns = df_bench.columns.str.strip().str.lower().str.replace(' ', '_')
    benchmarks_df = df_bench[[
        'id', 'publication_date', 'emissions_metric', 'emissions_boundary',
        'units', 'benchmark_type', 'country'
    ]].copy()
    benchmarks_df.columns = [
        'benchmark_id', 'publication_date', 'emissions_metric', 'emissions_boundary',
        'units', 'benchmark_type', 'country_name'
    ]
    value_columns = [col for col in df_bench.columns if col.isdigit()]
    benchmark_values_df = df_bench[['id'] + value_columns].melt(
        id_vars='id', var_name='year', value_name='value'
    ).dropna()
    benchmark_values_df.columns = ['benchmark_id', 'year', 'value']
    benchmark_values_df['year'] = benchmark_values_df['year'].astype(int)
    benchmarks_df.to_sql('benchmarks', engine, if_exists='append', index=False)
    benchmark_values_df.to_sql('benchmark_values', engine, if_exists='append', index=False)
    logger.info('ASCOR: benchmarks and benchmark_values tables populated.')

    # Assessment Elements
    df_elements = pd.read_excel(os.path.join(ascor_data_dir, 'ASCOR_indicators.xlsx'))
    df_elements.columns = df_elements.columns.str.strip().str.lower().str.replace(' ', '_')
    assessment_elements_df = df_elements[[
        'code', 'text', 'units_or_response_type', 'type'
    ]].copy()
    assessment_elements_df.columns = ['code', 'text', 'response_type', 'type']
    assessment_elements_df['response_type'] = assessment_elements_df['response_type'].fillna('Not specified')
    assessment_elements_df.to_sql('assessment_elements', engine, if_exists='append', index=False)
    logger.info('ASCOR: assessment_elements table populated.')

    # Assessment Results (wide to long)
    df_results = pd.read_excel(os.path.join(ascor_data_dir, 'ASCOR_assessments_results.xlsx'))
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
        country_name = row["Country"]
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
    
    # Insert into the database
    assessment_results_df.to_sql('assessment_results', engine, if_exists='append', index=False)
    logger.info('ASCOR: assessment_results table populated.')

    # Assessment Trends (wide to long)
    df_trends = pd.read_excel(os.path.join(ascor_data_dir, 'ASCOR_assessments_results_trends_pathways.xlsx'))
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
    
    # Convert date and year fields to appropriate types
    assessment_trends_df["assessment_date"] = pd.to_datetime(assessment_trends_df["assessment_date"], dayfirst=True).dt.date
    assessment_trends_df["publication_date"] = pd.to_datetime(assessment_trends_df["publication_date"], dayfirst=True).dt.date
    assessment_trends_df["last_historical_year"] = assessment_trends_df["last_historical_year"].astype("Int64")
    
    # Create assessment_trends table
    create_assessment_trends_sql = """
    DROP TABLE IF EXISTS value_per_year CASCADE;
    DROP TABLE IF EXISTS assessment_trends CASCADE;

    CREATE TABLE assessment_trends (
      trend_id INT NOT NULL,
      emissions_metric VARCHAR,
      emissions_boundary VARCHAR,
      units VARCHAR,
      assessment_date DATE,
      publication_date DATE,
      last_historical_year INT,
      country_name VARCHAR NOT NULL,
      PRIMARY KEY (trend_id, country_name),
      FOREIGN KEY (country_name) REFERENCES country(country_name)
    );
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_assessment_trends_sql))
        conn.commit()
    
    assessment_trends_df.to_sql('assessment_trends', engine, if_exists='append', index=False)
    logger.info('ASCOR: assessment_trends table populated.')
    
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
    
    # Drop rows with missing values
    value_per_year_df = value_per_year_df.dropna(subset=["value"])
    
    # Create value_per_year table
    create_value_per_year_sql = """
    CREATE TABLE value_per_year (
      year INT NOT NULL,
      value FLOAT NOT NULL,
      trend_id INT NOT NULL,
      country_name VARCHAR NOT NULL,
      FOREIGN KEY (trend_id, country_name) REFERENCES assessment_trends(trend_id, country_name)
    );
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_value_per_year_sql))
        conn.commit()
    
    value_per_year_df.to_sql("value_per_year", engine, if_exists="append", index=False)
    logger.info('ASCOR: value_per_year table populated.')

    # Trend values table
    # Extract relevant columns for trend_values
    trend_values_df = df_trends[[
        "id", "country", "year_metric_ep1.a.i", "metric_ep1.a.i"
    ]].copy()
    trend_values_df.columns = ["trend_id", "country_name", "year", "value"]
    trend_values_df["year"] = pd.to_numeric(trend_values_df["year"], errors="coerce").astype("Int64")
    trend_values_df["value"] = pd.to_numeric(trend_values_df["value"].replace("No data", pd.NA), errors="coerce")
    trend_values_df = trend_values_df.dropna(subset=["year", "value"])
    trend_values_df.to_sql("trend_values", engine, if_exists="append", index=False)
    logger.info('ASCOR: trend_values table populated.')


def populate_tpi():
    engine = get_engine('tpi_api')
    logger.info('Populating TPI tables...')

    # Sector Benchmark
    df_sector = pd.read_csv(os.path.join(tpi_data_dir, 'Sector_Benchmarks_08032025.csv'))
    df_sector.columns = df_sector.columns.str.strip().str.lower().str.replace(' ', '_')
    sector_benchmark_df = df_sector[['benchmark_id', 'sector_name', 'scenario_name', 'region', 'release_date', 'unit']].copy()
    sector_benchmark_df['release_date'] = pd.to_datetime(sector_benchmark_df['release_date'], dayfirst=True)
    sector_benchmark_df.to_sql('sector_benchmark', engine, if_exists='append', index=False)
    
    # Prepare benchmark_projection
    value_columns = [col for col in df_sector.columns if col.isdigit()]
    benchmark_projection_df = df_sector[['benchmark_id', 'sector_name', 'scenario_name'] + value_columns].melt(
        id_vars=['benchmark_id', 'sector_name', 'scenario_name'],
        var_name='benchmark_projection_year',
        value_name='benchmark_projection_attribute'
    ).dropna()
    benchmark_projection_df['benchmark_projection_year'] = benchmark_projection_df['benchmark_projection_year'].astype(int)
    benchmark_projection_df.to_sql('benchmark_projection', engine, if_exists='append', index=False)
    logger.info('TPI: sector_benchmark and benchmark_projection tables populated.')

    # Company
    # Define paths to company files
    file_5 = os.path.join(tpi_data_dir, 'Company_Latest_Assessments_5.0.csv')
    file_4 = os.path.join(tpi_data_dir, 'Company_Latest_Assessments.csv')

    # Load both files
    df_5 = pd.read_csv(file_5)
    df_4 = pd.read_csv(file_4)

    # Map metadata columns
    meta_cols_common = {
        'Company Name': 'company_name',
        'Geography': 'geography',
        'Geography Code': 'geography_code',
        'Sector': 'sector_name',
        'CA100 Focus Company': 'ca100_focus',
        'Large/Medium Classification': 'size_classification',
        'ISINs': 'isin',
        'SEDOL': 'sedol'
    }

    # Extract and tag company data
    df_5_meta = df_5[list(meta_cols_common.keys())].rename(columns=meta_cols_common)
    df_4_meta = df_4[list(meta_cols_common.keys())].rename(columns=meta_cols_common)
    df_5_meta["version"] = "5.0"
    df_4_meta["version"] = "4.0"
    company_df = pd.concat([df_4_meta, df_5_meta], ignore_index=True)

    # Insert into company table
    company_df.to_sql("company", engine, if_exists="append", index=False)
    logger.info('TPI: company table populated.')

    # Company Answer - using MQ Assessments files
    mq_files = [
        'MQ_Assessments_Methodology_1_08032025.csv',
        'MQ_Assessments_Methodology_2_08032025.csv',
        'MQ_Assessments_Methodology_3_08032025.csv',
        'MQ_Assessments_Methodology_4_08032025.csv',
        'MQ_Assessments_Methodology_5_08032025.csv'
    ]
    
    company_answers = []
    for mq_file in mq_files:
        # Extract methodology version from filename
        methodology_version = mq_file.split('_')[3]  # Gets the number after 'Methodology_'
        version = f"{methodology_version}.0"  # Convert to version format (e.g., "1.0")
        
        df_mq = pd.read_csv(os.path.join(tpi_data_dir, mq_file))
        df_mq.columns = df_mq.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Extract questions and their codes
        questions = [col for col in df_mq.columns if col.startswith('q') and '|' in col]
        records = []
        for q in questions:
            code, text = q.split('|', 1)
            for _, row in df_mq.iterrows():
                records.append({
                    'question_code': code.strip(),
                    'question_text': text.strip(),
                    'response': row[q],
                    'company_name': row['company_name'].strip(),
                    'version': version  # Use the extracted version
                })
        company_answers.append(pd.DataFrame(records))
    
    company_answer_df = pd.concat(company_answers, ignore_index=True)
    
    # Drop null responses (required for NOT NULL constraint)
    company_answer_df = company_answer_df.dropna(subset=['response'])
    
    # Keep only the last occurrence of each question-company-version combination
    # This ensures we use the most recent answer if a question appears in multiple files
    company_answer_df = company_answer_df.drop_duplicates(
        subset=['question_code', 'company_name', 'version'],
        keep='last'
    )
    
    # Enforce FK constraint: only include answers for existing companies
    with engine.connect() as conn:
        valid_keys = pd.read_sql(
            "SELECT company_name, version FROM company",
            conn
        )
    valid_keys = set(zip(valid_keys['company_name'], valid_keys['version']))
    company_answer_df = company_answer_df[
        company_answer_df.apply(
            lambda row: (row['company_name'], row['version']) in valid_keys,
            axis=1
        )
    ]
    
    company_answer_df.to_sql('company_answer', engine, if_exists='append', index=False)
    logger.info('TPI: company_answer table populated.')

    # MQ Assessment
    df_mq = pd.read_csv(os.path.join(tpi_data_dir, 'Company_Latest_Assessments.csv'))
    df_mq.columns = df_mq.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Convert dates and handle missing values
    df_mq['assessment_date'] = pd.to_datetime(df_mq['mq_assessment_date'], dayfirst=True, errors='coerce')
    df_mq['publication_date'] = pd.to_datetime(df_mq['mq_publication_date'], errors='coerce')
    
    # Log number of records before dropping
    initial_count = len(df_mq)
    
    # Drop rows with missing assessment dates
    df_mq = df_mq.dropna(subset=['assessment_date'])
    
    # Log number of records dropped
    dropped_count = initial_count - len(df_mq)
    if dropped_count > 0:
        logger.warning(f'Dropped {dropped_count} MQ assessment records due to missing assessment dates')
    
    mq_assessment_df = df_mq[['company_name', 'level', 'assessment_date', 'publication_date']].copy()
    mq_assessment_df['version'] = '5.0'  # Add version column with default value
    mq_assessment_df['tpi_cycle'] = 5  # Add tpi_cycle column
    mq_assessment_df.columns = ['company_name', 'level', 'assessment_date', 'publication_date', 'version', 'tpi_cycle']
    mq_assessment_df.to_sql('mq_assessment', engine, if_exists='append', index=False)
    logger.info('TPI: mq_assessment table populated.')

    # CP Assessment
    cp_dir = tpi_data_dir
    
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
    
    # Insert into DB
    if assessment_records:
        pd.concat(assessment_records).to_sql("cp_assessment", engine, if_exists="append", index=False)
        logger.info('TPI: cp_assessment table populated.')
    
    if alignment_records:
        pd.concat(alignment_records).to_sql("cp_alignment", engine, if_exists="append", index=False)
        logger.info('TPI: cp_alignment table populated.')
    
    if projection_records:
        pd.concat(projection_records).to_sql("cp_projection", engine, if_exists="append", index=False)
        logger.info('TPI: cp_projection table populated.')


def main():
    populate_ascor()
    populate_tpi()
    logger.info('All tables populated successfully.')

if __name__ == '__main__':
    main() 