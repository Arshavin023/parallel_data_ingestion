import os
import re
import sys
import json
import uuid
import numpy as np
import psycopg2
from psycopg2 import ProgrammingError
from psycopg2.errors import UndefinedColumn
from sqlalchemy.exc import ProgrammingError as SAProgrammingError
from psycopg2.extras import Json, execute_values
import pandas as pd
from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine, JSON, Integer, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
# from database_connection import connect_to_db_v2 as connect_to_db
from database_connection import connect_to_db

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import logger


NO_ERRORS = 'No errors'
file_directory = os.environ.get('FILE_DIRECTORY')
pd.set_option('display.max_columns', None)

class FileLoader:
    def __init__(self):
        self.facility_id = None
        self.syncfile_entryID = None
        self.demo_path = file_directory
        self.count_of_df = 0
        self.load_end_time = None
        self.load_start_time = None

    def _get_and_map_cols(self, conn, table_name):
        '''
        Retrieves column names and their corresponding data types from the specified table.
        Uses the shared `conn` provided by the caller.
        '''
        try:
            cur = conn.cursor()

            retrieve_query = f"""SELECT column_name, data_type
                                FROM information_schema.columns
                                WHERE table_catalog = 'lamisplus_staging_dwh'
                                AND table_schema = 'public'
                                AND table_name = 'stg_{table_name}' """

            cur.execute(retrieve_query)
            columns = cur.fetchall()
            column_datatype_mapping = {name: type_ for name, type_ in columns}
            column_list = [i[0] for i in columns]
            cur.close()
            
            return column_datatype_mapping, column_list
        
        except Exception as e:
            logger.exception(e)
            raise e


    def _insert_into_log(self, conn, file_path, tablename):
        '''
        Inserts a new record into the file_ingestion_log table.
        Uses the shared `conn` provided by the caller.
        '''
        try:
            cur = conn.cursor()
            self.load_start_time = datetime.now()
            load_status_check = 'processing'
            table_name = f'stg_{tablename}'
            file_name = os.path.basename(file_path)
            facility_id = self.facility_id

            insert_query = """INSERT INTO file_ingestion_log 
                            (load_start_time, load_status_check, table_name, file_name, facility_id) 
                            VALUES (%s, %s, %s, %s, %s)"""
            cur.execute(insert_query, (self.load_start_time, load_status_check, table_name, file_name, facility_id))
            conn.commit()
            cur.close()
            logger.info('(successfully inserted records into file_ingestion_log')
            
        except Exception as e:
            logger.exception(e)
            raise e 


    def _fakeupsert_synclog(self, conn, decrypted_file_name, staging_table):
        '''
        Performs a fake upsert operation on the sync_file table.
        Uses the shared `conn` provided by the caller (filedb target).
        '''
        try:
            cur = conn.cursor()
            fakeupsert_query = """UPDATE sync_file 
                                SET ingest_start_time = %s, 
                                    ingest_file_name = %s, 
                                    ingest_table_name = %s
                                WHERE id = %s
                                """
            self.load_start_time = datetime.now()
            cur.execute(fakeupsert_query, (self.load_start_time, decrypted_file_name, staging_table, 
                                           self.syncfile_entryID))
            conn.commit()
            cur.close()
            logger.info('successfully updated start_time, file_name and stg_table in sync_file')

        except Exception as e:
            logger.exception(e)
            raise e 


    def _update_log(self, conn, proc_status, file_name, tab_count, error_msg):
        '''
        Updates the file ingestion log with the processing status and details.
        Uses the shared `conn` provided by the caller (staging target).
        '''
        try:
            cur = conn.cursor()
            load_status_check = proc_status
            update_query = """UPDATE file_ingestion_log 
                            SET load_end_time = %s,
                                load_status_check = %s,
                                json_rec_count = %s,
                                error_message = %s
                            WHERE file_name = %s"""
            cur.execute(update_query, (self.load_end_time, load_status_check, 
                                    tab_count, error_msg, file_name))
            conn.commit()
            cur.close()
            logger.info('file ingestion_log successfully updated')
        
        except Exception as e:
            logger.exception(e)
            raise e


    def _update_flag_syncfile(self, conn, proc_status, proc_val, tab_count, error_msg):  
        '''
        Updates the synchronization file log with processing status and details.
        Uses the shared `conn` provided by the caller (filedb target).
        '''  
        try: 
            cur = conn.cursor()
            ingest_status_check = proc_status
            update_query = """UPDATE sync_file 
                            SET processed = %s,
                                ingest_end_time = %s,
                                ingest_status_check = %s,
                                json_rec_count = %s,
                                ingest_error_message = %s
                            WHERE id = %s AND facility_id = %s
                            """
            self.load_end_time = datetime.now()
            cur.execute(update_query, (proc_val, self.load_end_time, ingest_status_check, 
                                    tab_count, error_msg[0:10000], self.syncfile_entryID,
                                    self.facility_id))
            conn.commit()
            cur.close()
            logger.info(f'Sync File log updated for {self.facility_id} successfully')

        except Exception as e:
            logger.exception(e)
            raise e
        

    def _update_centralpartnermapper(self, filedb_conn, staging_conn):   
        '''
        Updates the central partner mapping with the count of patients per facility.
        Accepts both destination connections to handle cross-database dependency safely.
        '''
        try:
            # Query the staging database connection
            cur_staging = staging_conn.cursor()
            get_patient_count = """
            SELECT COUNT(DISTINCT uuid) AS p_count 
            FROM stg_patient_person
            WHERE stg_datim_id = %s and archived=0
            """
            cur_staging.execute(get_patient_count, (self.facility_id,))
            p_count_per_datemid = cur_staging.fetchone()[0]
            cur_staging.close()

            # Write out to the filedb database connection
            cur_filedb = filedb_conn.cursor()
            update_query = """UPDATE central_partner_mapping 
                            SET patient_count = %s
                            WHERE datim_id = %s
                        """
            cur_filedb.execute(update_query, (p_count_per_datemid, self.facility_id,))
            filedb_conn.commit()
            cur_filedb.close()
            logger.info(f'Central Partner Mapping updated for {self.facility_id} successfully')

        except Exception as e:
            logger.exception(e)
            raise e
        

    def _retrieve_localdir_from_syncfile(self, facility_id):
        '''
        Retrieves local directories from the sync_file table.
        Establishes ONE connection per context contextually, reusing them down the stack.
        '''
        retrieve_query = """
        SELECT id, facility_id, decrypted_file_name 
        FROM sync_file 
        WHERE processed = 1
        AND modified_date >= '2026-01-01 00:00:00'
        AND facility_id = %s
        """
        
        # Open one connection for 'filedb' and one connection for 'lamisplus_staging_dwh' 
        # to process the entire execution context safely
        with connect_to_db.connect('filedb')[0] as filedb_conn, \
             connect_to_db.connect('lamisplus_staging_dwh')[0] as staging_conn:
                 
            try:
                with filedb_conn.cursor() as cur:
                    cur.execute(retrieve_query, (facility_id,))
                    files = cur.fetchall()

                for file in files:
                    self.syncfile_entryID = file[0]
                    self.facility_id = file[1]
                    encrypted_file_name = file[2]
                    decrypted_file_name = encrypted_file_name.replace('.json', '_decrypted.json')
                    local_dir = os.path.join(self.demo_path, self.facility_id, decrypted_file_name)
                    tablename = self._process_derive_tablename(local_dir)
                    staging_table = f'stg_{tablename}'

                    file_exists = os.path.exists(local_dir)

                    if file_exists and self._wait_until_file_stable(local_dir):
                        logger.info('----------------------------s-------------------------------------------------')
                        logger.info(f"The file '{local_dir}' exists.")
                        self._fakeupsert_synclog(filedb_conn, decrypted_file_name, staging_table)
                        self._process_file_by_name(filedb_conn, staging_conn, local_dir)
                    elif file_exists:
                        # File exists but never stopped growing within the timeout window -
                        # do NOT mark this as loaded/successful, leave it for the next run to retry.
                        self._fakeupsert_synclog(filedb_conn, decrypted_file_name, staging_table)
                        logger.warning(f"The file '{local_dir}' exists but never stabilized. Skipping for now, will retry next run.")
                        self.load_end_time = datetime.now()
                        self._update_flag_syncfile(filedb_conn, 'failed', -2, 0, f'{decrypted_file_name} did not finish writing to disk in time; will retry next run')
                    else:
                        self._fakeupsert_synclog(filedb_conn, decrypted_file_name, staging_table)
                        logger.info(f"The file '{local_dir}' does not exist. Skipping to next file")
                        self.load_end_time = datetime.now()
                        self._update_flag_syncfile(filedb_conn, 'loaded in the past', 2, 0, NO_ERRORS)
                        
                logger.info('json files successfully processed')

            except Exception as e:
                logger.exception(e)
                raise e


    def _process_derive_tablename(self, file_path):
        '''
        Processes the filename to derive the corresponding table name.
        '''
        try:
            logger.info("Processing file")
            filename = os.path.basename(file_path)
            parts = filename.split('_')
            non_digit_parts = [part for part in parts if not part.isdigit() and part != 'decrypted.json']
            return '_'.join(non_digit_parts)
        
        except Exception as e:
            logger.exception(e)
            raise e


    def _wait_until_file_stable(self, file_path, checks=3, interval=0.5, timeout=15):
        '''
        Confirms a file exists AND has stopped growing before we try to read it.
        Guards against reading a file that's still mid-write (e.g. still being
        decrypted) which was producing spurious ValueErrors on larger files.
        Returns True if the file's size was stable across `checks` consecutive
        polls, False if it never stabilized within `timeout` seconds.
        '''
        import time
        start = time.time()
        last_size = -1
        stable_count = 0

        while time.time() - start < timeout:
            if not os.path.exists(file_path):
                time.sleep(interval)
                continue

            try:
                current_size = os.path.getsize(file_path)
            except OSError:
                time.sleep(interval)
                continue

            if current_size > 0 and current_size == last_size:
                stable_count += 1
                if stable_count >= checks:
                    return True
            else:
                stable_count = 0

            last_size = current_size
            time.sleep(interval)

        logger.warning(f"File '{file_path}' did not stabilize within {timeout}s")
        return False


    def _check_if_previouslyloaded(self, conn, file_name, facility_id):
        '''
        Checks if a file has been previously loaded successfully into the database.
        Uses the shared staging connection `conn`.
        '''
        try:
            cur = conn.cursor()
            check_query = """SELECT COUNT(*) FROM file_ingestion_log 
                            WHERE file_name = %s AND facility_id = %s AND load_status_check = 'success' """
            
            cur.execute(check_query, (file_name, facility_id))
            count = cur.fetchone()[0]
            cur.close()

            return count > 0
        
        except Exception as e:
            logger.exception(e)
            raise e


    def _check_if_faillogged(self, conn, file_name, facility_id):
        '''
        Checks if a file has been previously failed to load into the database.
        Uses the shared staging connection `conn`.
        '''
        try:
            cur = conn.cursor()
            check_query = """SELECT COUNT(*) FROM file_ingestion_log 
                            WHERE file_name = %s AND facility_id = %s 
                            AND load_status_check = 'failed' """
            cur.execute(check_query, (file_name, facility_id))
            count = cur.fetchone()[0]
            cur.close()
            return count > 0
        except Exception as e:
            logger.exception(e)
            raise e 

    def format_programming_error(self, e, max_length=500):
        """Format and truncate large ProgrammingError messages."""
        error_type = type(e).__name__
        args_str = ' '.join(map(str, e.args))
        
        lines = args_str.replace("psycopg2.errors.", "").replace("stg_", "").split('\n')
        cleaned_message = lines[0]
        
        if len(cleaned_message) > max_length:
            cleaned_message = cleaned_message[:max_length] + '... [truncated]'
        
        return f'{error_type} - {cleaned_message}'


    def _process_file_by_name(self, filedb_conn, staging_conn, file_path):
        '''
        Processes a file based on its name.
        Requires active target database connection instances to be passed explicitly.
        '''
        check_param = self._process_derive_tablename(file_path)
        file_name = os.path.basename(file_path)
        is_loaded_success = self._check_if_previouslyloaded(staging_conn, file_name, self.facility_id)
        is_loaded_failed = self._check_if_faillogged(staging_conn, file_name, self.facility_id)

        if is_loaded_success:
            self.load_end_time = datetime.now()
            logger.info(f"The file {file_name} has been previously loaded successfully")
            self._update_flag_syncfile(filedb_conn, 'success', 2, self.count_of_df, NO_ERRORS)  
            logger.info('Sync log has been updated successfully')

        elif is_loaded_failed:
            logger.info(f'{file_name} previously failed to load')
            try:
                parse_dates = ['date_of_birth']
                staging_table = f'stg_{check_param}'
                logger.info(f'{file_name} attempting to reload')
                self._ingest_json_data(filedb_conn, staging_conn, file_path, staging_table, 
                                       dtype=self._get_and_map_cols(staging_conn, check_param)[0], 
                                       parse_dates=parse_dates)

            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                
                if error_type == 'ProgrammingError':
                    error_msg = self.format_programming_error(e)
                    logger.error(f'ProgrammingError encountered: {error_msg}')
                else:
                    args_str = ' '.join(map(str, e.args))
                    cleaned_message = args_str.split('\n')[0]
                    error_msg = f'{error_type} - {error_msg} - {cleaned_message}'
                    logger.error(f'Unexpected error encountered: {error_msg}')
                
                self.load_end_time = datetime.now()
                self._update_log(staging_conn, 'failed', file_name, self.count_of_df, error_msg)
                self._update_flag_syncfile(filedb_conn, 'failed', -2, self.count_of_df, error_msg)
                logger.error(f'Error processing {check_param} file: {file_name} - {error_msg}')

        else:
            logger.info(f'{file_name} yet to be loaded')
            self._insert_into_log(staging_conn, file_path, check_param)
            logger.info(f'{file_name} logs inserted into file_ingestion_log')
            
            try:
                parse_dates = ['date_of_birth']
                staging_table = f'stg_{check_param}'
                logger.info(f'{file_name} attempting to load')
                self._ingest_json_data(filedb_conn, staging_conn, file_path, staging_table, 
                                       dtype=self._get_and_map_cols(staging_conn, check_param)[0], 
                                       parse_dates=parse_dates)

            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                
                if error_type == 'ProgrammingError':
                    error_msg = self.format_programming_error(e)
                    logger.error(f'ProgrammingError encountered: {error_msg}')
                else:
                    args_str = ' '.join(map(str, e.args))
                    cleaned_message = args_str.split('\n')[0]
                    error_msg = f'{error_type} - {error_msg} - {cleaned_message}'
                    logger.error(f'Unexpected error encountered: {error_msg}')
                
                self.load_end_time = datetime.now()
                self._update_log(staging_conn, 'failed', file_name, self.count_of_df, error_msg)
                self._update_flag_syncfile(filedb_conn, 'failed', -2, self.count_of_df, error_msg)
                logger.error(f'Error processing {check_param} file: {file_name} - {error_msg}')

        if check_param == 'patient_person':
            self._update_centralpartnermapper(filedb_conn, staging_conn)


    def _replace_empty_strings_with_null(self, df):
        '''
        Replaces empty strings or spaces with pandas' representation of missing values (NA).
        '''
        try:
            df.replace('', np.nan, inplace=True)
            df.replace(' ', np.nan, inplace=True)
            df.replace('null', np.nan, inplace=True)
            logger.info('" " successfully replace with NA')

        except Exception as e:
            logger.exception(e)
            raise e

    def _strip_nul_bytes(self, df):
        '''
        Postgres text/jsonb columns reject embedded NUL (0x00) bytes and raise
        ValueError deep inside psycopg2 on insert. Strip them from all
        object/string columns before insert so bad source data doesn't kill
        the whole batch with an unhelpful, hard-to-trace error.

        Only touches values that actually contain a NUL byte, and only logs
        when something was actually stripped - so the log is a real audit
        trail of which file/column/row was affected, not a blanket message
        that fires on every file regardless of whether anything was found.
        '''
        try:
            obj_cols = df.select_dtypes(include=['object']).columns
            affected = {}

            for col in obj_cols:
                mask = df[col].apply(lambda x: isinstance(x, str) and '\x00' in x)
                if mask.any():
                    affected[col] = df.index[mask].tolist()
                    df.loc[mask, col] = df.loc[mask, col].apply(lambda x: x.replace('\x00', ''))

            if affected:
                for col, rows in affected.items():
                    logger.warning(f"NUL bytes found and stripped in column '{col}', rows: {rows}")
            # else: nothing found, nothing logged - file was already clean

        except Exception as e:
            logger.exception(e)
            raise e
	
    def _date_validation(self, df):
        date_columns = [col for col in df.columns if col.startswith('date_') or col.endswith('_date')]
        if not date_columns:
            return {}, []
        problematic_dates = {}
        indexes_for_bad_dates = []
        for col in date_columns:
            try:
                pd.to_datetime(df[col], errors='raise')
            except (TypeError, ValueError) as e:
                problematic_dates[col] = []
                for idx, value in df[col].items():
                    try:
                        pd.to_datetime(value, errors='raise')
                    except (TypeError, ValueError):
                        indexes_for_bad_dates.append(idx)
                        problematic_dates[col].append(f'record {idx+1}, value => {value}')

                        record_id = df.at[idx, 'id']
                        indexes_for_bad_dates.append(idx)
                        problematic_dates[col].append(f'record id: {record_id}, invalid_date => {value}')
        
        return problematic_dates, indexes_for_bad_dates
    
    def mask_pii(self, json_str):
        data = json.loads(json_str)
        if 'surname' in data:
            data['surname'] = '******'
        if 'first_name' in data:
            data['first_name'] = '******'
        if 'middle_name' in data:
            data['middle_name'] = '******'
        if 'phone_number' in data:
            data['phone_number'] = '******'
        if 'hospital_number' in data:
            data['hospital_number'] = '******'
        
        return json.dumps(data)


    def _read_json_with_retry(self, file_path, parse_dates=None, max_attempts=3, delay=2):
        '''
        Wraps pd.read_json with a small bounded retry. Falls back to raising the
        last ValueError seen if every attempt fails, so the existing except
        ValueError block in _ingest_json_data still handles the final failure.
        '''
        import time
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                return pd.read_json(file_path, convert_dates=parse_dates)
            except ValueError as ve:
                last_error = ve
                logger.warning(f"Attempt {attempt}/{max_attempts} failed reading {file_path}: {ve}")
                if attempt < max_attempts:
                    time.sleep(delay)
        raise last_error


    def _ingest_json_data(self, filedb_conn, staging_conn, file_path, staging_table, dtype=None, parse_dates=None):
        '''
        Ingests JSON data into a specified staging table in the database.
        Uses the active context connections instead of creating new connection or engine bindings.
        '''
        load_time = datetime.now()
        batch_id = file_path.split('_')[-2]
        datim_id = self.facility_id
        file_name = file_path.split('/')[-1]
        encrypted_file_name = file_name.replace('_decrypted', '')

        try:
            df = self._read_json_with_retry(file_path, parse_dates=parse_dates)
            columns_to_exclude = ['ods_load_time', 'ods_datim_id']
            columns_to_include = [col for col in df.columns if col not in columns_to_exclude]
            df = df[columns_to_include]

            if df.empty:
                self._update_log(staging_conn, 'failed', file_name, 0, 'JSON file is empty')
                self._update_flag_syncfile(filedb_conn, 'failed', -2, 0, 'JSON file is empty')
                logger.info('Sync File Log updated successfully')
                return
            
            # Staging schema transformations
            if staging_table == 'stg_mhpss_confirmation':
                pass
            elif staging_table == 'stg_biometric':
                columns_to_exclude = ['match_person_uuid', 'match_biometric_id']
                columns_to_include = [col for col in df.columns if col not in columns_to_exclude]
                df = df[columns_to_include]
            elif staging_table == 'stg_hiv_enrollment':
                columns_to_exclude = ['target_group_id_original']
                columns_to_include = [col for col in df.columns if col not in columns_to_exclude]
                df = df[columns_to_include]
            elif staging_table == 'stg_hts_client':
                df['extra'] = df['extra'].apply(lambda x: {'type': x['type'], 'value': self.mask_pii(x['value'])})
            elif staging_table == 'stg_hts_index_elicitation':
                df['last_name'] = '******'
                df['first_name'] = '******'
                df['middle_name'] = '******'
                df['phone_number'] = '******'
                df['alt_phone_number'] = '******'
            elif staging_table == 'stg_patient_person':
                df['surname'] = '******'
                df['first_name'] = '******'
                df['other_name'] = '******'
                df['hospital_number'] = '******'
                df['nin_number'] = '******'
                df['full_name'] = '******'

            validation = self._date_validation(df)
            validation_result, bad_indexes = validation
            
            if validation_result:
                logger.info(f"The JSON file: {file_path} has invalid dates that will be filtered out")
                df = df.dropna(how='all')
                df['stg_batch_id'] = batch_id
                df['stg_load_time'] = load_time
                df['stg_file_name'] = file_name
                df['stg_datim_id'] = datim_id
                self._replace_empty_strings_with_null(df)
                self._strip_nul_bytes(df)
                valid_dates_df = df.drop(bad_indexes)
                
                self._execute_vectorized_batch_insert(staging_conn, staging_table, valid_dates_df)
                staging_conn.commit()
                
                self.count_of_df = len(valid_dates_df)
                self._update_log(staging_conn, 'failed', file_name, self.count_of_df, 'Few date errors spotted but files ingested')
                self._update_flag_syncfile(filedb_conn, 'failed', -2, self.count_of_df, f'{encrypted_file_name} has invalid dates: {validation_result}. Bad date records were filtered and {self.count_of_df} records successfully ingested')
                
                cur = staging_conn.cursor()
                ins_counts = """INSERT INTO stg_monitoring (datim_id, batch_id, file_name, table_name, load_time, json_rec_count, processed) 
                                VALUES (%s, %s, %s, %s, %s, %s, 'N')"""
                cur.execute(ins_counts, (datim_id, batch_id, file_name, staging_table, load_time, self.count_of_df))
                staging_conn.commit()
                cur.close()
            
            else:
                df = df.dropna(how='all')
                df['stg_batch_id'] = batch_id
                df['stg_load_time'] = load_time
                df['stg_file_name'] = file_name
                df['stg_datim_id'] = datim_id
                self._replace_empty_strings_with_null(df)
                self._strip_nul_bytes(df)
                
                self._execute_vectorized_batch_insert(staging_conn, staging_table, df)
                logger.info(f'{file_name} successfully ingested into {staging_table} table')
                staging_conn.commit()
                
                self.count_of_df = len(df)
                self._update_log(staging_conn, 'success', file_name, self.count_of_df, NO_ERRORS)
                self._update_flag_syncfile(filedb_conn, 'success', 2, self.count_of_df, NO_ERRORS)
                
                cur = staging_conn.cursor()
                ins_counts = """INSERT INTO stg_monitoring (datim_id, batch_id, file_name, table_name, load_time, json_rec_count, processed) 
                                VALUES (%s, %s, %s, %s, %s, %s, 'N')"""
                cur.execute(ins_counts, (datim_id, batch_id, file_name, staging_table, load_time, self.count_of_df))
                staging_conn.commit()
                cur.close()
            
        except ValueError as ve:
            error_detail = str(ve)[:500]
            self._update_log(staging_conn, 'failed', file_name, 0, f'Error processing JSON file: {file_name} - {error_detail}')
            self._update_flag_syncfile(filedb_conn, 'failed', -2, 0, f'Error processing JSON file: {encrypted_file_name} - {error_detail}')
            logger.info('Sync File Log updated successfully')
            logger.error(f"Error processing JSON file: {file_path} - {error_detail}")        
        except ProgrammingError as pe:
            error_msg = str(pe)
            match = re.search(r'column "(.*?)" of relation "(.*?)"', error_msg)
            if match:
                missing_column = match.group(1)
                missing_table = match.group(2).replace('stg_', '')
                logger.error(f"Missing column '{missing_column}' in table '{missing_table}'")
                self._update_log(staging_conn, 'failed', file_name, 0, f"Column '{missing_column}' in {encrypted_file_name} does not exists in '{missing_table}' table")
                self._update_flag_syncfile(filedb_conn, 'failed', -2, 0, f"Column '{missing_column}' in {encrypted_file_name} does not exists in '{missing_table}' table")
            else:
                logger.error(f"PostgreSQL ProgrammingError: {error_msg}")
                self._update_log(staging_conn, 'failed', file_name, 0, f'{file_name} has a DB error: {error_msg}')
                self._update_flag_syncfile(filedb_conn, 'failed', -2, 0, f'{encrypted_file_name} has a DB error: {error_msg}')
            logger.info('Sync File Log updated successfully')
        
        except UndefinedColumn as udc:
            error_msg = str(udc)
            match = re.search(r'column "(.*?)" of relation "(.*?)"', error_msg)
            if match:
                missing_column = match.group(1)
                missing_table = match.group(2).replace('stg_', '')
                logger.error(f"Missing column '{missing_column}' in table '{missing_table}'")
                self._update_log(staging_conn, 'failed', file_name, 0, f"Column '{missing_column}' in {encrypted_file_name} does not exist in '{missing_table}' table")
                self._update_flag_syncfile(filedb_conn, 'failed', -2, 0, f"Column '{missing_column}' in {encrypted_file_name} does not exist in '{missing_table}' table")
            else:
                logger.error(f"PostgreSQL UndefinedColumn error: {error_msg}")
                self._update_log(staging_conn, 'failed', file_name, 0, f'{file_name} has a DB error: {error_msg}')
                self._update_flag_syncfile(filedb_conn, 'failed', -2, 0, f'{encrypted_file_name} has a DB error: {error_msg}')

        except SAProgrammingError as sa_pe:
            orig = getattr(sa_pe, 'orig', None)
            if isinstance(orig, UndefinedColumn):
                error_msg = str(orig)
                match = re.search(r'column "(.*?)" of relation "(.*?)"', error_msg)
                if match:
                    missing_column = match.group(1)
                    missing_table = match.group(2).replace('stg_', '')
                    logger.error(f"Missing column '{missing_column}' in table '{missing_table}'")
                    self._update_log(staging_conn, 'failed', file_name, 0, f"Column '{missing_column}' in {encrypted_file_name} does not exist in '{missing_table}' table")
                    self._update_flag_syncfile(filedb_conn, 'failed', -2, 0, f"Column '{missing_column}' in {encrypted_file_name} does not exist in '{missing_table}' table")
                else:
                    logger.error(f"PostgreSQL UndefinedColumn error: {error_msg}")
                    self._update_log(staging_conn, 'failed', file_name, 0, f'{file_name} has a DB error: {error_msg}')
                    self._update_flag_syncfile(filedb_conn, 'failed', -2, 0, f'{encrypted_file_name} has a DB error: {error_msg}')
            else:
                logger.error(f"SQLAlchemy ProgrammingError (not UndefinedColumn): {str(sa_pe)}")
                self._update_log(staging_conn, 'failed', file_name, 0, f'{file_name} has a DB error: {str(sa_pe)}')
                self._update_flag_syncfile(filedb_conn, 'failed', -2, 0, f'{encrypted_file_name} has a DB error: {str(sa_pe)}')

        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
        logger.info('-------------------------------------------')


    @staticmethod
    def _sanitise_value(val):
        if val is pd.NaT:
            return None
        try:
            if pd.isna(val):
                return None
        except (TypeError, ValueError):
            pass

        if isinstance(val, np.integer):
            return int(val)
        if isinstance(val, np.floating):
            return None if np.isnan(val) else float(val)
        if isinstance(val, np.bool_):
            return bool(val)
        if isinstance(val, np.ndarray):
            return Json(val.tolist())
        if isinstance(val, (dict, list)):
            return Json(val)
        return val
    
    def _execute_vectorized_batch_insert(self, conn, table_name, df: pd.DataFrame):
        if df.empty:
            return

        columns = list(df.columns)
        column_identifiers = ", ".join(f'"{c}"' for c in columns)
        insert_query = f'INSERT INTO "{table_name}" ({column_identifiers}) VALUES %s'

        rows = [
            tuple(self._sanitise_value(val) for val in row)
            for row in df.itertuples(index=False, name=None)
        ]

        with conn.cursor() as cur:
            execute_values(cur, insert_query, rows, page_size=5000)

        logger.info(
            "Successfully inserted %d records into %s via execute_values.",
            len(rows), table_name,
        )