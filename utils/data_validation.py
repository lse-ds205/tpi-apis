import pandas as pd
import logging
from typing import Dict, List, Tuple
from datetime import datetime
import re
from utils.database_manager import DatabaseManagerFactory

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self, db_name: str):
        self.validation_results = {
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        self.db_manager = DatabaseManagerFactory.get_manager(db_name)
        self.current_pipeline_run_id = None

    def set_pipeline_run_id(self, execution_id: int):
        """Set the current pipeline run ID for validation logging."""
        self.current_pipeline_run_id = execution_id

    def _log_validation_issue(self, table_name: str, message: str, severity: str, 
                            affected_rows: int = None, validation_rule: str = None):
        """Log a validation issue to the audit_log table."""
        if not self.current_pipeline_run_id:
            logger.warning("No pipeline run ID set, skipping validation log")
            return

        try:
            # Format the validation message
            process = f"Validation - {table_name}"
            status = 'VALIDATION_ERROR' if severity in ['critical', 'error'] else 'VALIDATION_WARNING'
            notes = f"Rule: {validation_rule}\nMessage: {message}"
            if affected_rows is not None:
                notes += f"\nAffected Rows: {affected_rows}"

            # Log to audit_log
            self.db_manager.log_execution(
                process=process,
                status=status,
                notes=notes,
                table_name=table_name,
                rows_inserted=affected_rows
            )
        except Exception as e:
            logger.error(f"Failed to log validation issue: {str(e)}")

    def validate_tpi_data(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """Validate TPI data across all tables."""
        logger.info("Starting TPI data validation...")
        
        # Validate company data
        self._validate_company_data(data_dict.get('company', pd.DataFrame()))
        
        # Validate company answers
        self._validate_company_answers(data_dict.get('company_answer', pd.DataFrame()))
        
        # Validate MQ assessments
        self._validate_mq_assessments(data_dict.get('mq_assessment', pd.DataFrame()))
        
        # Validate CP assessments
        self._validate_cp_assessments(
            data_dict.get('cp_assessment', pd.DataFrame()),
            data_dict.get('cp_alignment', pd.DataFrame()),
            data_dict.get('cp_projection', pd.DataFrame())
        )
        
        # Validate sector benchmarks
        self._validate_sector_benchmarks(
            data_dict.get('sector_benchmark', pd.DataFrame()),
            data_dict.get('benchmark_projection', pd.DataFrame())
        )
        
        return self.validation_results

    def validate_ascor_data(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """Validate ASCOR data across all tables."""
        logger.info("Starting ASCOR data validation...")
        
        # Validate country data
        self._validate_country_data(data_dict.get('country', pd.DataFrame()))
        
        # Validate benchmarks
        self._validate_ascor_benchmarks(
            data_dict.get('benchmarks', pd.DataFrame()),
            data_dict.get('benchmark_values', pd.DataFrame())
        )
        
        # Validate assessment elements
        self._validate_assessment_elements(data_dict.get('assessment_elements', pd.DataFrame()))
        
        # Validate assessment results
        self._validate_assessment_results(data_dict.get('assessment_results', pd.DataFrame()))
        
        # Validate assessment trends
        self._validate_assessment_trends(
            data_dict.get('assessment_trends', pd.DataFrame()),
            data_dict.get('trend_values', pd.DataFrame()),
            data_dict.get('value_per_year', pd.DataFrame())
        )
        
        return self.validation_results

    def _validate_company_data(self, df: pd.DataFrame) -> None:
        """Validate company data."""
        if df.empty:
            error_msg = "Company data is empty"
            self.validation_results['errors'].append(error_msg)
            self._log_validation_issue('company', error_msg, 'critical')
            return

        # Check required columns
        required_cols = ['company_name', 'version', 'geography', 'sector_name']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            error_msg = f"Missing required columns in company data: {missing_cols}"
            self.validation_results['errors'].append(error_msg)
            self._log_validation_issue('company', error_msg, 'error', validation_rule='required_columns')

        # Check for duplicate company-version combinations
        duplicates = df.duplicated(subset=['company_name', 'version'], keep=False)
        if duplicates.any():
            error_msg = f"Found {duplicates.sum()} duplicate company-version combinations"
            self.validation_results['errors'].append(error_msg)
            self._log_validation_issue('company', error_msg, 'error', 
                                     affected_rows=duplicates.sum(),
                                     validation_rule='unique_constraint')

        # Check for missing values in required fields
        for col in required_cols:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                warning_msg = f"Found {null_count} null values in {col}"
                self.validation_results['warnings'].append(warning_msg)
                self._log_validation_issue('company', warning_msg, 'warning',
                                         affected_rows=null_count,
                                         validation_rule='null_check')

        # Validate version format
        invalid_versions = df[~df['version'].str.match(r'^\d+\.\d+$')]
        if not invalid_versions.empty:
            error_msg = f"Found {len(invalid_versions)} invalid version formats"
            self.validation_results['errors'].append(error_msg)
            self._log_validation_issue('company', error_msg, 'error',
                                     affected_rows=len(invalid_versions),
                                     validation_rule='version_format')

    def _validate_company_answers(self, df: pd.DataFrame) -> None:
        """Validate company answers data."""
        if df.empty:
            self.validation_results['errors'].append("Company answers data is empty")
            return

        # Check required columns
        required_cols = ['question_code', 'company_name', 'version', 'response']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.validation_results['errors'].append(
                f"Missing required columns in company answers: {missing_cols}"
            )

        # Check for null responses
        null_responses = df['response'].isnull().sum()
        if null_responses > 0:
            self.validation_results['warnings'].append(
                f"Found {null_responses} null responses"
            )

        # Validate question code format
        invalid_codes = df[~df['question_code'].str.match(r'^[A-Za-z0-9.]+$')]
        if not invalid_codes.empty:
            self.validation_results['errors'].append(
                f"Found {len(invalid_codes)} invalid question codes"
            )

    def _validate_mq_assessments(self, df: pd.DataFrame) -> None:
        """Validate MQ assessment data."""
        if df.empty:
            self.validation_results['errors'].append("MQ assessment data is empty")
            return

        # Check required columns
        required_cols = ['assessment_date', 'company_name', 'version', 'tpi_cycle']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.validation_results['errors'].append(
                f"Missing required columns in MQ assessments: {missing_cols}"
            )

        # Validate dates
        if 'assessment_date' in df.columns:
            invalid_dates = df[~pd.to_datetime(df['assessment_date'], errors='coerce').notnull()]
            if not invalid_dates.empty:
                self.validation_results['errors'].append(
                    f"Found {len(invalid_dates)} invalid assessment dates"
                )

        # Validate TPI cycle values
        if 'tpi_cycle' in df.columns:
            invalid_cycles = df[~df['tpi_cycle'].between(1, 5)]
            if not invalid_cycles.empty:
                self.validation_results['errors'].append(
                    f"Found {len(invalid_cycles)} invalid TPI cycle values"
                )

    def _validate_cp_assessments(
        self,
        assessment_df: pd.DataFrame,
        alignment_df: pd.DataFrame,
        projection_df: pd.DataFrame
    ) -> None:
        """Validate CP assessment data and related tables."""
        if assessment_df.empty:
            self.validation_results['errors'].append("CP assessment data is empty")
            return

        # Validate assessment data
        required_cols = ['assessment_date', 'company_name', 'version', 'is_regional']
        missing_cols = [col for col in required_cols if col not in assessment_df.columns]
        if missing_cols:
            self.validation_results['errors'].append(
                f"Missing required columns in CP assessments: {missing_cols}"
            )

        # Validate alignment data
        if not alignment_df.empty:
            required_cols = ['cp_alignment_year', 'cp_alignment_value', 'assessment_date', 'company_name']
            missing_cols = [col for col in required_cols if col not in alignment_df.columns]
            if missing_cols:
                self.validation_results['errors'].append(
                    f"Missing required columns in CP alignments: {missing_cols}"
                )

            # Validate alignment years
            if 'cp_alignment_year' in alignment_df.columns:
                invalid_years = alignment_df[~alignment_df['cp_alignment_year'].between(2000, 2100)]
                if not invalid_years.empty:
                    self.validation_results['errors'].append(
                        f"Found {len(invalid_years)} invalid alignment years"
                    )

        # Validate projection data
        if not projection_df.empty:
            required_cols = ['cp_projection_year', 'cp_projection_value', 'assessment_date', 'company_name']
            missing_cols = [col for col in required_cols if col not in projection_df.columns]
            if missing_cols:
                self.validation_results['errors'].append(
                    f"Missing required columns in CP projections: {missing_cols}"
                )

            # Validate projection years
            if 'cp_projection_year' in projection_df.columns:
                invalid_years = projection_df[~projection_df['cp_projection_year'].between(2000, 2100)]
                if not invalid_years.empty:
                    self.validation_results['errors'].append(
                        f"Found {len(invalid_years)} invalid projection years"
                    )

    def _validate_sector_benchmarks(
        self,
        benchmark_df: pd.DataFrame,
        projection_df: pd.DataFrame
    ) -> None:
        """Validate sector benchmark data and projections."""
        if benchmark_df.empty:
            self.validation_results['errors'].append("Sector benchmark data is empty")
            return

        # Validate benchmark data
        required_cols = ['benchmark_id', 'sector_name', 'scenario_name']
        missing_cols = [col for col in required_cols if col not in benchmark_df.columns]
        if missing_cols:
            self.validation_results['errors'].append(
                f"Missing required columns in sector benchmarks: {missing_cols}"
            )

        # Validate projections
        if not projection_df.empty:
            required_cols = ['benchmark_projection_year', 'benchmark_projection_attribute']
            missing_cols = [col for col in required_cols if col not in projection_df.columns]
            if missing_cols:
                self.validation_results['errors'].append(
                    f"Missing required columns in benchmark projections: {missing_cols}"
                )

            # Validate projection years
            if 'benchmark_projection_year' in projection_df.columns:
                invalid_years = projection_df[~projection_df['benchmark_projection_year'].between(2000, 2100)]
                if not invalid_years.empty:
                    self.validation_results['errors'].append(
                        f"Found {len(invalid_years)} invalid benchmark projection years"
                    )

    def _validate_country_data(self, df: pd.DataFrame) -> None:
        """Validate country data."""
        if df.empty:
            self.validation_results['errors'].append("Country data is empty")
            return

        # Check required columns
        required_cols = ['country_name', 'iso']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.validation_results['errors'].append(
                f"Missing required columns in country data: {missing_cols}"
            )

        # Validate ISO codes
        if 'iso' in df.columns:
            invalid_iso = df[~df['iso'].str.match(r'^[A-Z]{2,3}$')]
            if not invalid_iso.empty:
                self.validation_results['errors'].append(
                    f"Found {len(invalid_iso)} invalid ISO codes"
                )

    def _validate_ascor_benchmarks(
        self,
        benchmark_df: pd.DataFrame,
        values_df: pd.DataFrame
    ) -> None:
        """Validate ASCOR benchmark data and values."""
        if benchmark_df.empty:
            self.validation_results['errors'].append("ASCOR benchmark data is empty")
            return

        # Validate benchmark data
        required_cols = ['benchmark_id', 'publication_date', 'emissions_metric']
        missing_cols = [col for col in required_cols if col not in benchmark_df.columns]
        if missing_cols:
            self.validation_results['errors'].append(
                f"Missing required columns in ASCOR benchmarks: {missing_cols}"
            )

        # Validate benchmark values
        if not values_df.empty:
            required_cols = ['year', 'benchmark_id', 'value']
            missing_cols = [col for col in required_cols if col not in values_df.columns]
            if missing_cols:
                self.validation_results['errors'].append(
                    f"Missing required columns in benchmark values: {missing_cols}"
                )

            # Validate years
            if 'year' in values_df.columns:
                invalid_years = values_df[~values_df['year'].between(2000, 2100)]
                if not invalid_years.empty:
                    self.validation_results['errors'].append(
                        f"Found {len(invalid_years)} invalid benchmark value years"
                    )

    def _validate_assessment_elements(self, df: pd.DataFrame) -> None:
        """Validate assessment elements data."""
        if df.empty:
            self.validation_results['errors'].append("Assessment elements data is empty")
            return

        # Check required columns
        required_cols = ['code', 'text', 'response_type', 'type']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.validation_results['errors'].append(
                f"Missing required columns in assessment elements: {missing_cols}"
            )

        # Validate codes
        if 'code' in df.columns:
            invalid_codes = df[~df['code'].str.match(r'^[A-Za-z0-9.]+$')]
            if not invalid_codes.empty:
                self.validation_results['errors'].append(
                    f"Found {len(invalid_codes)} invalid assessment element codes"
                )

    def _validate_assessment_results(self, df: pd.DataFrame) -> None:
        """Validate assessment results data."""
        if df.empty:
            self.validation_results['errors'].append("Assessment results data is empty")
            return

        # Check required columns
        required_cols = ['assessment_id', 'code', 'assessment_date', 'country_name']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.validation_results['errors'].append(
                f"Missing required columns in assessment results: {missing_cols}"
            )

        # Validate dates
        if 'assessment_date' in df.columns:
            invalid_dates = df[~pd.to_datetime(df['assessment_date'], errors='coerce').notnull()]
            if not invalid_dates.empty:
                self.validation_results['errors'].append(
                    f"Found {len(invalid_dates)} invalid assessment dates"
                )

    def _validate_assessment_trends(
        self,
        trends_df: pd.DataFrame,
        values_df: pd.DataFrame,
        yearly_df: pd.DataFrame
    ) -> None:
        """Validate assessment trends and related data."""
        if trends_df.empty:
            self.validation_results['errors'].append("Assessment trends data is empty")
            return

        # Validate trends data
        required_cols = ['trend_id', 'country_name', 'emissions_metric']
        missing_cols = [col for col in required_cols if col not in trends_df.columns]
        if missing_cols:
            self.validation_results['errors'].append(
                f"Missing required columns in assessment trends: {missing_cols}"
            )

        # Validate trend values
        if not values_df.empty:
            required_cols = ['trend_id', 'country_name', 'year', 'value']
            missing_cols = [col for col in required_cols if col not in values_df.columns]
            if missing_cols:
                self.validation_results['errors'].append(
                    f"Missing required columns in trend values: {missing_cols}"
                )

        # Validate yearly values
        if not yearly_df.empty:
            required_cols = ['year', 'value', 'trend_id', 'country_name']
            missing_cols = [col for col in required_cols if col not in yearly_df.columns]
            if missing_cols:
                self.validation_results['errors'].append(
                    f"Missing required columns in yearly values: {missing_cols}"
                )

    def get_validation_summary(self) -> Dict:
        """Get a summary of validation results."""
        return {
            'error_count': len(self.validation_results['errors']),
            'warning_count': len(self.validation_results['warnings']),
            'errors': self.validation_results['errors'],
            'warnings': self.validation_results['warnings'],
            'stats': self.validation_results['stats']
        }

    def clear_results(self) -> None:
        """Clear validation results."""
        self.validation_results = {
            'errors': [],
            'warnings': [],
            'stats': {}
        } 