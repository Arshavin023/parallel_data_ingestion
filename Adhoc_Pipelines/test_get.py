import psycopg2
import os
db_params = {
        'host': 'localhost',
        'database': 'lamisplus_staging_dwh',
        'user': 'oluwaloseyi',
        'password': 'VgLYVEqNzJxMmSX',
        'port': '5432',
         }

def test_():
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        table_name = 'stg_patient_person'


        retrieve_query = """SELECT column_name, data_type
        FROM information_schema.columns
        where table_catalog = 'lamisplus_staging_dwh'
        and table_schema = 'public'
        and table_name = '{tname}' """.format(tname = table_name)

        cur.execute(retrieve_query)


        # Fetch all file associated data from sync_file
        columns = cur.fetchall()

        column_list = []
        types_list = []

        column_mapping = {name: type_ for name, type_ in columns}
        
        #print(column_mapping)
        column_list = [i[0] for i in columns]
        #print(column_list)
        return [column_mapping, column_list]

print(test_()[1])
