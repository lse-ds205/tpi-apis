import pandas as pd
from pathlib import Path as FilePath
from utils.utils import (
    get_latest_data_dir,
    get_latest_assessment_file,
    get_latest_cp_file,
    normalize_company_id,
)
from datetime import datetime
from utils.filters import CompanyFilters, MQFilter

class BaseDataHandler:
    """Base class for handling data operations with common functionality.
    
    This class provides basic DataFrame operations and pagination functionality
    that can be inherited by specific data handlers.
    """
    
    def __init__(self):
        """Initialize the base data handler with empty DataFrame and files list."""
        self._df = pd.DataFrame()
        self._files = []

    def get_df(self):
        """Get the current DataFrame.
        
        Returns:
            pd.DataFrame: The current DataFrame containing the data.
        """
        return self._df
    
    def get_files(self):
        """Get the list of files being used.
        
        Returns:
            list: List of file paths being used by the handler.
        """
        return self._files
    
    def get_df_length(self):
        """Get the number of rows in the DataFrame.
        
        Returns:
            int: Number of rows in the current DataFrame.
        """
        return len(self._df)
    
    def get_files_length(self):
        """Get the number of files being used.
        
        Returns:
            int: Number of files in the files list.
        """
        return len(self._files)
    
    def paginate(self, df: pd.DataFrame, page: int, per_page: int) -> pd.DataFrame:
        """Paginate a DataFrame based on page number and items per page.
        
        Args:
            df (pd.DataFrame): DataFrame to paginate
            page (int): Page number (1-based)
            per_page (int): Number of items per page
            
        Returns:
            pd.DataFrame: Paginated slice of the input DataFrame
        """
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        return df.iloc[start_idx:end_idx].fillna("N/A").infer_objects(copy=False)
    
    def _sanitize_text(self, text: str, preserve_case: bool = False) -> str:
        """
        Sanitize text by stripping whitespace and optionally converting to lowercase.
        
        Args:
            text (str): The text to sanitize.
            preserve_case (bool): Whether to preserve the original case.
            
        Returns:
            str: Sanitized text.
        """
        if not isinstance(text, str):
            return text
        text = text.strip()
        return text if preserve_case else text.lower()
    
    def _sanitize_data(self) -> None:
        """Sanitize all text fields in the dataframes."""
        # Sanitize company data
        text_columns = self.company_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            if col == "company name":
                self.company_df[col] = self.company_df[col].apply(
                    lambda x: self._sanitize_text(x, preserve_case=True)
                )
            else:
                self.company_df[col] = self.company_df[col].apply(self._sanitize_text)
        
        # Sanitize MQ data
        text_columns = self.mq_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            if col == "company name":
                self.mq_df[col] = self.mq_df[col].apply(
                    lambda x: self._sanitize_text(x, preserve_case=True)
                )
            else:
                self.mq_df[col] = self.mq_df[col].apply(self._sanitize_text)
        
        # Sanitize CP data
        text_columns = self.cp_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            if col == "company name":
                self.cp_df[col] = self.cp_df[col].apply(
                    lambda x: self._sanitize_text(x, preserve_case=True)
                )
            else:
                self.cp_df[col] = self.cp_df[col].apply(self._sanitize_text)

    def get_company_history(self,company_id: str):
        normalized_company_id = normalize_company_id(company_id)
        mask = (
            self._df["company name"].apply(normalize_company_id) == normalized_company_id
        )
        company = self._df[mask]
        return company
    
    def get_latest_details(self, company_id: str):
        company = self.get_company_history(company_id)
        if company.empty:
            raise ValueError(f"Company '{company_id}' not found.")
        latest_record = company.iloc[-1]
        return latest_record.fillna("N/A")
    
    def get_latest_assessments(self, page: int, page_size: int):
        """Get latest assessments with pagination."""
        latest_records = (
            self._df.sort_values("assessment date")
            .groupby("company name")
            .tail(1)
        )
        return self.paginate(latest_records, page, page_size)
    
    def apply_company_filter(self, filters: CompanyFilters):
        """Apply filters to the DataFrame.

        Args:
            filters (CompanyFilters): Filter object containing filter parameters for filtering companies
            
        Returns:
            pd.DataFrame: Filtered DataFrame with only matching records
        """    
        # Create a copy of the DataFrame to avoid modifying original

        filtered_df = self._df.copy()
        
        # Apply geography filter
        if filters.geography:
            filtered_df = filtered_df[filtered_df["geography"] == filters.geography]
            
        # Apply geography code filter
        if filters.geography_code:
            filtered_df = filtered_df[filtered_df["geography code"] == filters.geography_code]
            
        # Apply sector filter
        if filters.sector:
            filtered_df = filtered_df[filtered_df["sector"] == filters.sector]
            
        # Apply CA100 filter
        if filters.ca100_focus_company is not None:
            # Find the column containing 'ca100' (case-insensitive)
            ca100_cols = [col for col in filtered_df.columns if 'ca100' in col.lower()]            
            ca100_col = ca100_cols[0] 
            if filters.ca100_focus_company:
                filtered_df = filtered_df[filtered_df[ca100_col] == "Yes"]
            else:
                filtered_df = filtered_df[filtered_df[ca100_col] != "Yes"]
                
        # Apply company size filter
        if filters.large_medium_classification:
            filtered_df = filtered_df[filtered_df["large/medium classification"] == filters.large_medium_classification]
            
        # Apply ISIN filter
        if filters.isins:
            if isinstance(filters.isins, str):
                filtered_df = filtered_df[filtered_df["isins"].str.contains(filters.isins, na=False)]
            else:
                mask = filtered_df["isins"].apply(lambda x: any(isin in str(x) for isin in filters.isins))
                filtered_df = filtered_df[mask]
                
        # Apply SEDOL filter
        if filters.sedol:
            if isinstance(filters.sedol, str):
                filtered_df = filtered_df[filtered_df["sedol"].str.contains(filters.sedol, na=False)]
            else:
                mask = filtered_df["sedol"].apply(lambda x: any(sedol in str(x) for sedol in filters.sedol))
                filtered_df = filtered_df[mask]
            
        self._df = filtered_df

