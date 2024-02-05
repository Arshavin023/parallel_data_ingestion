import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# PostgreSQL database connection parameters
db_params = {
    'host': 'localhost',
    'port': '5432',
    'database': 'lamisplus_staging_dwh',
    'user': 'oluwaloseyi',
    'password': 'VgLYVEqNzJxMmSX'
}

# Table name to export
#table_name = 'stg_hiv_art_pharmacy'

# Chunk size for reading data
chunk_size = 100000

# Create a connection to PostgreSQL
conn = psycopg2.connect(**db_params)

# Create a SQLAlchemy engine
engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}')

# Count total rows in the table
total_rows = pd.read_sql_query("""select count(*) from public.hiv_art_pharmacy_withregimens_1452""", conn).iloc[0, 0]
print('total_row is: ', total_rows)

# Read the table in chunks
chunks = []
for chunk_start in range(0, total_rows, chunk_size):
    query = f"""select * from public.hiv_art_pharmacy_withregimens_1452 LIMIT {chunk_size} OFFSET {chunk_start}"""
    chunk_df = pd.read_sql_query(query, engine)
    chunk_df.fillna('', inplace=True)
    chunks.append(chunk_df)

# Concatenate all chunks into a single DataFrame
df = pd.concat(chunks, ignore_index=True)

# Specify the CSV file path
csv_file_path = 'hiv_art_pharmacy_withregimens_1452.csv'

# Write the DataFrame to a CSV file
df.to_csv(csv_file_path, index=False)

# Close the database connection
conn.close()

print(f'Table "{table_name}" exported to CSV: {csv_file_path}')
