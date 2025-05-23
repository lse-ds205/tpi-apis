from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# get_db_connection() function= creates connection using SQL
def get_db_connection():
    """Creates and returns a new SQLAlchemy session."""
    load_dotenv()  # Load environment variables from .env file

    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')

    engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
    Session = sessionmaker(bind=engine)
    return Session()

# Reuse the engine you already created inside your function
def get_engine():
    load_dotenv()
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')
    return create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
