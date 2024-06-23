from automate_stg_records_delete import delete_staging_table_records
from datetime import datetime
import psycopg2
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


if __name__ == '__main__':
    db_params = {
    'host': db_config['stg_host'],
    'database': 'lamisplus_staging_dwh',
    'user': db_config['stg_username'],
    'password': db_config['stg_password'],
    'port': db_config['stg_port'],}
    
    db_params2 = {
        'host': db_config['stg_host'],
        'database': 'filedb',
        'user': db_config['stg_username'],
        'password': db_config['stg_password'],
        'port': db_config['stg_port'],}
    
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    conn2 = psycopg2.connect(**db_params2)
    cur2 = conn2.cursor()

    start_time = datetime.now() 
    log_id = f'DPID_{start_time.strftime("%Y%m%d_%H_%M")}' #deletion process ID
    logger.info(log_id)

    insert_pipeline_query = """insert into file_ingestion_pipeline_log (log_id, start_time, status, process_type) 
    VALUES ('{}','{}','{}', '{}')""".format(log_id, start_time, 'Job Started', 'staging records deletion')
    cur.execute(insert_pipeline_query)
    conn.commit()

    try:
        logger.info('Job Started')

        logger.info('Deletion of <= 45 days records from staging tables started')
        delete_staging_table_records()
        conn.commit()
        logger.info('Deletion of <= 45 days records from staging tables completed')
        
    except Exception as e:
        error_msg =str(e)
        end_time = datetime.now()
        conn.commit()
        
    
    conn.commit()
    cur.close()
    conn2.commit()