from .base_pipeline import BasePipeline
import pandas as pd
import os
import re
from datetime import datetime
import logging

class TPIPipeline(BasePipeline):
    """Pipeline for TPI database operations."""
    
    def __init__(self, data_dir: str, logger: logging.Logger):
        """Initialize TPI pipeline.
        
        Args:
            data_dir (str): Path to the data directory
            logger (logging.Logger): Logger instance to use
        """
        super().__init__('tpi_api', data_dir, logger)
        self.tpi_data_dir = os.path.join(data_dir, 'TPI_sector_data_All_sectors_08032025')



    def _process_data(self):
        """Process TPI data from files into dataframes."""
        # Company
        # Define paths to company files
        file_5 = os.path.join(self.tpi_data_dir, 'Company_Latest_Assessments_5.0.csv')
        file_4 = os.path.join(self.tpi_data_dir, 'Company_Latest_Assessments.csv')

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
            
            df_mq = pd.read_csv(os.path.join(self.tpi_data_dir, mq_file))
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
        self.data['company'] = all_companies

        # Store company data - it will be inserted via bulk_insert in populate_tables

        # Create a set of valid company-version combinations for foreign key validation
        valid_companies = set(zip(all_companies['company_name'].str.strip(), all_companies['version']))

        # Company Answers - using MQ Assessments files
        company_answers = []
        for mq_file in mq_files:
            # Extract methodology version from filename
            methodology_version = mq_file.split('_')[3]  # Gets the number after 'Methodology_'
            version = f"{methodology_version}.0"  # Convert to version format (e.g., "1.0")
            
            df_mq = pd.read_csv(os.path.join(self.tpi_data_dir, mq_file))
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
                        self.logger.warning(f"Skipping company answer for invalid company-version combination: {company_name} (v{version})")
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
        self.data['company_answer'] = company_answer_df

        # MQ Assessment
        mq_records = []
        for mq_file in mq_files:
            # Extract methodology version from filename
            methodology_version = mq_file.split('_')[3]  # Gets the number after 'Methodology_'
            tpi_cycle = int(methodology_version)  # Convert to integer for tpi_cycle
            version = f"{methodology_version}.0"
            
            df_mq = pd.read_csv(os.path.join(self.tpi_data_dir, mq_file))
            df_mq.columns = df_mq.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Process the data
            df_mq['tpi_cycle'] = tpi_cycle
            df_mq['version'] = version
            df_mq['company_name'] = df_mq['company_name'].str.strip()
            
            # Filter out invalid company-version combinations
            invalid_companies = df_mq[~df_mq.apply(lambda x: (x['company_name'], x['version']) in valid_companies, axis=1)]
            if not invalid_companies.empty:
                self.logger.warning("Found MQ assessments with invalid company-version combinations:")
                for company in invalid_companies['company_name'].unique():
                    self.logger.warning(f"- {company} (v{version})")
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
        self.data['mq_assessment'] = mq_df

        # CP Assessment
        cp_dir = self.tpi_data_dir
        
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
                self.logger.warning("Found CP assessments with invalid company-version combinations:")
                for company in invalid_companies["company_name"].unique():
                    self.logger.warning(f"- {company} (v5.0)")
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
        
        # Store CP data in data dictionary
        if assessment_records:
            self.data['cp_assessment'] = pd.concat(assessment_records)
        if alignment_records:
            self.data['cp_alignment'] = pd.concat(alignment_records)
        if projection_records:
            self.data['cp_projection'] = pd.concat(projection_records)

        # Sector Benchmark
        df_sector = pd.read_csv(os.path.join(self.tpi_data_dir, 'Sector_Benchmarks_08032025.csv'))
        df_sector.columns = df_sector.columns.str.strip().str.lower().str.replace(' ', '_')
        sector_benchmark_df = df_sector[['benchmark_id', 'sector_name', 'scenario_name', 'region', 'release_date', 'unit']].copy()
        sector_benchmark_df['release_date'] = pd.to_datetime(sector_benchmark_df['release_date'], dayfirst=True)
        self.data['sector_benchmark'] = sector_benchmark_df
        
        # Prepare benchmark_projection
        value_columns = [col for col in df_sector.columns if col.isdigit()]
        benchmark_projection_df = df_sector[['benchmark_id', 'sector_name', 'scenario_name'] + value_columns].melt(
            id_vars=['benchmark_id', 'sector_name', 'scenario_name'],
            var_name='benchmark_projection_year',
            value_name='benchmark_projection_attribute'
        ).dropna()
        benchmark_projection_df['benchmark_projection_year'] = benchmark_projection_df['benchmark_projection_year'].astype(int)
        self.data['benchmark_projection'] = benchmark_projection_df

    def _validate_data(self) -> dict:
        """Validate TPI data."""
        return self.validator.validate_tpi_data(self.data)

 