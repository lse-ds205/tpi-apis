import pandas as pd
from pathlib import Path as FilePath
from utils import (
    get_latest_data_dir,
    get_latest_assessment_file,
    get_latest_cp_file,
    normalize_company_id,
)
from datetime import datetime
from fastapi import HTTPException
class MQHandler:

    def __init__(self):
        self.mq_files = []
        self.df = self.load_mq_data()

    def get_mq_files_length(self):
        return len(self.mq_files)

    def load_mq_data(self):
        """Load and process MQ assessment data from CSV files."""
        BASE_DIR = FilePath(__file__).resolve().parent
        BASE_DATA_DIR = BASE_DIR / "data"
        DATA_DIR = get_latest_data_dir(BASE_DATA_DIR)

        self.mq_files = sorted(DATA_DIR.glob("MQ_Assessments_Methodology_*.csv"))
        if not self.mq_files:
            raise FileNotFoundError(f"No MQ datasets found in {DATA_DIR}")
        print(len(self.mq_files))
        mq_df_list = [pd.read_csv(f) for f in self.mq_files]

        for idx, df in enumerate(mq_df_list, start=1):
            df["methodology_cycle"] = idx

        mq_df = pd.concat(mq_df_list, ignore_index=True)
        mq_df.columns = mq_df.columns.str.strip().str.lower()

        return mq_df

    def get_latest_assessments(self, page: int, page_size: int):
        """Get latest MQ assessments with pagination."""
        latest_records = (
            self.df.sort_values("assessment date")
            .groupby("company name")
            .tail(1)
        )

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return latest_records.iloc[start_idx:end_idx]

    def get_methodology_data(self, methodology_id: int):
        """Get MQ assessments for a specific methodology cycle."""
        if not 1 <= methodology_id <= len(self.mq_files):
            raise ValueError(f"Methodology ID must be between 1 and {len(self.mq_files)}")
        
        return self.df[self.df["methodology_cycle"] == methodology_id]

    def get_sector_data(self, sector_id: str):
        """Get MQ assessments for a specific sector."""
        sector_data = self.df[
            self.df["sector"].str.strip().str.lower() == sector_id.strip().lower()
        ]
        
       
        return sector_data.sort_values("assessment date", ascending=False)

    def get_company_history(self, company_id: str):
        """Get all MQ assessments for a specific company."""
        normalized_id = normalize_company_id(company_id)
        company_history = self.df[
            self.df["company name"].apply(normalize_company_id) == normalized_id
        ]
        
        if company_history.empty:
            raise ValueError(f"Company '{company_id}' not found")
            
        return company_history

    def get_company_latest(self, company_id: str):
        """Get the latest MQ assessment for a specific company."""
        company_history = self.get_company_history(company_id)
        return company_history.sort_values("assessment date").iloc[-1]

class CPHandler:
    def __init__(self):
        self.df = self.load_cp_data()

    def load_cp_data(self):
        """Load and process CP assessment data from CSV files."""
        BASE_DIR = FilePath(__file__).resolve().parent
        BASE_DATA_DIR = BASE_DIR / "data"
        DATA_DIR = get_latest_data_dir(BASE_DATA_DIR)

        # Get CP assessment files
        cp_files = get_latest_cp_file("CP_Assessments_*.csv", DATA_DIR)
        if not cp_files:
            raise ValueError("No CP assessment files found in data directory")

        # Load and process each file
        cp_df_list = [pd.read_csv(f) for f in cp_files]
        if not cp_df_list:
            raise ValueError("Failed to load CP assessment data from files")

        # Add assessment cycle and normalize column names
        for idx, df in enumerate(cp_df_list, start=1):
            df["assessment_cycle"] = idx

        cp_df = pd.concat(cp_df_list, ignore_index=True)
        cp_df.columns = cp_df.columns.str.strip().str.lower()

        # Validate required columns
        required_columns = ["company name", "assessment date", "sector", "geography"]
        missing_columns = [col for col in required_columns if col not in cp_df.columns]
        if missing_columns:
            raise ValueError(f"Required columns missing in CP dataset: {', '.join(missing_columns)}")
        

        return cp_df

    def get_latest_assessments(self, page: int, page_size: int):
        """Get latest CP assessments with pagination."""
        latest_records = (
            self.df.sort_values("assessment date")
            .groupby("company name")
            .tail(1)
        )

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return latest_records.iloc[start_idx:end_idx]

    def get_company_history(self, company_id: str):
        """Get all CP assessments for a specific company."""
        normalized_id = normalize_company_id(company_id)
        company_history = self.df[
            self.df["company name"].apply(normalize_company_id)  == normalized_id
        ]
        
        return company_history

    def get_company_alignment(self, company_id: str):
        """Get a company's carbon performance alignment status."""
        company_data = self.get_company_history(company_id)
        if company_data.empty:
            raise ValueError(f"Company '{company_id}' not found")
        latest_record = company_data.sort_values("assessment date").iloc[-1]
        return latest_record

    def compare_company_cp(self, company_id: str):
        """Compare a company's CP assessments over time."""
        company_data = self.get_company_history(company_id)

        if len(company_data) < 2:
            available_years = [
                pd.to_datetime(date, errors="coerce").year
                for date in company_data["assessment date"]
            ]
            available_years = [year for year in available_years if year is not None]
            return None, available_years

        sorted_data = company_data.sort_values("assessment date", ascending=False)
        return sorted_data.iloc[0], sorted_data.iloc[1]

