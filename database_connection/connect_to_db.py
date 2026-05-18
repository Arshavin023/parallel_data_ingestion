import os
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv  # <-- Add this import

# Load variables from .env file into os.environ if it exists
load_dotenv()

def connect(database_name):
    # Fallback to standard environment variables if explicitly passed to the container
    db_host = os.environ.get("DB_HOST", "localhost")
    db_user = os.environ.get("DB_USER", "lamisplus")
    db_password = os.environ.get("DB_PASSWORD", "your_default_password")
    db_port = os.environ.get("DB_PORT", "5432")
    
    # Dynamically select which database to point to based on your current application logic
    # (e.g., 'filedb' or 'lamisplus_staging_dwh')
    db_name = os.environ.get(f"DB_NAME_{database_name.upper()}", database_name)

    # 1. Establish Psycopg2 Connection
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=db_port
    )
    
    # 2. Establish SQLAlchemy Engine
    connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(connection_string)
    
    return conn, engine

# connect("filedb")  # Example usage, you can replace "filedb" with "lamisplus_staging_dwh" as needed
# print("Successfully connected to the database and created SQLAlchemy engine.")