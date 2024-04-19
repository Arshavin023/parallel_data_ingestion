import psycopg2
from datetime import datetime
from test_file_ingestion_process.test_file_loader import FileLoader

def insert_pipeline_log(cur, log_id, start_time):
    insert_pipeline_query = """
        INSERT INTO file_ingestion_pipeline_log (log_id, start_time, status, process_type) 
        VALUES (%s, %s, %s, %s)
    """
    cur.execute(insert_pipeline_query, (log_id, start_time, 'Job Started', 'file ingestion'))

def update_pipeline_log(cur, log_id, end_time, status, error_message=None, records_processed=None):
    update_pipeline_query = """
        UPDATE file_ingestion_pipeline_log 
        SET end_time = %s, status = %s, error_message = %s, records_processed = %s
        WHERE log_id = %s
    """
    cur.execute(update_pipeline_query, (end_time, status, error_message, records_processed, log_id))

def main():
    db_params = {
        'host': 'localhost',
        'database': 'lamisplus_staging_dwh',
        'user': 'lamisplus',
        'password': '37EpE&U&H?',
        'port': '5432',
    }

    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cur:
                start_time = datetime.now() 
                log_id = f'IPID_{start_time.strftime("%Y%m%d_%H_%M")}' #ingestion process ID
                print(log_id)
                
                insert_pipeline_log(cur, log_id, start_time)
                
                try:
                    print('Job Started')
                    loader = FileLoader()
                    loader._retrieve_localdir_from_syncfile()
                    end_time = datetime.now()
    
                    q_check_count = """
                        SELECT COUNT(*) 
                        FROM file_ingestion_log 
                        WHERE load_start_time >= %s AND load_end_time <= %s
                    """
                    cur.execute(q_check_count, (start_time, end_time))
                    records_processed = cur.fetchone()[0]
    
                    update_pipeline_log(cur, log_id, end_time, 'Job Passed', 'No Errors', records_processed)
                    print('Job was run Successfully')
                
                except Exception as e:
                    error_msg = str(e)
                    end_time = datetime.now()
                    update_pipeline_log(cur, log_id, end_time, 'Job Failed', error_msg)
    
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL database:", e)

if __name__ == '__main__':
    main()
