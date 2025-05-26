from sqlalchemy import text
from utils.database_creation_utils import get_engine
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
        self.engine = get_engine(db_name)
        self.validator = DataValidator()
        self.data = {}
        self.logger = logger

    def drop_tables(self):
        """Drop all tables in the database."""
        try:
            self.logger.info(f"Dropping {self.db_name} database tables...")
            
            # Check if tables exist before dropping
            with self.engine.connect() as conn:
                tables = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)).fetchall()
                
                if not tables:
                    self.logger.info(f"No {self.db_name} tables found to drop.")
                    return
                
                # Drop tables using CASCADE to handle dependencies
                for table in tables:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table[0]}" CASCADE'))
                conn.commit()
                
                self.logger.info(f"Successfully dropped {len(tables)} {self.db_name} tables.")
                
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
            # Ensure public schema exists and is set as search path
            with self.engine.connect() as conn:
                # Create schema if it doesn't exist
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS public;"))
                
                # Set search path
                conn.execute(text("SET search_path TO public;"))
                conn.commit()
            self.logger.info(f"{self.db_name}: public schema ensured and search path set.")

            # Get table creation SQL
            tables = self._get_table_creation_sql()

            # Create tables one by one for better error handling
            with self.engine.connect() as conn:
                for i, table_sql in enumerate(tables, 1):
                    try:
                        conn.execute(text(table_sql))
                        self.logger.debug(f"Created {self.db_name} table {i}/{len(tables)}")
                    except Exception as e:
                        self.logger.error(f"Failed to create {self.db_name} table {i}: {str(e)}")
                        raise
                conn.commit()
            self.logger.info(f"{self.db_name} tables created successfully.")

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
            
            # Insert data into tables
            self._insert_data()
            
            self.logger.info(f'{self.db_name} database population completed successfully.')

        except Exception as e:
            self.logger.error(f"Failed to populate {self.db_name} database: {str(e)}")
            raise

    @abstractmethod
    def _get_table_creation_sql(self) -> list:
        """Get SQL statements for creating tables.
        
        Returns:
            list: List of SQL statements for creating tables
        """
        pass

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

    def _insert_data(self):
        """Insert processed data into tables."""
        try:
            # Insert data into tables
            for table_name, df in self.data.items():
                if table_name not in self._get_primary_tables():  # Skip primary tables as they're already inserted
                    df.to_sql(table_name, self.engine, if_exists='append', index=False)
                    self.logger.info(f'{self.db_name}: {table_name} table populated.')
        except Exception as e:
            self.logger.error(f"Failed to insert data into {self.db_name} tables: {str(e)}")
            raise

    @abstractmethod
    def _get_primary_tables(self) -> list:
        """Get list of primary tables that should be inserted first.
        
        Returns:
            list: List of primary table names
        """
        pass
    