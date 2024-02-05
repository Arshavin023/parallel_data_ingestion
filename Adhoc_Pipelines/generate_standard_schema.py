import psycopg2

def copy_table_schemas(source_conn_params, destination_conn_params):
    source_conn = psycopg2.connect(**source_conn_params)
    source_cur = source_conn.cursor()

    destination_conn = psycopg2.connect(**destination_conn_params)
    destination_cur = destination_conn.cursor()

    # Get the list of tables from the source database
    source_cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT LIKE 'pg_%' AND table_schema != 'information_schema'
    """)

    for table_schema, table_name in source_cur.fetchall():
        # Get the column names and types for the current table
        select_select = """SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema =  %s AND table_name =  %s
            ORDER BY ordinal_position"""

        print(table_schema, table_name)
        source_cur.execute(select_select, (table_schema, table_name))

        columns = source_cur.fetchall()
        print(columns)

        # Additional columns to be added to each table
        additional_columns = [
            ('stg_batch_id', 'VARCHAR'),
            ('stg_load_time', 'TIMESTAMP'),
            ('stg_file_name', 'VARCHAR'),
            ('stg_datim_id', 'VARCHAR')
        ]

        # Add the additional columns to the existing columns
        columns += additional_columns

        create_table_sql = f"""
            CREATE TABLE public.stg_{table_name} (
                {', '.join([f'{column[0]} {column[1]}' for column in columns])}
            );
        """
        #print(create_table_sql)

        # Execute the SQL script in the destination database
        destination_cur.execute(create_table_sql)

    source_cur.close()
    source_conn.close()

    destination_cur.close()
    destination_conn.commit()
    destination_conn.close()

source_conn_params = {
    'host': 'localhost',
    'database': 'dwh_standard',
    'user': 'oluwaloseyi',
    'password': 'VgLYVEqNzJxMmSX',
    'port': '5432',  # Adjust the port if necessary
}

destination_conn_params = {
    'host': 'localhost',
    'database': 'lamisplus_staging_dwh',
    'user': 'oluwaloseyi',
    'password': 'VgLYVEqNzJxMmSX',
    'port': '5432',  # Adjust the port if necessary
}

copy_table_schemas(source_conn_params, destination_conn_params)
