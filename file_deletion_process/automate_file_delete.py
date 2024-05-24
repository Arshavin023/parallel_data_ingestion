import psycopg2
import os
from datetime import datetime
from src import logger

def _db_connect_filedb():
        db_params = {
        'host': 'localhost',
        'database': 'filedb',
        'user': 'lamisplus',
        'password': '37EpE&U&H?',
        'port': '5432',
         }

         # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_params)
        return conn

def _db_connect_lamisplus_staging_dwh():
        db_params = {
        'host': 'localhost',
        'database': 'lamisplus_staging_dwh',
        'user': 'lamisplus',
        'password': '37EpE&U&H?',
        'port': '5432',
         }

         # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_params)
        return conn
        
def _insert_into_log(tableName, fileName, facilityId):
        conn=_db_connect_filedb()
        cur = conn.cursor()
        deletion_start_time = datetime.now()
        deletion_status_check = 'processing'
        table_name = tableName
        file_name = fileName
        facility_id = facilityId

        insert_query = """insert into file_deletion_log 
        (deletion_start_time, deletion_status_check, table_name, file_name, facility_id) 
        values ('{}','{}','{}','{}', '{}') RETURNING id""".format(deletion_start_time, deletion_status_check, table_name, file_name, facility_id)

        cur.execute(insert_query)
        logger.info("inserted successfully")
        log_id =  cur.fetchall()[0][0]
        conn.commit()
        cur.close()
        return log_id

def count_rows_in_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                num_rows = len(data)
                return num_rows

            except json.JSONDecodeError as e:
                logger.info(f"Error decoding JSON file {os.path.basename(file_path)}: {str(e)}")
                logger.exception(e)
                return 0

    except Exception as e:
        logger.exception(e)
        logger.info(f"No such file or directory {os.path.basename(file_path)}: {str(e)}")
        return 0

def _update_log(id, proc_status, file_name, tab_count, error_msg):
        conn=_db_connect_filedb()
        cur = conn.cursor()

        deletion_end_time = datetime.now()
        deletion_status_check = proc_status

        update_query = """UPDATE file_deletion_log 
                        SET deletion_end_time =  %s,
                        deletion_status_check =  %s, json_rec_count =  %s, error_message = %s
                        WHERE id =  %s
                        """

        cur.execute(update_query,(deletion_end_time, deletion_status_check, 
                                  tab_count, error_msg, id))
        conn.commit()
        cur.close()
        logger.info(f'{file_name} log updated successfully')

def _process_derive_tablename(file_path):
        print("processing file")
        filename = os.path.basename(file_path)
        parts = filename.split('_')
        non_digit_parts = [part for part in parts if not part.isdigit() and part != 'decrypted.json']
        result=[]
        result.append('_'.join(non_digit_parts))
        check_path = result[0]
        logger.info(check_path)
        return check_path

#_process_derive_tablename(' /home/lamisplus/server/temp/kEoPeO75AG2/base_organisation_unit_0_20240129190716_decrypted.json')
        
def delete_stg_table_records():

    try:
        conn = _db_connect_filedb()
        cur = conn.cursor()
        retrieve_query = """SELECT facility_id, decrypted_file_name
                            FROM public.sync_file 
                            WHERE ingest_end_time <= CURRENT_DATE - INTERVAL '30' DAY
                            AND processed IN (2) 
                            AND ingest_status_check = 'success' 
                            AND ingest_error_message = 'No errors' 
                            AND decrypted_file_name NOT IN (
                                SELECT REPLACE(file_name, '_decrypted.json', '.json') 
                                FROM file_deletion_log 
                                WHERE deletion_status_check = 'success' 
                                OR error_message = 'file not found') 
                            ORDER BY create_date ASC
                            LIMIT 30000
                            """
        delete_query = """ DELETE FROM %s 
                           WHERE stg_load_time <= CURRENT_DATE - INTERVAL '105' DAY 
                       """
        cur.execute(retrieve_query)

        # Fetch all file associated data from sync_file
        files = cur.fetchall()

        for file in files:
            encryptedjson_file_name = file[1]
            parts = encryptedjson_file_name.split('_')
            non_digit_parts = [part for part in parts if not part.isdigit() and part != 'decrypted.json']
            staging_table = '_'.join(non_digit_parts)

            try:
                cur.execute(delete_query,(staging_table))
                logger.info(f'records successfully deleted from {staging_table} table')

            except Exception as e:
                logger.exception(e)

        # Commit the changes and close the connection
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {str(e)}")


