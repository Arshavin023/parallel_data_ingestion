import os
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load variables from .env file into os.environ if it exists
load_dotenv()


def connect(database_name):
    """
    Connect to a PostgreSQL database on the local server.

    Supported database_name values:
      - "server_a"  → maps to DB_NAME_SERVER_A  (default: lamisplus_demo_db)
      - "server_b"  → maps to DB_NAME_LAMISPLUS_STAGING_DWH  (default: lamisplus_staging_dwh_test)
      - any other   → maps to DB_NAME_<DATABASE_NAME> env var, falling back to the name itself
    """

    # ── Shared connection parameters (both DBs live on this machine) ──────────
    db_host     = os.environ.get("DB_HOST", "localhost")
    db_user     = os.environ.get("DB_USER", "lamisplus")
    db_password = os.environ.get("DB_PASSWORD", "FmALa9PYGQUfyjq")
    db_port     = os.environ.get("DB_PORT", "5432")

    # ── Map logical name → actual database name ───────────────────────────────
    if database_name.lower() == "server_a":
        lookup_key = "DB_NAME_SERVER_A"
        default_db = "lamisplus_demo_db"
    elif database_name.lower() == "server_b":
        lookup_key = "DB_NAME_LAMISPLUS_STAGING_DWH"
        default_db = "lamisplus_staging_dwh_test"
    else:
        lookup_key = f"DB_NAME_{database_name.upper()}"
        default_db = database_name

    db_name = os.environ.get(lookup_key, default_db)

    # ── Establish connection ──────────────────────────────────────────────────
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=str(db_port),
    )

    connection_string = (
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    engine = create_engine(connection_string)

    return conn, engine