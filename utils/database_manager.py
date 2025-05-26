"""
Database Manager for TPI and ASCOR APIs

This module provides a centralized database management system that handles:
- Database connections and engine management
- Table creation from SQL files
- Data insertion and validation
- Query execution and data extraction
- Transaction management
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
logger = logging.getLogger(__name__)
logger.debug(f"Looking for .env file at: {env_path}")
if env_path.exists():
    logger.debug(".env file found")
    load_dotenv(env_path)
else:
    logger.warning(f".env file not found at {env_path}")

class DatabaseManager:
    """
    Centralized database manager for TPI and ASCOR databases.
    
    Provides methods for:
    - Database connection management
    - Table creation from SQL files
    - Data insertion and querying
    - Transaction management
    """
    
    def __init__(self, db_name: str):
        """
        Initialize the database manager.
        
        Args:
            db_name (str): Name of the database ('tpi_api' or 'ascor_api')
        """
        self.db_name = db_name
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.sql_dir = Path(__file__).parent.parent / "sql" / db_name.replace("_api", "")
        
    def _create_engine(self):
        """Create and return a SQLAlchemy engine."""
        # Use default values if environment variables are not set
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD', '')
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        
    
        
        db_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{self.db_name}'
        return create_engine(db_url)
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.
        
        Yields:
            Session: SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a DataFrame.
        
        Args:
            query (str): SQL query to execute
            params (Optional[Dict]): Query parameters
            
        Returns:
            pd.DataFrame: Query results
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                return pd.DataFrame(result.fetchall(), columns=result.keys())
        except SQLAlchemyError as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def execute_sql_file(self, file_path: Path) -> None:
        """
        Execute SQL commands from a file.
        
        Args:
            file_path (Path): Path to the SQL file
        """
        try:
            with open(file_path, 'r') as file:
                sql_content = file.read()
            
            with self.engine.connect() as conn:
                # Split by semicolon and execute each statement
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                for statement in statements:
                    conn.execute(text(statement))
                conn.commit()
                
            logger.info(f"Successfully executed SQL file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error executing SQL file {file_path}: {e}")
            raise
    
    def drop_all_tables(self) -> None:
        """Drop all tables in the database."""
        try:
            logger.info(f"Dropping all tables in {self.db_name}...")
            
            with self.engine.connect() as conn:
                # Get all table names
                tables_query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
                result = conn.execute(text(tables_query))
                tables = [row[0] for row in result.fetchall()]
                
                if not tables:
                    logger.info(f"No tables found in {self.db_name}")
                    return
                
                # Drop tables with CASCADE to handle dependencies
                for table in tables:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                
                conn.commit()
                logger.info(f"Successfully dropped {len(tables)} tables from {self.db_name}")
                
        except SQLAlchemyError as e:
            logger.error(f"Error dropping tables: {e}")
            raise
    
    def create_tables(self) -> None:
        """Create all tables by executing SQL files in the init directory."""
        try:
            init_dir = self.sql_dir / "init"
            if not init_dir.exists():
                raise FileNotFoundError(f"Init directory not found: {init_dir}")
            
            logger.info(f"Creating tables for {self.db_name}...")
            
            # Execute SQL files in alphabetical order
            sql_files = sorted(init_dir.glob("*.sql"))
            if not sql_files:
                raise FileNotFoundError(f"No SQL files found in {init_dir}")
            
            for sql_file in sql_files:
                logger.info(f"Executing {sql_file.name}...")
                self.execute_sql_file(sql_file)
            
            logger.info(f"Successfully created all tables for {self.db_name}")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def insert_dataframe(self, df: pd.DataFrame, table_name: str, 
                        if_exists: str = 'append', index: bool = False) -> None:
        """
        Insert a DataFrame into a database table.
        
        Args:
            df (pd.DataFrame): DataFrame to insert
            table_name (str): Target table name
            if_exists (str): How to behave if table exists ('fail', 'replace', 'append')
            index (bool): Whether to write DataFrame index as a column
        """
        try:
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=index)
            logger.info(f"Successfully inserted {len(df)} rows into {table_name}")
            
        except SQLAlchemyError as e:
            logger.error(f"Error inserting data into {table_name}: {e}")
            raise
    
    def bulk_insert(self, data_dict: Dict[str, pd.DataFrame]) -> None:
        """
        Insert multiple DataFrames into their respective tables.
        
        Args:
            data_dict (Dict[str, pd.DataFrame]): Dictionary mapping table names to DataFrames
        """
        try:
            with self.engine.begin() as conn:
                for table_name, df in data_dict.items():
                    df.to_sql(table_name, conn, if_exists='append', index=False)
                    logger.info(f"Inserted {len(df)} rows into {table_name}")
            
            logger.info(f"Successfully completed bulk insert for {len(data_dict)} tables")
            
        except SQLAlchemyError as e:
            logger.error(f"Error during bulk insert: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            table_name (str): Name of the table to check
            
        Returns:
            bool: True if table exists, False otherwise
        """
        try:
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                )
            """
            result = self.execute_query(query, {"table_name": table_name})
            return result.iloc[0, 0] if not result.empty else False
            
        except SQLAlchemyError as e:
            logger.error(f"Error checking if table exists: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """
        Get information about a table's columns.
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            pd.DataFrame: Table column information
        """
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :table_name
            ORDER BY ordinal_position
        """
        return self.execute_query(query, {"table_name": table_name})
    
    def get_row_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table.
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            int: Number of rows in the table
        """
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = self.execute_query(query)
        return result.iloc[0, 0] if not result.empty else 0
    
    def truncate_table(self, table_name: str) -> None:
        """
        Truncate a table (remove all rows).
        
        Args:
            table_name (str): Name of the table to truncate
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
                conn.commit()
            logger.info(f"Successfully truncated table {table_name}")
            
        except SQLAlchemyError as e:
            logger.error(f"Error truncating table {table_name}: {e}")
            raise
    
    def close(self) -> None:
        """Close the database engine."""
        if self.engine:
            self.engine.dispose()
            logger.info(f"Closed database connection for {self.db_name}")


class DatabaseManagerFactory:
    """Factory class for creating database managers."""
    
    _instances: Dict[str, DatabaseManager] = {}
    
    @classmethod
    def get_manager(cls, db_name: str) -> DatabaseManager:
        """
        Get or create a database manager instance.
        
        Args:
            db_name (str): Database name
            
        Returns:
            DatabaseManager: Database manager instance
        """
        if db_name not in cls._instances:
            cls._instances[db_name] = DatabaseManager(db_name)
        return cls._instances[db_name]
    
    @classmethod
    def close_all(cls) -> None:
        """Close all database manager instances."""
        for manager in cls._instances.values():
            manager.close()
        cls._instances.clear() 