import json 
import psycopg2
import os
from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine, JSON, Integer, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from src import logger
import configparser
from database_connection.db_connect import connect_to_db

class FileDelete:
    def __init__(self):
        self.facility_id = None
        self.syncfile_entryID = None
        self.demo_path = '/home/lamisplus/server/temp'
        self.count_of_df = 0
        self.delete_end_time = None
        self.delete_start_time = None
            
    def _insert_into_log(self,tableName, fileName, facilityId):
        conn= connect_to_db.connect('filedb')[0]
        cur = conn.cursor()
        deletion_start_time = self.delete_start_time
        deletion_status_check = 'processing'
        table_name = tableName
        file_name = fileName
        facility_id = facilityId

        insert_query = """insert into file_deletion_log 
        (deletion_start_time, deletion_status_check, table_name, file_name, facility_id) 
        values ('{}','{}','{}','{}', '{}') RETURNING id""".format(deletion_start_time, deletion_status_check, table_name, file_name, facility_id)

        cur.execute(insert_query)
        #logger.info("inserted successfully")
        log_id =  cur.fetchall()[0][0]
        conn.commit()
        cur.close()
        return log_id
    def count_rows_in_json_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return len(data)
                elif isinstance(data, dict):
                    return len(data.keys())
                else:
                    return 0
        except UnicodeDecodeError as e:
            logger.error(f"UnicodeDecodeError while reading file {file_path}: {e}")
            return 0
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError while parsing file {file_path}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error while reading {file_path}: {e}")
            return 0


    # def count_rows_in_json_file(self, file_path):
    #     try:
    #         with open(file_path, 'r') as file:
    #             try:
    #                 data = json.load(file)
    #                 num_rows = len(data)
    #                 return num_rows

    #             except json.JSONDecodeError as e:
    #                 #logger.info(f"Error decoding JSON file {os.path.basename(file_path)}: {str(e)}")
    #                 logger.exception(e)
    #                 return 0

    #     except Exception as e:
    #         logger.exception(e)
    #         #logger.info(f"No such file or directory {os.path.basename(file_path)}: {str(e)}")
    #         return 0


    def count_rows_in_json_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    num_rows = len(data)
                    return num_rows

                except json.JSONDecodeError as e:
                    #logger.info(f"Error decoding JSON file {os.path.basename(file_path)}: {str(e)}")
                    logger.exception(e)
                    return 0

        except Exception as e:
            logger.exception(e)
            #logger.info(f"No such file or directory {os.path.basename(file_path)}: {str(e)}")
            return 0

    def _update_log(self, id, proc_status, file_name, tab_count, error_msg):
            conn=connect_to_db.connect('filedb')[0]
            cur = conn.cursor()
            deletion_end_time = self.delete_end_time
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
            logger.info(f'file_deletion_log updated successfully for {file_name}')

    def _process_derive_tablename(self, file_path):
            filename = os.path.basename(file_path)
            parts = filename.split('_')
            non_digit_parts = [part for part in parts if not part.isdigit() and part != 'decrypted.json']
            result=[]
            result.append('_'.join(non_digit_parts))
            check_path = result[0]
            #logger.info(check_path)
            return check_path
    
    def delete_encrypted_files(self):
        # Connect to the database
        conn = connect_to_db.connect('filedb')[0]
        cur = conn.cursor()
        retrieve_query = """SELECT sf.facility_id, sf.file_name
                        FROM public.sync_file sf
                        WHERE sf.processed IN (2, -2)
                            AND sf.modified_date BETWEEN '2025-08-01' AND CURRENT_DATE -- INTERVAL '1 DAYS'
                            AND sf.ingest_end_time IS NOT NULL
                            AND sf.file_name IS NOT NULL
                            AND NOT EXISTS (
                            SELECT 1
                            FROM public.file_deletion_log fdl
                            WHERE fdl.file_name = sf.file_name
                            AND fdl.deletion_status_check IN ('success', 'failed')
                            AND fdl.file_name NOT ILIKE '%_decrypted%')
                        """
        cur.execute(retrieve_query)

        # Fetch all file associated data from sync_file
        files = cur.fetchall()
        if files:
            logger.info(f"Number of files to delete: {len(files)}")
            for file in files:
                self.delete_start_time = datetime.now()
                self.facility_id = file[0]
                encryptedjson_file_name = file[1]
                decryptedjson_file_name = file[1].replace('.json', '_decrypted.json')
                encrypted_local_dir = os.path.join(self.demo_path,self.facility_id,encryptedjson_file_name)
                decrypted_local_dir = os.path.join(self.demo_path,self.facility_id,decryptedjson_file_name)
                encrypted_filelog_id = self._insert_into_log(self._process_derive_tablename(encrypted_local_dir), encryptedjson_file_name, self.facility_id)
                decrypted_filelog_id = self._insert_into_log(self._process_derive_tablename(decrypted_local_dir), decryptedjson_file_name, self.facility_id)

                if os.path.exists(encrypted_local_dir):
                    logger.info(f"File: {encrypted_local_dir} exists")
                    try:
                        encrypted_count_of_df = 0 #self.count_rows_in_json_file(decrypted_local_dir)
                        os.remove(encrypted_local_dir)
                        logger.info(f"File deleted: {encrypted_local_dir}")
                        self.delete_end_time = datetime.now()
                        self._update_log(encrypted_filelog_id,'success',encryptedjson_file_name,encrypted_count_of_df, 'no errors')
                    except PermissionError as e:
                        logger.error(f"Permission error deleting {encrypted_local_dir}: {str(e)}")
                        self.delete_end_time=datetime.now()
                        self._update_log(encrypted_filelog_id,'failed',encryptedjson_file_name,self.count_of_df,f"Permission error: {str(e)}")
                else:
                    logger.error(f"File {encrypted_local_dir} not found")
                    self.delete_end_time = datetime.now()
                    self._update_log(encrypted_filelog_id,'failed',encryptedjson_file_name,self.count_of_df,'file not found')

                if os.path.exists(decrypted_local_dir):
                    logger.info(f"File: {decrypted_local_dir} exists")
                    try:
                        decrypted_count_of_df = 0 # self.count_rows_in_json_file(decrypted_local_dir)
                        os.remove(decrypted_local_dir)
                        logger.info(f"File deleted: {decrypted_local_dir}")
                        self.delete_end_time = datetime.now()
                        self._update_log(decrypted_filelog_id,'success',decryptedjson_file_name,decrypted_count_of_df, 'no errors')
                    except PermissionError as e:
                        logger.error(f"Permission error deleting {decrypted_local_dir}: {str(e)}")
                        self.delete_end_time=datetime.now()
                        self._update_log(decrypted_filelog_id,'failed',decryptedjson_file_name,decrypted_count_of_df,f"Permission error: {str(e)}")
                else:
                    logger.error(f"File {decrypted_local_dir} not found")
                    self.delete_end_time = datetime.now()
                    self._update_log(decrypted_filelog_id,'failed',decryptedjson_file_name,self.count_of_df,'file not found')
                    
                logger.info('----------------------------------------------------------------------------------------------')

            # Commit the changes and close the connection
            conn.commit()
            cur.close()
            conn.close()
