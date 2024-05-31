from automate_file_delete import delete_encrypted_files, delete_ingested_decrypted_files, delete_stg_table_records
from datetime import datetime
import psycopg2
from src import logger


if __name__ == '__main__':
    db_params = {
    'host': 'localhost',
    'database': 'lamisplus_staging_dwh',
    'user': 'lamisplus',
    'password': '37EpE&U&H?',
    'port': '5432',
        }
    
    db_params2 = {
        'host': 'localhost',
        'database': 'filedb',
        'user': 'lamisplus',
        'password': '37EpE&U&H?',
        'port': '5432',
         }
    
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

        logger.info('Deletion of <= 105 days records from staging tables started')
        delete_staging_table_records()
        conn.commit()
        logger.info('Deletion of <= 105 days records from staging tables completed')
        
    except Exception as e:
        error_msg =str(e)
        end_time = datetime.now()
        conn.commit()
        
    
    conn.commit()
    cur.close()
    conn2.commit()