import psycopg2

def copy_table_schemas(source_conn_params, destination_conn_params):
    # Connect to the source and destination databases
    source_conn = psycopg2.connect(**source_conn_params)
    destination_conn = psycopg2.connect(**destination_conn_params)

    try:
        # Retrieve table schemas from the source database
        with source_conn.cursor() as source_cur:
            source_cur.execute("SELECT table_name, table_schema, column_name, data_type FROM information_schema.columns")
            table_schemas = source_cur.fetchall()

        # Create tables in the destination database
        with destination_conn.cursor() as dest_cur:
            current_table_name = ""
            create_table_sql = ""

            for row in table_schemas:
                table_name, table_schema, column_name, data_type = row

                if table_name != current_table_name:
                    # New table encountered, execute the CREATE TABLE statement
                    if create_table_sql:
                        print(create_table_sql)
                        dest_cur.execute(create_table_sql)
                    current_table_name = table_name
                    create_table_sql = f"CREATE TABLE {table_schema}.stg_{table_name} ("

                # Add column definition to CREATE TABLE statement
                create_table_sql += f"{column_name} {data_type}, "

            # Execute the last CREATE TABLE statement
            if create_table_sql:
                print(create_table_sql)
                dest_cur.execute(create_table_sql.rstrip(", ") + ")")

        # Commit the changes to the destination database
        destination_conn.commit()

    finally:
        # Close database connections
        source_conn.close()
        destination_conn.close()

# Example Usage
source_conn_params = {
    'host': 'localhost',
    'database': 'dwh_standard',
    'user': 'oluwaloseyi',
    'password': 'VgLYVEqNzJxMmSX',
    'port': '5432',
}

destination_conn_params = {
    'host': 'localhost',
    'database': 'lamisplus_staging_dwh',
    'user': 'oluwaloseyi',
    'password': 'VgLYVEqNzJxMmSX',
    'port': '5432',
}

copy_table_schemas(source_conn_params, destination_conn_params)
