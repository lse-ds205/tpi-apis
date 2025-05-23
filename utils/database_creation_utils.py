from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables once globally
load_dotenv()

# Create a reusable function to construct DB URL
def construct_db_url(db_name=None):
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = db_name or os.getenv('DB_NAME')  # use passed name or fallback
    return f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

# Create a SQLAlchemy session for a given database
def get_db_connection(db_name=None):
    """Creates and returns a new SQLAlchemy session for a given database."""
    engine = create_engine(construct_db_url(db_name))
    Session = sessionmaker(bind=engine)
    return Session()

# Get an engine object for a given database
def get_engine(db_name=None):
    """Returns a SQLAlchemy engine for a given database."""
    return create_engine(construct_db_url(db_name))
