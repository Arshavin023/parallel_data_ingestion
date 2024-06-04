import psycopg2
import os
from datetime import datetime
from src import logger
import configparser

def read_db_config(filename='/home/lamisplus/database_credentials/config.ini', section='database'):
    # Create a parser
    parser = configparser.ConfigParser()
    # Read the configuration file
    parser.read(filename)
    # Get section, default to database
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')
    return db

db_config = read_db_config()

def _db_connect_filedb():
        db_params = {
        'host': db_config['stg_host'],
        'database': 'filedb',
        'user': db_config['stg_username'],
        'password': db_config['stg_password'],
        'port': db_config['stg_port'],}

         # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_params)
        return conn

def _db_connect_lamisplus_staging_dwh():
        db_params = {
        'host': db_config['stg_host'],
        'database': 'lamisplus_staging_dwh',
        'user': db_config['stg_username'],
        'password': db_config['stg_password'],
        'port': db_config['stg_port'],}

         # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_params)
        return conn

def delete_staging_table_records():

    try:
        # conn = _db_connect_filedb()
        conn = _db_connect_lamisplus_staging_dwh()
        cur = conn.cursor()
        #cur2 = conn2.cursor()
        retrieve_query = """with table_size_info as
                            (SELECT table_name, 
                             pg_total_relation_size(quote_ident(table_name))/1048576 AS total_size_megabytes
                            FROM information_schema.tables
                            WHERE table_schema = 'public')
                            select table_name from table_size_info 
                            where total_size_megabytes > 200 AND table_name ilike 'stg_%'
                            """
                            
        delete_query = """DELETE FROM {} 
                          WHERE stg_load_time <= CURRENT_DATE - INTERVAL '45' DAY 
                       """
        cur.execute(retrieve_query)

        # Fetch all file associated data from sync_file
        staging_tables = cur.fetchall()

        for stg in staging_tables:

            try:
                logger.info(f'deletion of records ingested in last 45 days from {stg} table started')
                cur.execute(delete_query.format(stg[0]))
                conn.commit()
                logger.info(f'deletion of records ingested in last 45 days from {stg} table started')

            except Exception as e:
                logger.exception(e)

        # Commit the changes and close the connection
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {str(e)}")
        
        