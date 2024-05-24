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
    VALUES ('{}','{}','{}', '{}')""".format(log_id, start_time, 'Job Started', 'file deletion')

    cur.execute(insert_pipeline_query)
    conn.commit()

    try:
        logger.info('Job Started')

        logger.info('Deletion of <90 days records from staging tables started')
        delete_stg_table_records()
        logger.info('Deletion of <90 days records from staging tables completed')
        
        logger.info('Deletion of decrypted json files started')
        delete_ingested_decrypted_files()
        logger.info('Deletion of decrypted json files completed')
        
        q_check_count = """select count(*) from file_deletion_log 
                        where where file_name ilike '%_decrypted.json' and 
                        deletion_start_time >=  %s and deletion_end_time <=  %s
                        """
        cur2.execute(q_check_count, (start_time, end_time))
        records_processed = cur2.fetchall()[0]

        update_pipeline_query = """update file_ingestion_pipeline_log set end_time=  %s
                                , status =  %s, error_message=  %s, records_processed=  %s
                                where log_id =  %s
                                """ 
        cur.execute(update_pipeline_query, (end_time, 'Job Passed', 'No Errors', records_processed, log_id))
        conn.commit()
        logger.info('Deletion Job for encrypted files was run Successfully')
        
        logger.info('Deletion of encrypted json files started')
        delete_encrypted_files()
        logger.info('Deletion of encrypted json files completed')
        end_time = datetime.now()
        q_check_count = """select count(*) from file_deletion_log 
                        where where file_name not ilike '%_decrypted.json' and 
                        deletion_start_time >=  %s and deletion_end_time <=  %s
                        """
        cur2.execute(q_check_count, (start_time, end_time))
        records_processed = cur2.fetchall()[0]
        update_pipeline_query = """update file_ingestion_pipeline_log set end_time=  %s
                                , status =  %s, error_message=  %s, records_processed=  %s
                                where log_id =  %s
                                """ 
        cur.execute(update_pipeline_query, (end_time, 'Job Passed', 'No Errors', records_processed, log_id))
        conn.commit()
        logger.info('Deletion Job for encrypted files was run successfully completed')

    except Exception as e:
        error_msg =str(e)
        end_time = datetime.now()
        update_pipeline_query = """update file_ingestion_pipeline_log set end_time=  %s
        , status =  %s, error_message=  %s
        where log_id =  %s""" 
        
        cur.execute(update_pipeline_query, (end_time, 'Job Failed', error_msg, log_id))
        conn.commit()
        
    
    conn.commit()
    cur.close()
    conn2.commit()