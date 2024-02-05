import psycopg2
import pandas as pd
from sqlalchemy import create_engine


source_db_params = {
    'host': 'localhost',
    'database': 'filedb',
    'user': 'oluwaloseyi',
    'password': 'VgLYVEqNzJxMmSX',
    'port': '5432'
}

target_db_params = {
    'host': 'localhost',
    'database': 'lamisplus_staging_dwh',
    'user': 'oluwaloseyi',
    'password': 'VgLYVEqNzJxMmSX',
    'port': '5432'
}

engine = create_engine(f'postgresql://{target_db_params["user"]}:{target_db_params["password"]}@{target_db_params["host"]}:{target_db_params["port"]}/{target_db_params["database"]}')


# Establish a connection to the source PostgreSQL database
source_conn = psycopg2.connect(**source_db_params)
source_cursor = source_conn.cursor()

load_table = "table_coltypes_check"

drop_query = "DROP TABLE IF EXISTS table_coltypes_check;"

source_cursor.execute(drop_query)

# Query to retrieve table names in the public schema
table_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"

# Execute the table query
source_cursor.execute(table_query)

# Fetch all table names
table_names = source_cursor.fetchall()
print(table_names)

# Loop through each table and obtain column names and types
for table_name in table_names:
    table_name = table_name[0]
    
    # Query to retrieve column names and types for a given table
    column_query = f"SELECT table_name tabname, column_name col_name, data_type col_type FROM information_schema.columns WHERE table_name = '{table_name}';"

    df = pd.read_sql(column_query, con=source_conn)

    print(df)
    ## Insert the DataFrame into the existing PostgreSQL table
    df.to_sql(load_table, con=engine, index=False, if_exists='append')

# Close the cursors and connections
source_cursor.close()
source_conn.close()
