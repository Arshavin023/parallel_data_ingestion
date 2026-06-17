import os
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder

# Load variables from .env file into os.environ if it exists
load_dotenv()

# Track the tunnel globally so we don't open multiple tunnels on concurrent threads
_server_a_tunnel = None

def connect(database_name):
    global _server_a_tunnel

    # 1. REMOTE TUNNELING: Only trigger the tunnel if explicitly asking for remote
    if database_name.lower() == "server_a_remote":
        ssh_host = os.environ.get("SERVER_A_SSH_HOST")
        ssh_user = os.environ.get("SERVER_A_SSH_USER")
        ssh_password = os.environ.get("SERVER_A_SSH_PASSWORD")
        
        remote_db_host = "127.0.0.1" 
        remote_db_port = int(os.environ.get("SERVER_A_DB_PORT", "5432"))
        
        db_user = os.environ.get("SERVER_A_DB_USER")
        db_password = os.environ.get("SERVER_A_DB_PASSWORD")
        db_name = os.environ.get("SERVER_A_DB_NAME")

        if _server_a_tunnel is None or not _server_a_tunnel.is_active:
            print(f"[SSH] Opening secure tunnel to {ssh_host}...")
            _server_a_tunnel = SSHTunnelForwarder(
                (ssh_host, 22),
                ssh_username=ssh_user,
                ssh_password=ssh_password,
                remote_bind_address=(remote_db_host, remote_db_port)
            )
            _server_a_tunnel.start()

        db_host = "127.0.0.1"
        db_port = _server_a_tunnel.local_bind_port
        print(f"[SSH] Tunnel established. Routing traffic locally via port: {db_port}")
        
    # 2. STANDARD ROUTING: For everything else running locally on this machine
    # 2. STANDARD ROUTING: For everything else running locally on this machine
    else:
        # Core infrastructure variables (Your local machine / Destination Server B)
        db_host = os.environ.get("DB_HOST", "localhost")
        db_user = os.environ.get("DB_USER", "lamisplus")
        db_password = os.environ.get("DB_PASSWORD", "FmALa9PYGQUfyjq") 
        db_port = os.environ.get("DB_PORT", "5432")
        
        # Intercept database keys and map them to your local .env configuration variables
        if database_name.lower() == "server_a":
            lookup_key = "DB_NAME_SERVER_A"
            default_db = "lamisplus_demo_db"  # <-- Hardcoded fallback for server_a
        elif database_name.lower() == "server_b":
            lookup_key = "DB_NAME_LAMISPLUS_STAGING_DWH"
            default_db = "lamisplus_staging_dwh_test"  # <-- Hardcoded fallback for server_b
        else:
            lookup_key = f"DB_NAME_{database_name.upper()}"
            default_db = database_name
            
        # Dynamically fetch the accurate DB name or default to our explicit string fallback
        db_name = os.environ.get(lookup_key, default_db)

    # 3. ESTABLISH CONNECTIONS (Crucial step that was cut off)
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=str(db_port)
    )
    
    connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(connection_string)
    
    return conn, engine