class MQHandler(BaseDataHandler):
    """Handler for Management Quality (MQ) assessment data.
    
    This class manages loading and processing of MQ assessment data from CSV files,
    providing methods to access and analyze the data.
    """

    def __init__(self):
        """Initialize the MQ handler and load MQ data."""
        super().__init__()
        self._df = self.load_mq_data()

    def get_mq_files_length(self):
        """Get the number of MQ assessment files.
        
        Returns:
            int: Number of MQ assessment files loaded.
        """
        return len(self.mq_files)

    def load_mq_data(self):
        """Load and process MQ assessment data from CSV files.
        
        Returns:
            pd.DataFrame: Processed MQ assessment data
            
        Raises:
            FileNotFoundError: If no MQ datasets are found
        """
        DATA_DIR = get_latest_data_dir(FilePath(__file__).resolve().parent / "data")

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
    
    
    def apply_mq_filter(self, filters: MQFilter):
        """Apply filters to the DataFrame.

        Args:
            filters (MQFilter): Filter object containing filter parameters for filtering companies
        """
        filtered_df = self._df.copy()
        
        if filters.assessment_year:
            filtered_df = filtered_df[filtered_df['Assessment Date'].str.contains(str(filters.assessment_year))]
        if filtered_df.empty:
            raise ValueError(f"Assessment Year is not valid: {filters.assessment_year}")
        
        # both of these can be simplified by using a service layer and simplying into check if valid in column name
        if filters.mq_levels:
            valid_mq_levels = filtered_df['MQ Level'].unique()
            invalid_levels = [level for level in filters.mq_levels if level not in valid_mq_levels]
            if invalid_levels:
                raise ValueError(f"MQ Levels are not valid: {invalid_levels}")
            filtered_df = filtered_df[filtered_df['MQ Level'].isin(filters.mq_levels)]

        if filters.level:
            valid_levels = filtered_df['Overall Management Level'].unique()
            invalid_levels = [level for level in filters.level if level not in valid_levels]
            if invalid_levels:
                raise ValueError(f"Overall Management Level is not valid: {invalid_levels}")
            filtered_df = filtered_df[filtered_df['Overall Management Level'].isin(filters.level)]

        self._df = filtered_df


    def get_methodology_data(self, methodology_id: int):
        """Get MQ assessments for a specific methodology cycle.
        
        Args:
            methodology_id (int): Methodology cycle ID (1-based)
            
        Returns:
            pd.DataFrame: Assessments for the specified methodology
            
        Raises:
            ValueError: If methodology_id is out of range
        """
        if not 1 <= methodology_id <= len(self.mq_files):
            raise ValueError(f"Methodology ID must be between 1 and {len(self.mq_files)}")
        
        return self._df[self._df["methodology_cycle"] == methodology_id]

    def get_sector_data(self, sector_id: str):
        """Get MQ assessments for a specific sector.
        
        Args:
            sector_id (str): Sector identifier
            
        Returns:
            pd.DataFrame: Assessments for the specified sector, sorted by date
        """
        sector_data = self._df[
            self._df["sector"].str.strip().str.lower() == sector_id.strip().lower()
        ]
        return sector_data.sort_values("assessment date", ascending=False)