def delete_ingested_decrypted_files():

    try:
        conn = _db_connect_filedb()
        cur = conn.cursor()
        retrieve_query = """SELECT facility_id, decrypted_file_name
                            FROM public.sync_file 
                            WHERE ingest_end_time <= CURRENT_DATE - INTERVAL '30' DAY
                            AND processed IN (2, -2) 
                            AND ingest_status_check = 'success' 
                            AND ingest_error_message = 'No errors' 
                            AND decrypted_file_name NOT IN (
                                SELECT REPLACE(file_name, '_decrypted.json', '.json') 
                                FROM file_deletion_log 
                                WHERE deletion_status_check = 'success' 
                                OR error_message = 'file not found') 
                            ORDER BY ingest_end_time ASC
                            LIMIT 30000
                            """
        cur.execute(retrieve_query)

        # Fetch all file associated data from sync_file
        files = cur.fetchall()
        #print(files)
        demo_path = '/home/lamisplus/server/temp'
        for file in files:
            logger.info(file)
            facility_id = file[0]
            decryptedjson_file_name = file[1].replace('.json', '_decrypted.json')
            # file_name = 
            local_dir = os.path.join(demo_path,facility_id,decryptedjson_file_name)

            filelog_id = _insert_into_log(_process_derive_tablename(local_dir), decryptedjson_file_name, facility_id)

            file_count = count_rows_in_json_file(local_dir)
            logger.info(file_count)

            try:
                # Check if the file exists before attempting to delete
                if os.path.exists(local_dir):
                    logger.info(f"{local_dir} file exists, deleting files...........\n\n")

                    os.remove(local_dir)
                    logger.info(f"File deleted: {local_dir}")
                    # update deletion log
                    _update_log(filelog_id, 'success', decryptedjson_file_name,file_count, 'no errors')

                else:
                    logger.info(f"File not found: {local_dir}")
                    _update_log(filelog_id, 'failed', decryptedjson_file_name,file_count, 'file not found')

            except Exception as e:
                logger.info(f"Error deleting file {local_dir}: {str(e)}")
                _update_log(filelog_id, 'failed', decryptedjson_file_name,file_count, str(e))

        # Commit the changes and close the connection
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        logger.info(f"Error: {str(e)}")
    

def delete_encrypted_files():

    try:
        conn = _db_connect_filedb()
        cur = conn.cursor()
        retrieve_query = """SELECT facility_id, decrypted_file_name
                            FROM public.sync_file 
                            WHERE create_date <= CURRENT_DATE - INTERVAL '90' DAY
                            AND processed IN (2, -2) 
                            AND ingest_status_check = 'success' 
                            AND ingest_error_message = 'No errors' 
                            AND decrypted_file_name NOT IN (
                                SELECT REPLACE(file_name, '_decrypted.json', '.json') 
                                FROM file_deletion_log 
                                WHERE deletion_status_check = 'success' 
                                OR error_message = 'file not found') 
                            ORDER BY create_date ASC
                            LIMIT 30000
                            """
        cur.execute(retrieve_query)

        # Fetch all file associated data from sync_file
        files = cur.fetchall()
        #print(files)
        demo_path = '/home/lamisplus/server/temp'
        for file in files:
            logger.info(file)
            facility_id = file[0]
            encryptedjson_file_name = file[1]
            # file_name = 
            local_dir = os.path.join(demo_path,facility_id,encryptedjson_file_name)

            filelog_id = _insert_into_log(_process_derive_tablename(local_dir), encryptedjson_file_name, facility_id)

            file_count = count_rows_in_json_file(local_dir)
            logger.info(file_count)

            try:
                # Check if the file exists before attempting to delete
                if os.path.exists(local_dir):
                    logger.info(f"{local_dir} file exists, deleting files...........\n\n")

                    os.remove(local_dir)
                    logger.info(f"File deleted: {local_dir}")
                    # update deletion log
                    _update_log(filelog_id, 'success', encryptedjson_file_name,file_count, 'no errors')

                else:
                    logger.info(f"File not found: {local_dir}")
                    _update_log(filelog_id, 'failed', encryptedjson_file_name,file_count, 'file not found')

            except Exception as e:
                logger.info(f"Error deleting file {local_dir}: {str(e)}")
                _update_log(filelog_id, 'failed', encryptedjson_file_name,file_count, str(e))

        # Commit the changes and close the connection
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        logger.exception(e)
