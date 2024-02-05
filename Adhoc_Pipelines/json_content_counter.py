import os
import json
import psycopg2

def _db_connect_filedb():
    db_params = {
    'host': 'localhost',
    'database': 'lamisplus_staging_dwh',
    'user': 'oluwaloseyi',
    'password': 'VgLYVEqNzJxMmSX',
    'port': '5432',
        }

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**db_params)
    return conn

def _create_report_table():
    conn = _db_connect_filedb()
    cur = conn.cursor()

    q_drop = "drop table if exists public.sourcefile_counter"
    cur.execute(q_drop)

    q_create = """CREATE TABLE public.sourcefile_counter(datim_id CHARACTER VARYING, 
    filename CHARACTER VARYING, 
    row_count BIGINT, tablename CHARACTER VARYING)
    """
    cur.execute(q_create)

    conn.commit()
    cur.close()

    print('Report table prepared successfully')

def _process_derive_tablename(file_path):
    print("processing file")
    filename = os.path.basename(file_path)
    parts = filename.split('_')
    non_digit_parts = [part for part in parts if not part.isdigit() and part != 'decrypted.json']
    result=[]
    result.append('_'.join(non_digit_parts))
    check_path = result[0]
    return check_path

def count_rows_in_json_files(folder_path, prefix, suffix):
    result = []
    for filename in os.listdir(folder_path):
        if filename.startswith(prefix) and filename.endswith(suffix):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    num_rows = len(data)
                    result.append((filename, num_rows))
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON file {filename}: {e}")
    return result

# Example usage:
facility_datim = 'YYKhk7qR2W3'
folder_path = f'/home/lamisplus/server/temp/{facility_datim}'
print(folder_path)
prefix = 'hiv_art_pharmacy_'  # Adjust as needed
suffix = '_decrypted.json'  # Adjust as needed
result = count_rows_in_json_files(folder_path, prefix, suffix)

_create_report_table()

for filename, num_rows in result:
    conn = _db_connect_filedb()
    cur = conn.cursor()
    
    print(f"File: {filename}, Number of Rows: {num_rows}")


    insert_query = """insert into public.sourcefile_counter 
        (datim_id, filename, row_count, tablename) 
        values ('{}','{}','{}','{}')""".format(facility_datim, filename, num_rows, _process_derive_tablename(filename))

    cur.execute(insert_query)
    conn.commit()
    cur.close()