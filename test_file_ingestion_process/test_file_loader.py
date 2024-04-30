import os
import json
import uuid
import numpy as np
import psycopg2
from psycopg2.extras import Json
import pandas as pd
from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine, JSON, Integer, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from src import logger

pd.set_option('display.max_columns', None)

class FileLoader:
    def __init__(self):
        self.facility_id = None
        self.syncfile_entryID = None
        self.demo_path = '/home/lamisplus/server/temp'
        self.count_of_df = 0
        self.load_end_time = None
        self.load_start_time = None

    def _db_connect(self, database:str):
        '''
        Establishes a connection to the specified PostgreSQL database.
        Parameters:
        - database (str): The name of the database to connect to.
        Returns:
        - conn (psycopg2.connection): The connection object.
        - engine (sqlalchemy.engine.base.Engine): The SQLAlchemy engine object.
        Raises:
        - Exception: If connection to the database fails.
        '''
        db_params = {'host': 'localhost', 'database': database, 'user': 'lamisplus',
                     'password': '37EpE&U&H?','port': '5432',}
        try:
            conn = psycopg2.connect(**db_params)
            engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}')
            logger.info(f'successfully connected to {database} database')
            return [conn, engine]
        
        except Exception as e:
            logger.exception(e)
            raise e


    def _get_and_map_cols(self, table_name):
        '''
        Retrieves column names and their corresponding data types from the specified table.
        Parameters:
        - table_name (str): The name of the table.
        Returns:
        - column_datatype_mapping (dict): A dictionary mapping column names to their data types.
        - column_list (list): A list of column names.
        Raises:
        - Exception: If an error occurs while retrieving column information.
        '''
        try:
            conn = self._db_connect('lamisplus_staging_dwh')[0]
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
            conn.commit()
            cur.close()
            logger.info(f'successfully connected to retrieved column_datatype_mapping and column_list database')
            return column_datatype_mapping, column_list
        
        except Exception as e:
            logger.exception(e)
            raise e


    def _insert_into_log(self, file_path, tablename):
        '''
        Inserts a new record into the file_ingestion_log table with relevant details.
        Parameters:
        - file_path (str): The path of the file being ingested.
        - tablename (str): The name of the table being ingested.
        Raises:
        - Exception: If an error occurs while inserting the record into the file_ingestion_log table.
        '''
        try:
            conn = self._db_connect('lamisplus_staging_dwh')[0]
            cur = conn.cursor()
            self.load_start_time = datetime.now()
            load_status_check = 'processing'
            table_name = f'stg_{tablename}'
            file_name = os.path.basename(file_path)
            facility_id = self.facility_id

            insert_query = f"""INSERT INTO file_ingestion_log 
                            (load_start_time, load_status_check, table_name, file_name, facility_id) 
                            VALUES ('{self.load_start_time}', '{load_status_check}', '{table_name}', 
                            '{file_name}', '{facility_id}')"""
            cur.execute(insert_query)
            conn.commit()
            cur.close()
            logger.info('(successfully inserted records into file_ingestion_log')
            
        except Exception as e:
            logger.exception(e)
            raise e 


    def _fakeupsert_synclog(self, file_path, tablename):
        '''
        Performs a fake upsert operation on the sync_file table.
        This method updates an existing record in the sync_file table if it exists, or inserts a new one if it doesn't. 
        The record is identified by the syncfile_entryID attribute.
        Parameters:
        - file_path (str): The path of the file being ingested.
        - tablename (str): The name of the table being ingested.
        Raises:
        - Exception: If an error occurs while performing the fake upsert operation on the sync_file table.
        '''
        try:
            conn = self._db_connect('filedb')[0]
            cur = conn.cursor()
            ingest_status_check = 'processing'
            table_name = f'stg_{tablename}'
            file_name = os.path.basename(file_path)
            fakeupsert_query = """UPDATE sync_file 
                                SET ingest_start_time = %s, 
                                    ingest_file_name = %s, 
                                    ingest_table_name = %s, 
                                    ingest_status_check = %s
                                WHERE id = %s"""
            cur.execute(fakeupsert_query, (self.load_start_time, file_name, table_name, 
                                        ingest_status_check, self.syncfile_entryID))
            conn.commit()
            cur.close()
            logger.info('successfully updated sync_file records')

        except Exception as e:
            logger.exception(e)
            raise e 


    def _update_log(self, proc_status, file_name, tab_count, error_msg):
        '''
        Updates the file ingestion log with the processing status and details.
        This method updates the file_ingestion_log table with the end time of the file processing, processing status, 
        number of JSON records ingested, and any error message encountered during processing.
        Parameters:
        - proc_status (str): The processing status ('success' or 'failed').
        - file_name (str): The name of the file being ingested.
        - tab_count (int): The number of JSON records ingested.
        - error_msg (str): Any error message encountered during processing.
        Raises:
        - Exception: If an error occurs while updating the file ingestion log.
        '''
        try:
            conn = self._db_connect('lamisplus_staging_dwh')[0]
            cur = conn.cursor()
            self.load_end_time = datetime.now()
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


    def _update_flag_syncfile(self, proc_status, proc_val, tab_count, error_msg):  
        '''
        Updates the synchronization file log with processing status and details.
        This method updates the sync_file table with the processing status, end time of ingestion, 
        number of JSON records ingested, and any error message encountered during processing.
        Parameters:
        - proc_status (str): The processing status ('success' or 'failed').
        - proc_val (int): The processing value.
        - tab_count (int): The number of JSON records ingested.
        - error_msg (str): Any error message encountered during processing.
        Raises:
        - Exception: If an error occurs while updating the synchronization file log.
        '''  
        try: 
            conn = self._db_connect('filedb')[0]
            cur = conn.cursor()
            ingest_status_check = proc_status
            update_query = """UPDATE sync_file 
                            SET processed = %s,
                                ingest_end_time = %s,
                                ingest_status_check = %s,
                                json_rec_count = %s,
                                ingest_error_message = %s
                            WHERE id = %s"""
            cur.execute(update_query, (proc_val, self.load_end_time, ingest_status_check, 
                                    tab_count, error_msg, self.syncfile_entryID))
            conn.commit()
            cur.close()
            logger.info(f'Sync File log updated for {self.syncfile_entryID} successfully')

        except Exception as e:
            logger.exception(e)
            raise e
        

    def _update_centralpartnermapper(self):   
        '''
        Updates the central partner mapping with the count of patients per facility.
        This method retrieves the count of distinct UUIDs from the stg_patient_person table for a specific facility,
        then updates the central_partner_mapping table with the patient count.
        Raises:
        - Exception: If an error occurs while updating the central partner mapping.
        '''
        try:
            conn = self._db_connect('lamisplus_staging_dwh')[0]
            cur = conn.cursor()

            get_patient_count = """
            SELECT COUNT(DISTINCT uuid) AS p_count FROM stg_hiv_enrollment
            WHERE stg_datim_id = %s and archived=0
            """
            cur.execute(get_patient_count, (self.facility_id,))
            p_count_per_datemid = cur.fetchone()[0]
            cur.close()

            conn = self._db_connect('filedb')[0]
            cur = conn.cursor()
            update_query = """UPDATE central_partner_mapping 
                            SET patient_count = %s
                            WHERE datim_id = %s
                        """
            cur.execute(update_query, (p_count_per_datemid, self.facility_id,))
            conn.commit()
            cur.close()
            logger.info(f'Central Partner Mapping updated for {self.facility_id} successfully')

        except Exception as e:
            logger.exception(e)
            raise e
        

    def _retrieve_localdir_from_syncfile(self):
        '''
        Retrieves local directories from the sync_file table.
        This method connects to the filedb database to retrieve information about files from the sync_file table 
        that have been processed. It then iterates over the retrieved files, processes each file by calling the 
        _process_file_by_name method, and logs whether each file exists or not.
        Raises:
        - Exception: If an error occurs while retrieving or processing files from the sync_file table.
        '''
        try:
            conn = self._db_connect('filedb')[0]
            cur = conn.cursor()
            retrieve_query = """
            SELECT id, facility_id, decrypted_file_name 
            FROM sync_file WHERE processed = 1 and create_date >= '2024-03-21' 
            ORDER BY modified_date ASC
            LIMIT 30000"""
            cur.execute(retrieve_query)

            files = cur.fetchall()

            for file in files:
                self.syncfile_entryID = file[0]
                self.facility_id = file[1]
                decryptedjson_file_name = file[2].replace('.json', '_decrypted.json')
                local_dir = os.path.join(self.demo_path, self.facility_id, decryptedjson_file_name)

                if os.path.exists(local_dir):
                    logger.info('-----------------------------------------------------------------------------')
                    logger.info(f"The file '{local_dir}' exists.")
                    self._process_file_by_name(local_dir)
                else:
                    logger.info(f"The file '{local_dir}' does not exist. Skipping to next file")
                    pass
            cur.close()
            logger.info('json files successfully processed')

        except Exception as e:
            logger.exception(e)
            raise e


    def _process_derive_tablename(self, file_path):
        '''
        Processes the filename to derive the corresponding table name.
        This method extracts non-numeric parts from the filename of the given file_path and joins them to 
        derive the corresponding table name. It removes 'decrypted.json' if present.
        Args:
        - file_path (str): The path of the file to derive the table name from.
        Returns:
        - str: The derived table name.
        Raises:
        - Exception: If an error occurs during the processing of the file name.
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


    def _check_if_previouslyloaded(self, file_name, facility_id):
        '''
        Checks if a file has been previously loaded successfully into the database.
        This method queries the file_ingestion_log table in the lamisplus_staging_dwh database to check if a file 
        with the given file_name and facility_id has been successfully loaded previously.
        Args:
        - file_name (str): The name of the file to check.
        - facility_id (str): The ID of the facility associated with the file.
        Returns:
        - bool: True if the file has been previously loaded successfully, False otherwise.
        Raises:
        - Exception: If an error occurs during the database query.    
        '''
        try:
            conn = self._db_connect('lamisplus_staging_dwh')[0]
            cur = conn.cursor()
            check_query = """SELECT COUNT(*) FROM file_ingestion_log 
                            WHERE file_name = %s AND facility_id = %s AND load_status_check = 'success' """
            
            cur.execute(check_query, (file_name, facility_id))
            count = cur.fetchone()[0]
            cur.close()

            # If count is greater than 0, the file has been previously loaded
            return count > 0
        
        except Exception as e:
            logger.exception(e)
            raise e


    def _check_if_faillogged(self, file_name, facility_id):
        '''
        Checks if a file has been previously failed to load into the database.
        This method queries the file_ingestion_log table in the lamisplus_staging_dwh database to check if a file 
        with the given file_name and facility_id has previously failed to load.
        Args:
        - file_name (str): The name of the file to check.
        - facility_id (str): The ID of the facility associated with the file.
        Returns:
        - bool: True if the file has been previously failed to load, False otherwise.
        Raises:
        - Exception: If an error occurs during the database query.
        '''
        try:
            conn = self._db_connect('lamisplus_staging_dwh')[0]
            cur = conn.cursor()
            check_query = """SELECT COUNT(*) FROM file_ingestion_log 
                            WHERE file_name = %s AND facility_id = %s 
                            AND load_status_check = 'failed' """
            cur.execute(check_query, (file_name, facility_id))
            count = cur.fetchone()[0]
            cur.close()
            # If count is greater than 0, the file has been previously loaded
            return count > 0
        except Exception as e:
            logger.exception(e)
            raise e 


    def _process_file_by_name(self, file_path):
        '''
        Processes a file based on its name.
        This method handles the processing of a file identified by its file_path. It determines whether the file has been 
        previously loaded successfully or failed. If the file has been previously loaded successfully, it updates the sync 
        log accordingly. If the file has been previously failed to load or it's a new file, it inserts a new entry into 
        the file_ingestion_log table and performs a fake upsert in the sync_file table. Then, it attempts to ingest the 
        data from the file into the database table.
        Args:
        - file_path (str): The path of the file to process.
        Returns:
        - None
        Raises:
        - Exception: If an error occurs during file processing.
        '''
        check_param = self._process_derive_tablename(file_path)
        file_name = os.path.basename(file_path)
        is_loaded_success = self._check_if_previouslyloaded(file_name, self.facility_id)
        self.count_of_df = 0

        if is_loaded_success:
            self.load_end_time = None
            logger.info(f"The file {file_name} has been previously loaded successfully")
            self._update_flag_syncfile('success', 2, self.count_of_df, 'No errors')  
            logger.info('Sync log has been updated successfully')
        else:
            is_loaded_failed = self._check_if_faillogged(file_name, self.facility_id)
            if is_loaded_failed:
                logger.info(f'{file_name} previously failed to load')
            else:
                logger.info(f'{file_name} yet to be loaded')
                self._insert_into_log(file_path, check_param)
                logger.info(f'{file_name} logs inserted into file_ingestion_log')
                self._fakeupsert_synclog(file_path, check_param)
                logger.info(f'{file_name} logs updated into sync_file')
            
            try:
                parse_dates = ['date_of_birth']
                staging_table = f'stg_{check_param}'
                logger.info(f'{file_name} attempting to load')
                self._ingest_json_data(file_path, staging_table, dtype=self._get_and_map_cols(check_param)[0], parse_dates=parse_dates)
                logger.info(f'{file_name} successfully ingested into {staging_table} table')

            except Exception as e:
                # logger.exception(e)
                error_msg = str(e)
                error_type = type(e).__name__
                if error_type == 'UnicodeDecodeError':
                    error_msg = 'UnicodeDecodeError - File is corrupted and unreadable, kindly regenerate and re-upload'
                elif error_type == 'ProgrammingError':
                    logger.info(f'{error_type} = {e}')
                    args_str = ' '.join(map(str, e.args))
                    lines = args_str.replace("psycopg2.errors.", "")
                    lines = lines.replace("stg_", "")
                    lines = lines.split('\n')
                    cleaned_message = lines[0]
                    error_msg = f'{error_type} - {cleaned_message}'
                    logger.info(error_msg)
                else:
                    args_str = ' '.join(map(str, e.args))
                    error_msg = f'{error_type} - {error_msg}'
                    lines = args_str.split('\n')
                    cleaned_message = lines[0]
                    error_msg = f'{error_msg} - {cleaned_message}'
                    logger.info(error_msg)

                self._update_log('failed', file_name, self.count_of_df, error_msg)
                self._update_flag_syncfile('failed', -2, self.count_of_df, error_msg)
                print(f'Error processing {check_param} file: {file_name} - {error_msg}')

            if check_param == 'patient_person':
                self._update_centralpartnermapper()

                
    def _replace_empty_strings_with_null(self, df):
        '''
        Replaces empty strings or spaces with pandas' representation of missing values (NA) in the given DataFrame.
        Args:
            df (pandas.DataFrame): The DataFrame in which to replace empty strings.
        Returns:
            None
        Raises:
            Exception: If an error occurs during the replacement process.
        '''
        try:
        # Replace empty strings or spaces with NaN
            df.replace('', np.nan, inplace=True)
            df.replace(' ', np.nan, inplace=True)
            df.replace('null', np.nan, inplace=True)
            logger.info('" " successfully replace with NA')

        except Exception as e:
            logger.exception(e)
            raise e
  
    def _ingest_json_data(self, file_path, staging_table, dtype=None, parse_dates=None):
        '''
        Ingests JSON data into a specified staging table in the database.
        Args:
            file_path (str): The path to the JSON file.
            staging_table (str): The name of the staging table in the database.
            dtype (dict, optional): A dictionary mapping column names to PostgreSQL data types. Defaults to None.
            parse_dates (list, optional): A list of column names to parse as dates. Defaults to None.
        Returns:
            None
        Raises:
            Exception: If an error occurs during the ingestion process.
        '''
        try:
            conn, engine = self._db_connect('lamisplus_staging_dwh')[0], self._db_connect('lamisplus_staging_dwh')[1]
            load_time = datetime.now()
            batch_id = file_path.split('_')[-2]
            datim_id = self.facility_id
            file_name = file_path.split('/')[-1]
            

            # Define the type mapping function
            def convert_postgresql_to_sqlalchemy(data_type):
                type_mapping = {
                    'integer': Integer,
                    'bigint': Integer,
                    'smallint': Integer,
                    'character varying': String,
                    'text': String,
                    'numeric': Float,
                    'real': Float,
                    'double precision': Float,
                    'timestamp without time zone': DateTime,
                    'timestamp with time zone': DateTime,
                    'jsonb': JSONB,
                    'bytea': String,
                    'boolean': Boolean,
                    'uuid': String,
                    'date': DateTime,
                    # Add more mappings as needed
                }
                return type_mapping.get(data_type, String)
            
            # def load_dsd_into_postgres(file_path, staging_table, connection):
            #     with open(file_path, 'r') as f:
            #         data = json.load(f)

            #     # Establish a cursor
            #     cursor = connection.cursor()

            #     num_records_loaded = 0 # Initialize a variable to count the number of records loaded

            #     for record in data:
            #         # Assuming record is a dictionary where keys correspond to column names
            #         # For keys with nested structures, you may need to handle them accordingly
            #         columns = ', '.join(list(record.keys()) + ['stg_load_time', 'stg_batch_id', 'stg_datim_id', 'stg_file_name'])
            #         placeholders = ', '.join(['%s'] * (len(record) + 4))
            #         values = []

            #         for key, value in record.items():
            #             if value == "":
            #                 values.append(None)  # Set empty string to None for date fields
            #             elif isinstance(value, dict):
            #                 values.append(json.dumps(value))
            #             else:
            #                 values.append(value)

            #         # Add values for new columns
            #         values.extend([load_time, batch_id, datim_id, file_name])

            #         insert_query = f"INSERT INTO {staging_table} ({columns}) VALUES ({placeholders})"
            #         cursor.execute(insert_query, values)

            #         num_records_loaded += cursor.rowcount  # Increment the count by the number of records inserted in this iteration

            #     # Commit the transaction
            #     connection.commit()

            #     # Close the cursor
            #     cursor.close()

            #     return num_records_loaded
            
            # Convert PostgreSQL types to SQLAlchemy types for dif dtype is not None and isinstance(dtype, dict):
            dtype_mapping = {col: convert_postgresql_to_sqlalchemy(dtype[col]) for col in dtype}

            if staging_table == 'stg_dsd_devolvement':
                pass

            elif staging_table == 'stg_biometric':
                df = pd.read_json(file_path, convert_dates=parse_dates)
                # Specify columns to exclude
                columns_to_exclude = ['match_type','match_person_uuid','match_biometric_id']  
                columns_to_include = [col for col in df.columns if col not in columns_to_exclude]
                # Read JSON data into DataFrame, including only the specified columns
                df = df[columns_to_include]
                
                if df.empty:
                    logger.info(f"The JSON file is empty: {file_path}")
                    self._update_log('failed', file_name, 0, 'JSON file is empty')
                    self._update_flag_syncfile('failed', -2, 0, 'JSON file is empty')
                    return
                else:
                    df = df.dropna(how='all')
                    logger.info(len(df))
                    logger.info('Processing...')
                    df['stg_batch_id'] = batch_id
                    df['stg_load_time'] = load_time
                    df['stg_file_name'] = file_name
                    df['stg_datim_id'] = datim_id
                    self._replace_empty_strings_with_null(df)
                    df.to_sql(staging_table, con=engine, index=False, if_exists='append', 
                                dtype=dtype_mapping)
                    conn.commit()        
                self.count_of_df = len(df)
            
            elif staging_table == 'stg_patient_person':
                df = pd.read_json(file_path, convert_dates=parse_dates)
                if df.empty:
                    logger.info(f"The JSON file is empty: {file_path}")
                    self._update_log('failed', file_name, 0, 'JSON file is empty')
                    self._update_flag_syncfile('failed', -2, 0, 'JSON file is empty')
                    return
                else:
                    df = df.dropna(how='all')
                    logger.info(len(df))
                    logger.info('Processing...')
                    df['stg_batch_id'] = batch_id
                    df['stg_load_time'] = load_time
                    df['stg_file_name'] = file_name
                    df['stg_datim_id'] = datim_id
                    # PII columns to hide; 'first_name','surname','other_name','full_name', 'contact_point'
                    df['first_name'] = '*****'
                    df['surname'] = '*****'
                    df['other_name'] = '*****'
                    df['full_name'] = '*****'
                    df['contact_point'] = '*****'
                    self._replace_empty_strings_with_null(df)
                    df.to_sql(staging_table, con=engine, index=False, if_exists='append', 
                                dtype=dtype_mapping)
                    conn.commit()        
                self.count_of_df = len(df)
            
            else:
                df = pd.read_json(file_path, convert_dates=parse_dates)
                if df.empty:
                    logger.info(f"The JSON file is empty: {file_path}")
                    self._update_log('failed', file_name, 0, 'JSON file is empty')
                    self._update_flag_syncfile('failed', -2, 0, 'JSON file is empty')
                    return
                else:
                    df = df.dropna(how='all')
                    logger.info(len(df))
                    logger.info('Processing...')
                    df['stg_batch_id'] = batch_id
                    df['stg_load_time'] = load_time
                    df['stg_file_name'] = file_name
                    df['stg_datim_id'] = datim_id
                    self._replace_empty_strings_with_null(df)
                    df.to_sql(staging_table, con=engine, index=False, if_exists='append', 
                                dtype=dtype_mapping)
                    conn.commit()        
                self.count_of_df = len(df)

            cur = conn.cursor()
            count_of_stg = pd.read_sql(
                "SELECT COUNT(*) FROM {} WHERE stg_datim_id = '{}' AND stg_file_name = '{}' AND stg_batch_id = '{}'"
                .format(staging_table, datim_id, file_name, batch_id), con=engine).values[0][0]

            ins_counts = f"INSERT INTO stg_monitoring (datim_id, batch_id, file_name, table_name, load_time, json_rec_count, stg_rec_count) VALUES \
            ('{datim_id}', '{batch_id}', '{file_name}', '{staging_table}', '{load_time}', '{self.count_of_df}', '{count_of_stg}')"

            cur.execute(ins_counts)
            conn.commit()
            cur.close()
            self._update_log('success', file_name, self.count_of_df, 'No errors')
            self._update_flag_syncfile('success', 2, self.count_of_df, 'No errors')
        
            
        except Exception as e:
            logger.exception(e)
            raise e