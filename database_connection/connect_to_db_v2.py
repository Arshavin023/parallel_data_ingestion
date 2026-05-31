# import os
# import psycopg2
# from sqlalchemy import create_engine
# from dotenv import load_dotenv
# from sshtunnel import SSHTunnelForwarder  # <-- Import the SSH library

# # Load variables from .env file into os.environ if it exists
# load_dotenv()

# # Track the tunnel globally so we don't open multiple tunnels on concurrent threads
# _server_a_tunnel = None

# def connect(database_name):
#     # 1. SPECIAL CASE: Isolate Server A (Source Engine)
#     if database_name.lower() == "server_a":
#         db_host = os.environ.get("SERVER_A_SSH_HOST")
#         db_user = os.environ.get("SERVER_A_DB_USER")
#         db_password = os.environ.get("SERVER_A_DB_PASSWORD")
#         db_port = os.environ.get("SERVER_A_DB_PORT", "5432")
#         db_name = os.environ.get("SERVER_A_DB_NAME")
        
#     # 2. STANDARD ROUTING: For everything else (Server B, filedb, lamisplus_staging_dwh)
#     else:
#         # Core infrastructure environment variables (Your local machine / Destination Server B)
#         db_host = os.environ.get("DB_HOST", "localhost")
#         db_user = os.environ.get("DB_USER", "lamisplus")
#         db_password = os.environ.get("DB_PASSWORD", "your_default_password")
#         db_port = os.environ.get("DB_PORT", "5432")
        
#         # Intercept "server_b" string from schema_alignment and map it to your DWH configuration variable
#         if database_name.lower() == "server_b":
#             lookup_key = "DB_NAME_LAMISPLUS_STAGING_DWH"
#         else:
#             lookup_key = f"DB_NAME_{database_name.upper()}"
            
#         # Dynamically fetch the accurate DB name or default to the raw input string
#         db_name = os.environ.get(lookup_key, database_name)

#     # 1. Establish Psycopg2 Connection
#     conn = psycopg2.connect(
#         host=db_host,
#         database=db_name,
#         user=db_user,
#         password=db_password,
#         port=db_port
#     )
    
#     # 2. Establish SQLAlchemy Engine
#     connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
#     engine = create_engine(connection_string)
    
#     return conn, engine

import os
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder  # <-- Import the SSH library

# Load variables from .env file into os.environ if it exists
load_dotenv()

# Track the tunnel globally so we don't open multiple tunnels on concurrent threads
_server_a_tunnel = None

def connect(database_name):
    global _server_a_tunnel

    # 1. SPECIAL CASE: Isolate Server A (Source Engine with SSH Tunnel)
    if database_name.lower() == "server_a":
        ssh_host = os.environ.get("SERVER_A_SSH_HOST")
        ssh_user = os.environ.get("SERVER_A_SSH_USER")
        ssh_password = os.environ.get("SERVER_A_SSH_PASSWORD")
        
        remote_db_host = "127.0.0.1" # The target address *relative* to the Server A machine
        remote_db_port = int(os.environ.get("SERVER_A_DB_PORT", "5432"))
        
        db_user = os.environ.get("SERVER_A_DB_USER")
        db_password = os.environ.get("SERVER_A_DB_PASSWORD")
        db_name = os.environ.get("SERVER_A_DB_NAME")

        # Start the SSH Tunnel if it isn't running yet
        if _server_a_tunnel is None or not _server_a_tunnel.is_active:
            print(f"[SSH] Opening secure tunnel to {ssh_host}...")
            _server_a_tunnel = SSHTunnelForwarder(
                (ssh_host, 22),                    # SSH Server Address & Default Port
                ssh_username=ssh_user,
                ssh_password=ssh_password,
                remote_bind_address=(remote_db_host, remote_db_port) # Destination inside the private network
            )
            _server_a_tunnel.start()

        # Route psycopg2 through the local binding port created by the tunnel
        db_host = "127.0.0.1"
        db_port = _server_a_tunnel.local_bind_port
        print(f"[SSH] Tunnel established. Routing traffic locally via port: {db_port}")
        
    # 2. STANDARD ROUTING: For everything else (Server B, filedb, lamisplus_staging_dwh)
    else:
        # Core infrastructure variables (Your local machine / Destination Server B)
        db_host = os.environ.get("DB_HOST", "localhost")
        db_user = os.environ.get("DB_USER", "lamisplus")
        db_password = os.environ.get("DB_PASSWORD", "your_default_password")
        db_port = os.environ.get("DB_PORT", "5432")
        
        # Intercept "server_b" string from schema_alignment and map it to your DWH configuration variable
        if database_name.lower() == "server_b":
            lookup_key = "DB_NAME_LAMISPLUS_STAGING_DWH"
        else:
            lookup_key = f"DB_NAME_{database_name.upper()}"
            
        # Dynamically fetch the accurate DB name or default to the raw input string
        db_name = os.environ.get(lookup_key, database_name)

    # 1. Establish Psycopg2 Connection
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=str(db_port)
    )
    
    # 2. Establish SQLAlchemy Engine
    connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(connection_string)
    
    return conn, engine