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
from typing import Dict, List, Optional, Any, Union, Type
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from dotenv import load_dotenv
from models.sqlalchemymodels import AscorBase, TpiBase

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
        
        # Set the appropriate base for model operations
        self.Base = TpiBase if db_name == 'tpi_api' else AscorBase
        
    def _create_engine(self):
        """Create and return a SQLAlchemy engine."""
        # Use default values if environment variables are not set
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD', '')
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        
        if not all([db_user, db_host, db_port]):
            raise ValueError("Missing required database configuration. Please check your .env file.")
        
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
    
    def create_all_tables(self) -> None:
        """Create all tables defined in the SQLAlchemy models."""
        try:
            self.Base.metadata.create_all(self.engine)
            logger.info(f"Successfully created all tables for {self.db_name}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def drop_all_tables(self, exclude_tables: List[str] = None) -> None:
        """
        Drop all tables in the database.
        
        Args:
            exclude_tables (List[str], optional): List of table names to exclude from dropping
        """
        try:
            logger.info(f"Dropping all tables in {self.db_name}...")
            
            # Get all table names from the metadata
            tables = self.Base.metadata.tables.keys()
            
            # Filter out excluded tables
            if exclude_tables:
                tables = [table for table in tables if table not in exclude_tables]
                logger.info(f"Excluding tables from drop: {', '.join(exclude_tables)}")
            
            # Drop tables with CASCADE to handle dependencies
            with self.engine.connect() as conn:
                for table in tables:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                conn.commit()
            
            logger.info(f"Successfully dropped {len(tables)} tables from {self.db_name}")
            
        except SQLAlchemyError as e:
            logger.error(f"Error dropping tables: {e}")
            raise
    
    def insert_model(self, model_instance: Any) -> None:
        """
        Insert a single model instance into the database.
        
        Args:
            model_instance: SQLAlchemy model instance to insert
        """
        try:
            with self.get_session() as session:
                session.add(model_instance)
                session.commit()
                logger.info(f"Successfully inserted {model_instance.__class__.__name__} instance")
        except SQLAlchemyError as e:
            logger.error(f"Error inserting model instance: {e}")
            raise
    
    def bulk_insert_models(self, model_instances: List[Any]) -> None:
        """
        Insert multiple model instances into the database.
        
        Args:
            model_instances: List of SQLAlchemy model instances to insert
        """
        if not model_instances:
            return
            
        try:
            with self.get_session() as session:
                session.bulk_save_objects(model_instances)
                session.commit()
                logger.info(f"Successfully inserted {len(model_instances)} {model_instances[0].__class__.__name__} instances")
        except SQLAlchemyError as e:
            logger.error(f"Error bulk inserting model instances: {e}")
            raise
    
    def query_model(self, model_class: Type, **filters) -> List[Any]:
        """
        Query the database using SQLAlchemy model.
        
        Args:
            model_class: SQLAlchemy model class to query
            **filters: Filter conditions to apply
            
        Returns:
            List[Any]: List of model instances matching the query
        """
        try:
            with self.get_session() as session:
                query = session.query(model_class)
                for key, value in filters.items():
                    query = query.filter(getattr(model_class, key) == value)
                return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error querying model: {e}")
            raise
    
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
    
    def insert_dataframe(self, df: pd.DataFrame, table_name: str, 
                        source_file: str = None,
                        if_exists: str = 'append', index: bool = False) -> None:
        """
        Insert a DataFrame into a database table and log the insertion.
        
        Args:
            df (pd.DataFrame): DataFrame to insert
            table_name (str): Target table name
            source_file (str, optional): Path to the source file
            if_exists (str): How to behave if table exists ('fail', 'replace', 'append')
            index (bool): Whether to write DataFrame index as a column
        """
        try:
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=index)
            rows_inserted = len(df)
            logger.info(f"Successfully inserted {rows_inserted} rows into {table_name}")
            
            # Log the insertion in audit_log
            self.log_execution(
                process=f"Data Insertion - {table_name}",
                status='COMPLETED',
                table_name=table_name,
                source_file=str(source_file) if source_file else None,
                rows_inserted=rows_inserted
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Error inserting data into {table_name}: {e}")
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
    
    def execute_sql_template(self, file_path: Union[str, Path], params: Optional[Dict] = None, 
                           where_clause: str = "") -> pd.DataFrame:
        """
        Execute a SQL template file with parameter substitution.
        
        Args:
            file_path (Union[str, Path]): Path to the SQL template file
            params (Optional[Dict]): Query parameters
            where_clause (str): WHERE clause to substitute in the template
            
        Returns:
            pd.DataFrame: Query results
        """
        try:
            # Convert to Path object if string
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            # Read the SQL template
            with open(file_path, 'r') as file:
                sql_template = file.read()
            
            # Replace WHERE clause placeholder
            if "-- WHERE_CLAUSE_PLACEHOLDER" in sql_template:
                where_clause_full = f"WHERE 1=1 {where_clause}" if where_clause else "WHERE 1=1"
                sql_query = sql_template.replace("-- WHERE_CLAUSE_PLACEHOLDER", where_clause_full)
            else:
                # Handle other placeholder formats
                sql_query = sql_template.replace("{{where_clause}}", where_clause)
            
            # Execute the query
            return self.execute_query(sql_query, params or {})
            
        except Exception as e:
            logger.error(f"Error executing SQL template {file_path}: {e}")
            raise
    
    def log_execution(self, process: str, status: str = 'COMPLETED', notes: str = None,
                     table_name: str = None, source_file: str = None, rows_inserted: int = None) -> int:
        """
        Log an execution to the audit_log table.
        
        Args:
            process (str): Name of the process being executed
            status (str): Execution status (default: 'COMPLETED')
            notes (str, optional): Additional notes about the execution
            table_name (str, optional): Name of the table being modified
            source_file (str, optional): Path to the source file
            rows_inserted (int, optional): Number of rows inserted
            
        Returns:
            int: The execution_id of the created log entry
        """
        try:
            # Convert None to empty string for notes
            notes = notes if notes is not None else ''
            
            # Ensure source_file is stored as string
            source_file = str(source_file) if source_file else None
            
            query = """
                INSERT INTO audit_log 
                (process, execution_status, execution_notes, table_name, source_file, rows_inserted)
                VALUES (:process, :status, :notes, :table_name, :source_file, :rows_inserted)
                RETURNING execution_id
            """
            
            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(
                        text(query),
                        {
                            "process": process,
                            "status": status,
                            "notes": notes,
                            "table_name": table_name,
                            "source_file": source_file,
                            "rows_inserted": rows_inserted
                        }
                    )
                    execution_id = result.scalar()
                    logger.info(f"Successfully logged execution with ID: {execution_id}")
                    return execution_id
                    
        except SQLAlchemyError as e:
            logger.error(f"Failed to log execution: {e}")
            raise

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