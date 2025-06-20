from sqlalchemy import text
from utils.database_manager import DatabaseManagerFactory
import logging
import pandas as pd
import os
from utils.data_validation import DataValidator
import re
from datetime import datetime
from abc import ABC, abstractmethod

class BasePipeline(ABC):
    """Base class for database pipelines."""
    
    def __init__(self, db_name: str, data_dir: str, logger: logging.Logger):
        """Initialize the pipeline.
        
        Args:
            db_name (str): Name of the database
            data_dir (str): Path to the data directory
            logger (logging.Logger): Logger instance to use
        """
        self.db_name = db_name
        self.data_dir = data_dir
        self.db_manager = DatabaseManagerFactory.get_manager(db_name)
        self.validator = DataValidator(db_name)
        self.data = {}
        self.logger = logger

    def log_pipeline_execution(self, process: str = None, status: str = 'COMPLETED', notes: str = None,
                             table_name: str = None, source_file: str = None, rows_inserted: int = None):
        """Log pipeline execution to the database.
        
        Args:
            process (str, optional): Name of the process being executed. If None, uses default pipeline name.
            status (str): Execution status (default: 'COMPLETED')
            notes (str, optional): Optional notes about the execution
            table_name (str, optional): Name of the table being modified
            source_file (str, optional): Path to the source file
            rows_inserted (int, optional): Number of rows inserted
        """
        try:
            # Use provided process name or create a default one
            if process is None:
                process = f"TPI Pipeline - {self.db_name}"
            
            self.logger.info(f"Attempting to log pipeline execution with status: {status}")
            execution_id = self.db_manager.log_execution(
                process=process,
                status=status,
                notes=notes,
                table_name=table_name,
                source_file=source_file,
                rows_inserted=rows_inserted
            )
            self.logger.info(f"Successfully logged pipeline execution with ID: {execution_id}")
        except Exception as e:
            self.logger.error(f"Failed to log pipeline execution: {str(e)}")
            raise

    def drop_tables(self):
        """Drop all tables in the database except audit_log."""
        try:
            self.logger.info(f"Dropping {self.db_name} database tables (excluding audit_log)...")
            self.db_manager.drop_all_tables(exclude_tables=['audit_log'])
        except Exception as e:
            self.logger.error(f"Failed to drop {self.db_name} tables: {str(e)}")
            # Add some context to the error
            if "connection" in str(e).lower():
                self.logger.error("Database connection failed. Please check your database settings.")
            elif "permission" in str(e).lower():
                self.logger.error("Permission denied. Please check your database user permissions.")
            raise

    def create_tables(self):
        """Create all tables in the database."""
        try:
            self.logger.info(f"Creating {self.db_name} tables...")
            self.db_manager.create_all_tables()
            # Log pipeline start after tables are created
            self.log_pipeline_execution(
                process=f"PIPELINE_START - {self.db_name}",
                status='STARTED'
            )
        except Exception as e:
            self.logger.error(f"Failed to create {self.db_name} tables: {str(e)}")
            # Add some context to the error
            if "connection" in str(e).lower():
                self.logger.error("Database connection failed. Please check your database settings.")
            elif "permission" in str(e).lower():
                self.logger.error("Permission denied. Please check your database user permissions.")
            raise

    def populate_tables(self):
        """Populate tables with data."""
        try:
            self.logger.info(f'Populating {self.db_name} tables...')
            
            # Process and validate data
            self._process_data()
            
            # Log validation start
            execution_id = self.log_pipeline_execution(
                process=f"VALIDATION_START - {self.db_name}",
                status='STARTED',
                notes="Starting data validation process"
            )
            
            # Set pipeline run ID for validation logging
            self.validator.set_pipeline_run_id(execution_id)
            
            # Run validation
            self.logger.info("Running data validation...")
            validation_results = self._validate_data()
            
            if validation_results['errors']:
                self.logger.error("Data validation failed with the following errors:")
                for error in validation_results['errors']:
                    self.logger.error(f"- {error}")
                self.log_pipeline_execution(
                    process=f"VALIDATION_FINISH - {self.db_name}",
                    status='VALIDATION_FAILED',
                    notes=f"Validation errors: {', '.join(validation_results['errors'])}"
                )
                raise ValueError("Data validation failed. Please check the errors above.")
            
            if validation_results['warnings']:
                self.logger.warning("Data validation completed with warnings:")
                for warning in validation_results['warnings']:
                    self.logger.warning(f"- {warning}")
                self.log_pipeline_execution(
                    process=f"VALIDATION_FINISH - {self.db_name}",
                    status='VALIDATION_WARNINGS',
                    notes=f"Validation warnings: {', '.join(validation_results['warnings'])}"
                )
            else:
                self.log_pipeline_execution(
                    process=f"VALIDATION_FINISH - {self.db_name}",
                    status='VALIDATION_PASSED',
                    notes="All validation checks passed successfully"
                )
            
            # Get source files from the pipeline
            source_files = self._get_source_files()
            
            # Insert data into tables using database manager
            for table_name, df in self.data.items():
                source_file = source_files.get(table_name) if source_files else None
                self.db_manager.insert_dataframe(df, table_name, source_file=source_file)
            
            # Log pipeline finish after successful data insertion
            self.log_pipeline_execution(
                process=f"PIPELINE_FINISH - {self.db_name}",
                status='COMPLETED_WITH_WARNINGS' if validation_results['warnings'] else 'COMPLETED',
                notes=f"Validation warnings: {', '.join(validation_results['warnings'])}" if validation_results['warnings'] else None
            )
            
            self.logger.info(f'{self.db_name} database population completed successfully.')
            
        except Exception as e:
            self.logger.error(f"Failed to populate {self.db_name} tables: {str(e)}")
            # Log pipeline failure
            self.log_pipeline_execution(
                process=f"PIPELINE_FINISH - {self.db_name}",
                status='FAILED',
                notes=str(e)
            )
            raise

    @abstractmethod
    def _process_data(self):
        """Process data from files into dataframes."""
        pass

    @abstractmethod
    def _validate_data(self) -> dict:
        """Validate the processed data.
        
        Returns:
            dict: Dictionary containing validation results with 'errors' and 'warnings' keys
        """
        pass


    