class CompanyDataHandler:

    def __init__(self):
        self.df = self.load_company_data()

    def load_company_data(self):
        BASE_DIR = FilePath(__file__).resolve().parent
        BASE_DATA_DIR = BASE_DIR / "data"
        DATA_DIR = get_latest_data_dir(BASE_DATA_DIR)

        # Define the path for the company assessments CSV file.
        latest_file = get_latest_assessment_file(
            "Company_Latest_Assessments*.csv", DATA_DIR
        )

        # Load the company dataset into a DataFrame.
        company_df = pd.read_csv(latest_file)

        # Standardize column names: strip extra spaces and convert to lowercase.
        company_df.columns = company_df.columns.str.strip().str.lower()

        company_df["company name"] = company_df["company name"].apply(normalize_company_id)

        return company_df
    
    def format_data(self, df: pd.DataFrame):
        # Map each row to a company dictionary with a normalized unique ID.
        companies = [
        {
            "company_id": row["company name"],
            "name": row["company name"],  # Original company name
            "sector": row.get("sector", None),
            "geography": row.get("geography", None),
            "latest_assessment_year": row.get("latest assessment year", None),
        }
        for _, row in df.iterrows()
        ]
        return companies
    
    def get_all(self):
        return self.df
    
    def get_details(self, company_id: str):
        # normalize to ensure
        normalized_company_id = normalize_company_id(company_id)
        mask = (
            self.df["company name"] == normalized_company_id
        )
        company = self.df[mask]
        return company
    
    def get_latest_details(self, company_id: str):
        company = self.get_details(company_id)
        latest_record = company.iloc[-1]
        return latest_record.fillna("N/A")
    
    def compare_performance(self, company_id: str):
        """
        Compare a company's latest performance against the previous year.
        
        Args:
            company_id (str): The normalized company ID
            
        Returns:
            tuple: (latest_record, previous_record) if comparison is possible
            None: If comparison is not possible
            
        Raises:
            HTTPException: If company not found or required columns missing
        """
        history = self.get_details(company_id)

        if history.empty:
            raise HTTPException(
                status_code=404, detail=f"Company '{company_id}' not found."
            )

        if "mq assessment date" not in history.columns:
            raise HTTPException(
                status_code=500,
                detail="Column 'MQ Assessment Date' not found in dataset. Check CSV structure.",
            )

        if len(history) < 2:
            return None

        # Sort records by assessment date
        history = history.copy()
        history["assessment_year"] = history["mq assessment date"].apply(
            lambda x: (
                int(datetime.strptime(x, "%d/%m/%Y").year)
                if pd.notna(x)
                else None
            )
        )
        history = history.sort_values(by="assessment_year", ascending=False)
        
        return history.iloc[0], history.iloc[1]

    def get_available_years(self, company_id: str):
        """
        Get available assessment years for a company.
        
        Args:
            company_id (str): The normalized company ID
            
        Returns:
            list: List of available assessment years
        """
        history = self.get_details(company_id)
        available_years = []
        
        for date_str in history["mq assessment date"].dropna():
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                available_years.append(dt.year)
            except (ValueError, TypeError):
                continue
                
        return available_years

class DataHandler:

    def __init__(self):
        self.company = CompanyDataHandler()
        self.cp = CPHandler()
        self.mq = MQHandler()

    def paginate(self, df: pd.DataFrame, page: int, per_page: int):
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        return df.iloc[start_idx:end_idx].fillna("N/A")