class CPHandler(BaseDataHandler):
    """Handler for Carbon Performance (CP) assessment data.
    
    This class manages loading and processing of CP assessment data from CSV files,
    providing methods to access and analyze the data.
    """

    def __init__(self, prefix=None, *args, **kwargs):
        self.prefix = prefix
        """Initialize the CP handler and load CP data."""
        super().__init__()
        self._df = self.load_cp_data()

    def load_cp_data(self):
        """Load and process CP assessment data from CSV files.
        
        Returns:
            pd.DataFrame: Processed CP assessment data
            
        Raises:
            ValueError: If no CP assessment files are found or required columns are missing
        """
        DATA_DIR = get_latest_data_dir(
            FilePath(__file__).resolve().parent / "data",
            prefix="TPI_sector_data_All_sectors_"
        )

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
        cp_df.columns = cp_df.columns.str.strip()

        # Validate required columns
        required_columns = ["Company Name", "Assessment Date", "Sector", "Geography"]
        missing_columns = [col for col in required_columns if col not in cp_df.columns]
        if missing_columns:
            raise ValueError(f"Required columns missing in CP dataset: {', '.join(missing_columns)}")
        
        return cp_df

    def get_company_alignment(self, company_id: str):
        """Get a company's carbon performance alignment status.
        
        Args:
            company_id (str): Company identifier
            
        Returns:
            pd.Series: Latest CP alignment record
            
        Raises:
            ValueError: If company is not found
        """
        company_data = self.get_company_history(company_id)
        if company_data.empty:
            raise ValueError(f"Company '{company_id}' not found")
        latest_record = company_data.sort_values("Assessment Date").iloc[-1]
        return latest_record
    
    def compare_company_cp(self, company_id: str):
        """Compare a company's CP assessments over time.
        
        Args:
            company_id (str): Company identifier
            
        Returns:
            tuple: (latest_record, previous_record) if comparison is possible
            tuple: (None, available_years) if insufficient data
        """
        company_data = self.get_company_history(company_id)

        if len(company_data) < 2:
            available_years = [
                pd.to_datetime(date, errors="coerce").year
                for date in company_data["Assessment Date"]
            ]
            available_years = [year for year in available_years if year is not None]
            return None, available_years

        sorted_data = company_data.sort_values("Assessment Date", ascending=False)
        return sorted_data.iloc[0], sorted_data.iloc[1]

class CompanyDataHandler(BaseDataHandler):
    """Handler for company assessment data.
    
    This class manages loading and processing of company assessment data,
    providing methods to access and analyze company information.
    """

    def __init__(self):
        """Initialize the company data handler and load company data."""
        super().__init__()
        self._df = self.load_company_data()

    def load_company_data(self):
        """Load and process company assessment data from CSV files.
        
        Returns:
            pd.DataFrame: Processed company assessment data
            
        Raises:
            Exception: If data loading fails
        """
        try:
            DATA_DIR = get_latest_data_dir(FilePath(__file__).resolve().parent / "data")
            print(f"Loading company data from directory: {DATA_DIR}")

            # Define the path for the company assessments CSV file.
            latest_file = get_latest_assessment_file(
                "Company_Latest_Assessments*.csv", DATA_DIR
            )
            print(f"Found latest company assessments file: {latest_file}")

            # Load the company dataset into a DataFrame.
            company_df = pd.read_csv(latest_file)
            print(f"Loaded {len(company_df)} company records")

            # Standardize column names: strip extra spaces and convert to lowercase.
            company_df.columns = company_df.columns.str.strip().str.lower()

            company_df["company name"] = company_df["company name"].apply(normalize_company_id)

            return company_df
        except Exception as e:
            print(f"Error in load_company_data: {str(e)}")
            raise
    
    def format_data(self, df: pd.DataFrame):
        """Format company data into a standardized structure.
        
        Args:
            df (pd.DataFrame): Input DataFrame with company data
            
        Returns:
            list: List of dictionaries containing formatted company data
        """
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
        history = self.get_company_history(company_id)

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
        history = self.get_company_history(company_id)
        available_years = []
        
        for date_str in history["mq assessment date"].dropna():
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                available_years.append(dt.year)
            except (ValueError, TypeError):
                continue
                
        return available_years