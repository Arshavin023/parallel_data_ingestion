from multi_automate_file_delete import FileDelete
from datetime import datetime
import psycopg2
from src import logger
import configparser
from database_connection.db_connect import connect_to_db
import concurrent.futures

# Function to fetch datim_ids from the database
def fetch_datim_ids(ip_name):
    with connect_to_db.connect('filedb')[0] as conn:
        with conn.cursor() as cur:
            fetch_datims_query = """SELECT datim_id FROM central_partner_mapping 
                                    WHERE ip_name=%s"""
            cur.execute(fetch_datims_query,(ip_name,))
            datims = cur.fetchall()
            datim_ids = [record[0] for record in datims]
            return datim_ids

def create_single_instance(facility_id:str):
    try:
        deletion_encrypted = FileDelete()
        deletion_encrypted.delete_encrypted_files(facility_id)
        logger.info(f'deletetion of encrypted and decrypted files for {facility_id} successfully completed')
    
    except Exception as e:
        logger.info(f'deletetion of encrypted and decrypted files for {facility_id} failed')
        
        
def main():
    # Connect to the PostgreSQL database
    conn = connect_to_db.connect('lamisplus_staging_dwh')[0]
    cur = conn.cursor()
    
    conn2 = connect_to_db.connect('filedb')[0]
    cur2 = conn2.cursor()

    start_time = datetime.now()
    log_id = f'DPID_{start_time.strftime("%Y%m%d_%H_%M")}'
    logger.info(log_id)

    insert_pipeline_query = """insert into file_ingestion_pipeline_log (log_id, start_time, status, process_type) 
    VALUES ('{}','{}','{}', '{}')""".format(log_id, start_time, 'Job Started', 'file deletion')

    cur.execute(insert_pipeline_query)
    conn.commit()
    
    ip_names = ['ACE-1','ACE-2','ACE-3','ACE-4','CARE 1', 'CARE 2','ACE-5']
    #ip_names = ['CARE 2']
    
    group_ip_datims = [fetch_datim_ids(ip) for ip in ip_names]
    batch_size=10
    try:
        logger.info('Deletion of json files started')
        delete_start_time = datetime.now()
        for datim_ids in group_ip_datims:
            batches = [datim_ids[i:i + batch_size] for i in range(0, len(datim_ids), batch_size)]
            for batch in batches:
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    executor.map(create_single_instance, batch)
                logger.info(f"Batch of {len(batch)} deletion executed successfully for datim_ids: {batch}")
        logger.info('Deletion of json files completed')
        delete_end_time = datetime.now()
        q_check_count = """select count(*) from file_deletion_log 
        where  
        deletion_start_time >=  %s and deletion_end_time <=  %s
        """
        cur2.execute(q_check_count, (delete_start_time, delete_end_time))
        records_processed = cur2.fetchall()[0]
        update_pipeline_query = """update file_ingestion_pipeline_log set end_time=  %s, status =  %s, error_message=  %s, records_processed=  %s
        where log_id =  %s
        """ 
        cur.execute(update_pipeline_query, (delete_end_time, 'Job Passed', 'No Errors', records_processed, log_id))
        conn.commit()
        logger.info('Deletion Job for decrypted files was run successfully completed')

    except Exception as e:
        error_msg =str(e)
        end_time = datetime.now()
        logger.error(error_msg) 
        conn.commit()
        
    
    conn.commit()
    cur.close()
    conn2.commit()

if __name__ == '__main__':
    main()
