from file_loader_v3 import FileLoader
import configparser
import numpy as np
import psycopg2
from psycopg2.extras import Json
import pandas as pd
from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine, JSON, Integer, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from src import logger
import threading
import time
import concurrent.futures

unprocessed, processed, failed = 'UNPROCESSED', 'PROCESSING', 'FAILED'

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


def db_connect(database: str):
    """
    Establishes a connection to the specified PostgreSQL database.
    Parameters:
    - database (str): The name of the database to connect to.
    Returns:
    - conn (psycopg2.connection): The connection object.
    - engine (sqlalchemy.engine.base.Engine): The SQLAlchemy engine object.
    Raises:
    - Exception: If connection to the database fails.
    """
    db_params = {'host': db_config['stg_host'], 'database': database, 'user': db_config['stg_username'],
                    'password': db_config['stg_password'], 'port': db_config['stg_port'], }
    try:
        conn = psycopg2.connect(**db_params)
        engine = create_engine(
            f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}')

        return [conn, engine]

    except Exception as e:
        logger.info(f'failed to connect to {database} database')
        logger.exception(e)
        raise e

staging_conn, staging_engine = db_connect('lamisplus_staging_dwh')[0], db_connect('lamisplus_staging_dwh')[1]
filedb_conn, filedb_engine = db_connect('filedb')[0], db_connect('filedb')[1]
staging_cur = staging_conn.cursor()
filedb_cur = filedb_conn.cursor()

def insert_batch_ingestion_log():
    insert_batch_query="""
        INSERT INTO batch_facility_id_logs(facility_id,status,facility_id_count)
        SELECT facility_id, 'UNPROCESSED', COUNT(file_name)
        FROM sync_file
        WHERE processed=1 AND modified_date >= '2024-11-01'
        AND NOT (decrypted_file_name ilike 'hiv_art_clinical%' or decrypted_file_name ILIKE 'dsd_devolvement%' or decrypted_file_name ilike 'mhpss_confirmation%')
        GROUP BY 1,2
        ORDER BY modified_date ASC
    """
    filedb_cur.execute(insert_batch_query)
    filedb_conn.commit()

def update_batch_ingestion_log(id:int,facility_id:str,count:int,new_status,
                               old_status,start_time=None,end_time=None,error_message=None):
    update_batch_query="""
        UPDATE batch_facility_id_logs
        SET status=%s, start_time=%s, end_time=%s, error_message=%s
        WHERE id=%s 
        AND status=%s
        AND facility_id=%s
        AND facility_id_count=%s
        """
    filedb_cur.execute(update_batch_query,(new_status,start_time,end_time,
                                           error_message,id,old_status,facility_id,count))
    filedb_conn.commit()
    # logger.info(f'batch ingestion for {facility_id} successfully updated on batch_facility_id_logs table')

def insert_pipeline_log(cur, log_id, start_time):
    insert_pipeline_query = """
        INSERT INTO file_ingestion_pipeline_log (log_id, start_time, status, process_type) 
        VALUES (%s, %s, %s, %s)
    """
    staging_cur.execute(insert_pipeline_query, (log_id, start_time, 'Job Started', 'file ingestion'))

def update_pipeline_log(cur, log_id, end_time, status, error_message=None, records_processed=None):
    update_pipeline_query = """
        UPDATE file_ingestion_pipeline_log 
        SET end_time = %s, status = %s, error_message = %s, records_processed = %s
        WHERE log_id = %s
    """
    staging_cur.execute(update_pipeline_query, (end_time, status, error_message, records_processed, log_id))

def batch_facility_job(instance):
    filedb_conn, filedb_engine = db_connect('filedb')[0], db_connect('filedb')[1]
    filedb_cur = filedb_conn.cursor()
    unprocessed_cbo_query="""
        SELECT id, facility_id,facility_id_count
        FROM batch_facility_id_logs
        WHERE status = 'UNPROCESSED'
        ORDER BY id ASC
        LIMIT 1
    """

    filedb_cur.execute(unprocessed_cbo_query)
    facility_info = filedb_cur.fetchall()
    print(facility_info)

    if facility_info:
        batch_id = facility_info[0][0]
        facility_id = facility_info[0][1]
        facility_id_count = facility_info[0][2]
        try:
            batch_start_time = datetime.now() 
            update_batch_ingestion_log(batch_id,facility_id,facility_id_count,'PROCESSING','UNPROCESSED')
            instance._retrieve_localdir_from_syncfile(facility_id)
            batch_end_time = datetime.now()
            # print(type(batch_id),' ',type(facility_id),' ',type(facility_id_count),' ', type(status),' ',type(batch_start_time),' ',type(batch_end_time))
            update_batch_ingestion_log(batch_id,facility_id,facility_id_count,'PROCESSED','PROCESSING', batch_start_time,batch_end_time,'No errors')
            logger.info(f"""batch ingestion for {facility_id} started at {batch_start_time} completed at {batch_end_time}""")

        except Exception as e:
            error_msg = str(e)
            batch_end_time = datetime.now()
            update_batch_ingestion_log(batch_id,facility_id,facility_id_count,'FAILED','PROCESSING',batch_start_time,batch_end_time,error_msg)

def main():

    print('Job Started')
    start_time = datetime.now() 
    log_id = f'IPID_{start_time.strftime("%Y%m%d_%H_%M")}' #ingestion process ID
    print(log_id)
    insert_pipeline_log(staging_cur, log_id, start_time)
    insert_batch_ingestion_log()

    loader = FileLoader()
    batch_count = pd.read_sql(
                    """SELECT COUNT(facility_id) 
                    FROM batch_facility_id_logs
                    WHERE status = '{}'
                    """.format(unprocessed), con=filedb_engine).values[0][0]

    # Function to run the job in a thread
    def run_job():
        batch_facility_job(loader)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:

        results = executor.map(run_job, queue)

    #Wait for all tasks to complete using the shutdown() method
        executor.shutdown()
    if batch_count > 0:
        threads = []
        for _ in range(batch_count):
            thread = threading.Thread(target=run_job)
            thread.start()
            threads.append(thread)
            time.sleep(5)  # 5-second delay between starting threads

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    end_time = datetime.now()
    records_processed = pd.read_sql(
        """ SELECT COUNT(*) 
        FROM file_ingestion_log 
        WHERE load_start_time >= '{}' AND load_end_time <= '{}'
        """.format(start_time, end_time), con=staging_engine).values[0][0]
    
    # staging_cur.execute(q_check_count, (start_time, end_time))
    # records_processed = staging_cur.fetchone()[0]

    update_pipeline_log(staging_cur, log_id, end_time, 'Job Passed', 'No Errors', int(records_processed))
    print('Job was run Successfully')
        
    staging_cur.close()
    staging_conn.close()

    
if __name__ == '__main__':
    main()
