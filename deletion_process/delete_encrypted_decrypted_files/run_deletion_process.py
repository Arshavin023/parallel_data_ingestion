from automate_file_delete import FileDelete
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

def main():
    db_params = {'host': db_config['stg_host'],'database': 'lamisplus_staging_dwh','user': db_config['stg_username'],
                 'password': db_config['stg_password'],'port': db_config['stg_port'],}
    
    db_params2 = {'host': db_config['stg_host'],'database': 'filedb','user': db_config['stg_username'],
                  'password': db_config['stg_password'],'port': db_config['stg_port'],}
    
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
        logger.info('Deletion of decrypted json files started')
        deletion = FileDelete()
        deletion.delete_ingested_decrypted_files()
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
        logger.info('Deletion Job for decrypted files was run Successfully')
        
        logger.info('Deletion of encrypted json files started')
        deletion = FileDelete()
        deletion.delete_encrypted_files()
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

if __name__ == '__main__':
    main()