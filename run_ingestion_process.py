from file_ingestion_loader import FileLoader
from datetime import datetime
import psycopg2

print('importations successful')

if __name__ == '__main__':
    db_params = {
    'host': 'localhost',
    'database': 'lamisplus_staging_dwh',
    'user': 'oluwaloseyi',
    'password': 'VgLYVEqNzJxMmSX',
    'port': '5432',
        }
    
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    start_time = datetime.now() 
    log_id = f'IPID_{start_time.strftime("%Y%m%d_%H_%M")}' #ingestion process ID
    print(log_id)

    insert_pipeline_query = """insert into file_ingestion_pipeline_log (log_id, start_time, status, process_type) 
    VALUES ('{}','{}','{}', '{}')""".format(log_id, start_time, 'Job Started', 'file ingestion')

    cur.execute(insert_pipeline_query)
    conn.commit()

    try:
        print('Job Started')
        loader = FileLoader()
        loader._retrieve_localdir_from_syncfile()
        end_time = datetime.now()

        q_check_count = """select count(*) from file_ingestion_log 
        where load_start_time >=  %s and load_end_time <=  %s
        """
        cur.execute(q_check_count, (start_time, end_time))
        records_processed = cur.fetchall()[0]

        update_pipeline_query = """update file_ingestion_pipeline_log set end_time=  %s
        , status =  %s, error_message=  %s, records_processed=  %s
        where log_id =  %s""" 

        cur.execute(update_pipeline_query, (end_time, 'Job Passed', 'No Errors', records_processed, log_id))
        print('Job was run Successfully')
        conn.commit()
    
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