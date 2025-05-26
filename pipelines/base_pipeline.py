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
        self.validator = DataValidator()
        self.data = {}
        self.logger = logger

    def drop_tables(self):
        """Drop all tables in the database."""
        try:
            self.logger.info(f"Dropping {self.db_name} database tables...")
            self.db_manager.drop_all_tables()
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
            self.db_manager.create_tables()
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
            validation_results = self._validate_data()
            
            if validation_results['errors']:
                self.logger.error("Data validation failed with the following errors:")
                for error in validation_results['errors']:
                    self.logger.error(f"- {error}")
                raise ValueError("Data validation failed. Please check the errors above.")
            
            if validation_results['warnings']:
                self.logger.warning("Data validation completed with warnings:")
                for warning in validation_results['warnings']:
                    self.logger.warning(f"- {warning}")
            
            # Insert data into tables using database manager
            self.db_manager.bulk_insert(self.data)
            
            self.logger.info(f'{self.db_name} database population completed successfully.')

        except Exception as e:
            self.logger.error(f"Failed to populate {self.db_name} database: {str(e)}")
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


    