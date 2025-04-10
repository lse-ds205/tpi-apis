"""
Data handling utilities for the TPI API.

This module provides a DataHandler class that encapsulates all data operations,
including loading and serving CP, MQ, and company data with support for filtering,
pagination, and sorting.
"""


import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Union, Tuple
from utils import (
    get_latest_data_dir,
    get_latest_assessment_file,
    get_latest_cp_file,
    normalize_company_id,
)
STAR_MAPPING = {
    "0STAR": 0.0,
    "1STAR": 1.0,
    "2STAR": 2.0,
    "3STAR": 3.0,
    "4STAR": 4.0,
    "5STAR": 5.0,
}

class DataHandler:
    """
    A class to handle all data operations for the TPI API.
    
    This class provides methods to:
    - Load and serve CP, MQ, and company data
    - Handle data filtering
    - Support pagination and sorting
    """
    
    def __init__(self, base_data_dir: Path):
        """
        Initialize the DataHandler with the base data directory.
        
        Args:
            base_data_dir (Path): The base directory containing the data files.
        """
        self.base_data_dir = base_data_dir
        self.data_dir = get_latest_data_dir(base_data_dir)
        self._load_data()
        self._sanitize_data()
    
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
    
    def _load_data(self) -> None:
        # Load company data
        company_file = get_latest_assessment_file(
            "Company_Latest_Assessments*.csv", self.data_dir
        )
        self.company_df = pd.read_csv(company_file)
        self.company_df.columns = self.company_df.columns.str.strip().str.lower()
        
        # Load MQ data
        mq_files = sorted(self.data_dir.glob("MQ_Assessments_Methodology_*.csv"))
        if not mq_files:
            raise FileNotFoundError(f"No MQ datasets found in {self.data_dir}")
        
        mq_df_list = [pd.read_csv(f) for f in mq_files]
        for idx, df in enumerate(mq_df_list, start=1):
            df["methodology_cycle"] = idx
        
        self.mq_df = pd.concat(mq_df_list, ignore_index=True)
        self.mq_df.columns = self.mq_df.columns.str.strip().str.lower()
        
        # Load CP data
        cp_files = get_latest_cp_file("CP_Assessments_*.csv", self.data_dir)
        cp_df_list = [pd.read_csv(f) for f in cp_files]
        
        for idx, df in enumerate(cp_df_list, start=1):
            df["assessment_cycle"] = idx
        
        self.cp_df = pd.concat(cp_df_list, ignore_index=True)
        self.cp_df.columns = self.cp_df.columns.str.strip().str.lower()
    
    def get_companies(
        self,
        page: int = 1,
        per_page: int = 10,
        sector: Optional[str] = None,
        geography: Optional[str] = None,
    ) -> Tuple[List[Dict], int]:
        """
        Get a paginated list of companies with optional filtering.
        
        Args:
            page (int): Page number (1-based).
            per_page (int): Number of results per page.
            sector (Optional[str]): Filter by sector.
            geography (Optional[str]): Filter by geography.
            
        Returns:
            Tuple[List[Dict], int]: List of company dictionaries and total count.
        """
        df = self.company_df.copy()
        
        if sector:
            sector = self._sanitize_text(sector)
            df = df[df["sector"].str.lower() == sector]
        if geography:
            geography = self._sanitize_text(geography)
            df = df[
                df["geography"].apply(lambda x: self._sanitize_text(x)) == geography
            ]
        
        total = len(df)
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        df = df.iloc[start_idx:end_idx]
        
        companies = []
        for _, row in df.iterrows():
            company_name = row["company name"]
            company_id = normalize_company_id(company_name)
            
            assessment_year = None
            date_field = row.get("latest assessment date", None)
            
            if pd.notna(date_field) and isinstance(date_field, str):
                try:
                    assessment_year = datetime.strptime(date_field, "%d/%m/%Y").year
                except (ValueError, TypeError):
                    assessment_year = row.get("latest assessment year", None)
            else:
                cp_mask = (
                    self.cp_df["company name"].str.lower() == company_name.lower()
                )
                cp_company = self.cp_df[cp_mask]
                
                if not cp_company.empty:
                    cp_dates = pd.to_datetime(
                        cp_company["assessment date"], 
                        format="%d/%m/%Y", 
                        errors='coerce'
                    )
                    if not cp_dates.isna().all():
                        assessment_year = cp_dates.max().year
                else:
                    mq_mask = (
                        self.mq_df["company name"].str.lower() == company_name.lower()
                    )
                    mq_company = self.mq_df[mq_mask]
                    
                    if not mq_company.empty:
                        mq_dates = pd.to_datetime(
                            mq_company["assessment date"], 
                            format="%d/%m/%Y", 
                            errors='coerce'
                        )
                        if not mq_dates.isna().all():
                            assessment_year = mq_dates.max().year
            
            if pd.notna(assessment_year):
                try:
                    assessment_year = int(assessment_year)
                except (ValueError, TypeError):
                    pass
            
            companies.append({
                "company_id": company_id,
                "name": company_name,
                "sector": row.get("sector", None),
                "geography": row.get("geography", None),
                "latest_assessment_year": assessment_year,
            })
        
        return companies, total
    
    def get_company_details(self, company_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific company.
        
        Args:
            company_id (str): The company ID to look up.
            
        Returns:
            Optional[Dict]: Company details or None if not found.
        """
        normalized_id = normalize_company_id(company_id)
        mask = (
            self.company_df["company name"].apply(normalize_company_id)
            == normalized_id
        )
        company = self.company_df[mask]
        
        if company.empty:
            return None
        
        latest_record = company.iloc[-1].fillna("N/A")
        
        return {
            "company_id": normalized_id,
            "name": latest_record["company name"], 
            "sector": latest_record.get("sector", "N/A"),
            "geography": latest_record.get("geography", "N/A"),
            "latest_assessment_year": latest_record.get("latest assessment year", None),
            "management_quality_score": latest_record.get("level", None),
            "carbon_performance_alignment_2035": str(
                latest_record.get("carbon performance alignment 2035", "N/A")
            ),
            "emissions_trend": latest_record.get(
                "performance compared to previous year", "Unknown"
            ),
        }
    
    def get_mq_assessments(
        self,
        page: int = 1,
        per_page: int = 10,
        methodology_id: Optional[int] = None,
        sector: Optional[str] = None,
    ) -> Tuple[List[Dict], int]:
        """
        Get MQ assessments with optional filtering and pagination.
        
        Args:
            page (int): Page number (1-based).
            per_page (int): Number of results per page.
            methodology_id (Optional[int]): Filter by methodology cycle.
            sector (Optional[str]): Filter by sector.
            
        Returns:
            Tuple[List[Dict], int]: List of MQ assessment dictionaries and total count.
        """
        df = self.mq_df.copy()
        
        if methodology_id:
            df = df[df["methodology_cycle"] == methodology_id]
        if sector:
            sector = self._sanitize_text(sector)
            df = df[df["sector"] == sector]
        
        df = df.sort_values("assessment date").groupby("company name").tail(1)
        
        total = len(df)
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        df = df.iloc[start_idx:end_idx]
        
        def get_mq_score(level):
            if pd.isna(level) or level == "N/A":
                return None
            try:
                return float(level)
            except (ValueError, TypeError):
                # If it's in format like "4STAR", extract the number
                if isinstance(level, str) and "STAR" in level:
                    return STAR_MAPPING.get(level, None)
                return None
        
        assessments = [
            {
                "company_id": row["company name"],
                "name": row["company name"], 
                "sector": row.get("sector", "N/A"),
                "geography": row.get("geography", "N/A"),
                "latest_assessment_year": pd.to_datetime(
                    row["assessment date"], format="%d/%m/%Y", dayfirst=True
                ).year,
                "management_quality_score": get_mq_score(row.get("level", "N/A")),
            }
            for _, row in df.iterrows()
        ]
        
        return assessments, total
    
    def get_cp_assessments(
        self,
        page: int = 1,
        per_page: int = 10,
        sector: Optional[str] = None,
    ) -> Tuple[List[Dict], int]:
        """
        Get CP assessments with optional filtering and pagination.
        
        Args:
            page (int): Page number (1-based).
            per_page (int): Number of results per page.
            sector (Optional[str]): Filter by sector.
            
        Returns:
            Tuple[List[Dict], int]: List of CP assessment dictionaries and total count.
        """
        df = self.cp_df.copy()
        
        if sector:
            sector = self._sanitize_text(sector)
            df = df[df["sector"].str.lower() == sector]
        
        df['assessment_date_dt'] = pd.to_datetime(
            df['assessment date'], 
            format="%d/%m/%Y", 
            errors='coerce'
        )
        
        df['company_name_lower'] = df['company name'].str.lower()
        df = df.sort_values('assessment_date_dt', ascending=True).groupby('company_name_lower').tail(1)
        
        total = len(df)
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        df = df.iloc[start_idx:end_idx]
        
        def get_value_or_na(row, column):
            if column not in row:
                return "N/A"
            
            value = row.get(column)
            if pd.isna(value):
                return "N/A"
            
            # Ensure string values are properly sanitized
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return "N/A"
            
            return value
        
        assessments = []
        for _, row in df.iterrows():
            # Parse assessment date 
            assessment_year = None
            if pd.notna(row.get("assessment date")):
                try:
                    assessment_year = datetime.strptime(row["assessment date"], "%d/%m/%Y").year
                except (ValueError, TypeError):
                    assessment_year = None
            
            # Check for CP alignment for each target year
            cp_2025 = get_value_or_na(row, "carbon performance alignment 2025")
            cp_2027 = get_value_or_na(row, "carbon performance alignment 2027") 
            cp_2035 = get_value_or_na(row, "carbon performance alignment 2035")
            cp_2050 = get_value_or_na(row, "carbon performance alignment 2050")
            
            company_name = row["company name"]
            
            assessments.append({
                "company_id": normalize_company_id(company_name),
                "name": company_name, 
                "sector": row.get("sector", "N/A"),
                "geography": row.get("geography", "N/A"),
                "latest_assessment_year": assessment_year,
                "carbon_performance_2025": cp_2025,
                "carbon_performance_2027": cp_2027,
                "carbon_performance_2035": cp_2035,
                "carbon_performance_2050": cp_2050,
            })
        
        return assessments, total
    
    def get_company_history(self, company_id: str) -> Optional[List[Dict]]:
        """
        Get historical assessments for a specific company.
        
        Args:
            company_id (str): The company ID to look up.
            
        Returns:
            Optional[List[Dict]]: List of historical assessments or None if not found.
        """
        normalized_id = normalize_company_id(company_id)
        mask = (
            self.company_df["company name"].apply(normalize_company_id)
            == normalized_id
        )
        history = self.company_df[mask]
        
        if history.empty:
            return None
        
        return [
            {
                "company_id": normalized_id,
                "name": row["company name"],
                "sector": row.get("sector", "N/A"),
                "geography": row.get("geography", "N/A"),
                "latest_assessment_year": (
                    int(
                        datetime.strptime(
                            row.get("mq assessment date", "01/01/1900"),
                            "%d/%m/%Y",
                        ).year
                    )
                    if pd.notna(row.get("mq assessment date"))
                    else None
                ),
                "management_quality_score": row.get("level", "N/A"),
                "carbon_performance_alignment_2035": str(
                    row.get("carbon performance alignment 2035", "N/A")
                ),
                "emissions_trend": row.get(
                    "performance compared to previous year", "Unknown"
                ),
            }
            for _, row in history.iterrows()
        ]
    
    def compare_company_performance(
        self, company_id: str
    ) -> Optional[Dict]:
        """
        Compare a company's latest performance against the previous year.
        
        Args:
            company_id (str): The company ID to look up.
            
        Returns:
            Optional[Dict]: Performance comparison data or None if insufficient data.
        """
        normalized_id = normalize_company_id(company_id)
        
        cp_mask = (
            self.cp_df["company name"].apply(normalize_company_id)
            == normalized_id
        )
        cp_history = self.cp_df[cp_mask]
        
        mq_mask = (
            self.mq_df["company name"].apply(normalize_company_id)
            == normalized_id
        )
        mq_history = self.mq_df[mq_mask]
        
        if cp_history.empty or len(cp_history) < 2:
            available_years = []
            for date_str in cp_history["assessment date"].dropna():
                dt = datetime.strptime(date_str, "%d/%m/%Y") if date_str else None
                if dt:
                    available_years.append(dt.year)
            
            return {
                "company_id": normalized_id,
                "message": "Insufficient data for comparison",
                "available_assessment_years": available_years,
            }
        
        cp_history = cp_history.copy()
        cp_history["assessment_year"] = cp_history["assessment date"].apply(
            lambda x: (
                datetime.strptime(x, "%d/%m/%Y")
                if pd.notna(x)
                else None
            )
        )
        cp_history = cp_history.sort_values(by="assessment_year", ascending=False)
        cp_latest, cp_previous = cp_history.iloc[0], cp_history.iloc[1]
        
        mq_latest = None
        mq_previous = None
        
        if not mq_history.empty:
            mq_history = mq_history.copy()
            mq_history["assessment_date_obj"] = mq_history["assessment date"].apply(
                lambda x: (
                    datetime.strptime(x, "%d/%m/%Y")
                    if pd.notna(x)
                    else None
                )
            )
            mq_history = mq_history.sort_values(by="assessment_date_obj", ascending=False)
            
            if len(mq_history) >= 1:
                mq_latest = mq_history.iloc[0]
            if len(mq_history) >= 2:
                mq_previous = mq_history.iloc[1]
        
        def get_mq_score(level):
            if pd.isna(level) or level == "N/A":
                return "N/A"
            try:
                return str(float(level))
            except (ValueError, TypeError):
                if isinstance(level, str) and "STAR" in level:
                    return str(STAR_MAPPING.get(level, "N/A"))
                return str(level)
        
        return {
            "company_id": normalized_id,
            "current_year": cp_latest["assessment_year"].year,
            "previous_year": cp_previous["assessment_year"].year,
            "latest_mq_score": get_mq_score(mq_latest.get("level", "N/A")) if mq_latest is not None else "N/A",
            "previous_mq_score": get_mq_score(mq_previous.get("level", "N/A")) if mq_previous is not None else "N/A",
            "latest_mq_assessment_date": mq_latest.get("assessment date", "N/A") if mq_latest is not None else "N/A",
            "previous_mq_assessment_date": mq_previous.get("assessment date", "N/A") if mq_previous is not None else "N/A",
            "latest_cp_alignment": cp_latest.get("carbon performance alignment 2035", "N/A"),
            "previous_cp_alignment": cp_previous.get("carbon performance alignment 2035", "N/A"),
            "latest_assessment_date": cp_latest["assessment date"],
            "previous_assessment_date": cp_previous["assessment date"],
            "latest_cp_target": {
                "2025": cp_latest.get("carbon performance alignment 2025", "N/A"),
                "2027": cp_latest.get("carbon performance alignment 2027", "N/A"),
                "2035": cp_latest.get("carbon performance alignment 2035", "N/A"),
                "2050": cp_latest.get("carbon performance alignment 2050", "N/A")
            },
            "previous_cp_target": {
                "2025": cp_previous.get("carbon performance alignment 2025", "N/A"),
                "2027": cp_previous.get("carbon performance alignment 2027", "N/A"),
                "2035": cp_previous.get("carbon performance alignment 2035", "N/A"),
                "2050": cp_previous.get("carbon performance alignment 2050", "N/A")
            }
        } 