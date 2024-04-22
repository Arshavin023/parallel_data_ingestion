import os
import json
import uuid
import numpy as np
import psycopg2
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from datetime import datetime
from sqlalchemy import JSON, Integer, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB

pd.set_option('display.max_columns', None)

class FileLoader:
    def __init__(self):
        self.facility_id = None
        self.syncfile_entryID = None
        self.demo_path = '/home/lamisplus/server/temp'
        self.count_of_df = 0
        self.load_end_time = None
        self.load_start_time = None

    def _db_connect(self):
        db_params = {
        'host': 'localhost',
        'database': 'lamisplus_staging_dwh',
        'user': 'oluwaloseyi',
        'password': 'VgLYVEqNzJxMmSX',
        'port': '5432',
         }
         # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_params)
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}')
        return [conn,engine]

    def _db_connect_filedb(self):
        db_params = {
        'host': 'localhost',
        'database': 'filedb',
        'user': 'oluwaloseyi',
        'password': 'VgLYVEqNzJxMmSX',
        'port': '5432',
         }

         # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_params)
        return conn

    def _get_and_map_cols(self, table_name):
        # Connect to the PostgreSQL database
        conn = self._db_connect()[0]
        cur = conn.cursor()

        retrieve_query = """SELECT column_name, data_type
        FROM information_schema.columns
        where table_catalog = 'lamisplus_staging_dwh'
        and table_schema = 'public'
        and table_name = 'stg_{tname}' """.format(tname = table_name)

        cur.execute(retrieve_query)

        # Fetch all file associated data from sync_file
        columns = cur.fetchall()
        column_mapping = {name: type_ for name, type_ in columns}
        column_list = [i[0] for i in columns]
        return [column_mapping, column_list]
        conn.commit()
        cur.close()

    
    def _insert_into_log(self, file_path, tablename):
        conn=self._db_connect()[0]
        cur = conn.cursor()
        self.load_start_time = datetime.now()
        load_status_check = 'processing'
        table_name = f'stg_{tablename}'
        file_name = os.path.basename(file_path)
        facility_id = self.facility_id

        insert_query = """insert into file_ingestion_log 
        (load_start_time, load_status_check, table_name, file_name, facility_id) 
        values ('{}','{}','{}','{}', '{}')""".format(self.load_start_time, load_status_check, table_name, file_name, facility_id)

        cur.execute(insert_query)
        conn.commit()
        cur.close()

    def _fakeupsert_synclog(self, file_path, tablename):
        conn=self._db_connect_filedb()
        cur = conn.cursor()
        ingest_status_check = 'processing'
        table_name = f'stg_{tablename}'
        file_name = os.path.basename(file_path)

        fakeupsert_query = """update sync_file 
        SET ingest_start_time =  %s, ingest_file_name =  %s, ingest_table_name =  %s, ingest_status_check =  %s
        WHERE id =  %s
        """

        cur.execute(fakeupsert_query, (self.load_start_time, file_name,table_name, ingest_status_check, self.syncfile_entryID))
        conn.commit()
        cur.close()
    

    def _update_log(self, proc_status, file_name, tab_count, error_msg):
        conn=self._db_connect()[0]
        cur = conn.cursor()
        self.load_end_time = datetime.now()
        load_status_check = proc_status

        update_query = """UPDATE file_ingestion_log 
                        SET load_end_time =  %s,
                        load_status_check =  %s, json_rec_count =  %s, error_message = %s
                        WHERE file_name =  %s
                        """

        cur.execute(update_query,(self.load_end_time, load_status_check, tab_count, error_msg, file_name))
        conn.commit()
        cur.close()
        print(f'{file_name} log updated successfully')
    
    def _update_flag_syncfile(self, proc_status, proc_val, tab_count,error_msg):     
        conn=self._db_connect_filedb()
        cur = conn.cursor()
        ingest_status_check = proc_status

        update_query = """UPDATE sync_file 
                        SET processed =  %s,
                        ingest_end_time =  %s,
                        ingest_status_check =  %s,        
                        json_rec_count =  %s,
                        ingest_error_message =  %s
                        WHERE id =  %s
                        """

        cur.execute(update_query,(proc_val, self.load_end_time,ingest_status_check,tab_count,error_msg,self.syncfile_entryID))
        conn.commit()
        cur.close()
        print(f'Sync File log updated for {self.syncfile_entryID} successfully')

    def _update_centralpartnermapper(self):   
        conn=self._db_connect()[0]
        cur = conn.cursor()

        get_patient_count = """
        select count(distinct uuid) as p_count from stg_patient_person
        where stg_datim_id =  %s 
        """
        cur.execute(get_patient_count,(self.facility_id,))
        p_count_per_datemid = cur.fetchall()[0]

        conn.commit()
        cur.close()

        conn=self._db_connect_filedb()
        cur = conn.cursor()
        update_query = """UPDATE central_partner_mapping 
                        SET patient_count =  %s
                        WHERE datim_id =  %s
                        """
        cur.execute(update_query,(p_count_per_datemid, self.facility_id,))
        conn.commit()
        cur.close()

        print(f'Central Partner Mapping updated for {self.facility_id} successfully')

    def _retrieve_localdir_from_syncfile(self):
        cur = self._db_connect_filedb().cursor()
        retrieve_query = """
        select id, facility_id,decrypted_file_name 
        from sync_file where processed = 1 and create_date >= '2024-03-21' and decrypted_file_name not like '%dsd_devolvement%'
        ORDER BY create_date asc
        LIMIT 20000
        """
        cur.execute(retrieve_query)

        # Fetch all file associated data from sync_file
        files = cur.fetchall()

        for file in files:
                self.syncfile_entryID = file[0]
                self.facility_id = file[1]
                decryptedjson_file_name = file[2].replace('.json', '_decrypted.json')

                local_dir = os.path.join(self.demo_path,self.facility_id,decryptedjson_file_name)

                if os.path.exists(local_dir):
                        print(f"The file '{local_dir}' exists in the folder.")
                        self._process_file_by_name(local_dir)

                else:
                        print(f"The file '{local_dir}' does not exist in the folder. Skipping to the next file")
                        pass

        cur.close()


    def _process_derive_tablename(self, file_path):
        print("processing file")
        filename = os.path.basename(file_path)
        parts = filename.split('_')
        non_digit_parts = [part for part in parts if not part.isdigit() and part != 'decrypted.json']
        result=[]
        result.append('_'.join(non_digit_parts))
        check_path = result[0]
        return check_path

    def _check_if_previouslyloaded(self, file_name, facility_id):
        conn = self._db_connect()[0]
        cur = conn.cursor()

        # Use a parameterized query to avoid SQL injection
        check_query = """SELECT COUNT(*) FROM file_ingestion_log 
                        WHERE file_name = %s and facility_id =  %s and load_status_check = 'success' """
        
        cur.execute(check_query, (file_name,facility_id))
        count = cur.fetchone()[0]

        conn.commit()
        cur.close()

        # If count is greater than 0, the file has been previously loaded
        return count > 0

    def _check_if_faillogged(self, file_name, facility_id):
        conn = self._db_connect()[0]
        cur = conn.cursor()

        # Use a parameterized query to avoid SQL injection
        check_query = """SELECT COUNT(*) FROM file_ingestion_log 
                        WHERE file_name = %s and facility_id =  %s and load_status_check = 'failed' """
        
        cur.execute(check_query, (file_name,facility_id))
        count = cur.fetchone()[0]

        conn.commit()
        cur.close()

        # If count is greater than 0, the file has been previously loaded
        return count > 0

    def _process_file_by_name(self, file_path):
        check_param = self._process_derive_tablename(file_path)
        file_name = os.path.basename(file_path)
        is_loaded_success = self._check_if_previouslyloaded(file_name, self.facility_id)
        self.count_of_df = 0

        if is_loaded_success:
            self.load_end_time = None
            print(f"The file {file_name} has been previously loaded successfully")
            self._update_flag_syncfile('success', 2 ,self.count_of_df, 'No errors' )  
            print('sync log has been updated successfully')
        else:
            is_loaded_failed = self._check_if_faillogged(file_name, self.facility_id)
            if is_loaded_failed:
                print(f'{file_name} loaded but failed')
            else:
                print(f'{file_name} not loaded not failed')
                self._insert_into_log(file_path, check_param)
                self._fakeupsert_synclog(file_path, check_param)
                print(f'{file_name} logged successfully')
            
            try:
                parse_dates = ['date_of_birth']
                staging_table = f'stg_{check_param}'
                self._ingest_json_data(file_path, staging_table, dtype=self._get_and_map_cols(check_param)[0], parse_dates=parse_dates)
            
            except Exception as e:
                error_msg =str(e)
                error_type = type(e).__name__
                print(error_type)
                if error_type == 'UnicodeDecodeError':
                    error_msg = 'UnicodeDecodeError - File is corrupted and unreadable, kindly regenerate and re-upload'

                elif error_type == 'ProgrammingError':
                    args_str = ' '.join(map(str, e.args))
                    lines = args_str.replace("psycopg2.errors.", "")
                    lines=lines.replace("stg_", "")
                    lines = lines.split('\n')
                    cleaned_message = lines[0]
                    error_msg = f'{error_type} - {cleaned_message}'

                else:
                    args_str = ' '.join(map(str, e.args))
                    error_msg = f'{error_type} - {error_msg}'
                    lines = args_str.split('\n')
                    cleaned_message = lines[0]
                
                #print(e) 
                print(error_msg)
                self._update_log('failed', file_name, self.count_of_df, error_msg)
                self._update_flag_syncfile('failed', -2, self.count_of_df, error_msg)
                print(f'Error processing {check_param} file: {file_name} - {error_msg}')

            """
            except Exception as e:
                error_msg =str(e)
                self._update_log('failed', file_name, self.count_of_df, error_msg)
                self._update_flag_syncfile('failed', -2, self.count_of_df, error_msg)
                print(f'Error processing {check_param} file: {file_name} - {error_msg}')
            """
            
            if check_param == 'patient_person':
                self._update_centralpartnermapper()
            
                
    def _replace_empty_strings_with_null(self, df):
        # Replace empty strings or spaces with NaN
        df.replace('', np.nan, inplace=True)
        df.replace(' ', np.nan, inplace=True)
  
    def _ingest_json_data(self, file_path, staging_table, dtype=None, parse_dates=None):
        conn = self._db_connect()[0]
        engine = self._db_connect()[1]
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
                'bytea': String,  # You may need to adjust this based on your use case
                'boolean': Boolean,
                'uuid': String,  # UUID will be stored as String in SQLAlchemy
                'date': DateTime,  # Date will be stored as DateTime in SQLAlchemy
                # Add more mappings as needed
            }
            return type_mapping.get(data_type, String)

        # Convert PostgreSQL types to SQLAlchemy types for dtype
        dtype_mapping = {col: convert_postgresql_to_sqlalchemy(dtype[col]) for col in dtype}

        df = pd.read_json(file_path, convert_dates=parse_dates)
            # Check if DataFrame is empty
        if df.empty:
            print(f"The JSON file is empty: {file_path}")
            self._update_log('failed', file_name, 0, 'JSON file is empty')
            self._update_flag_syncfile('failed', -2, 0, 'JSON file is empty')
            return

        else:
            print(len(df))
            df = df.dropna(how='all')
            print(len(df))
            
            print('Processing...')
            df['stg_batch_id'] = batch_id
            df['stg_load_time'] = load_time
            df['stg_file_name'] = file_name
            df['stg_datim_id'] = datim_id

            # Call the method to replace empty strings or spaces with null
            self._replace_empty_strings_with_null(df)

            cur = conn.cursor()
            # cur.execute("delete from {} where stg_datim_id = '{}' and stg_file_name = '{}' and stg_batch_id = '{}'".format(staging_table, datim_id, file_name, batch_id))
            conn.commit()

            # Use dtype_mapping for type mapping
            df.to_sql(staging_table, con=engine, index=False, if_exists='append', dtype=dtype_mapping)

            self.count_of_df = len(df)

            count_of_stg = pd.read_sql(
                "select count(*) from {} where stg_datim_id = '{}' and stg_file_name = '{}' and stg_batch_id = '{}'"
                .format(staging_table, datim_id, file_name, batch_id), con=engine).values[0][0]

            ins_counts = "insert into stg_monitoring (datim_id, batch_id, file_name, table_name, load_time, json_rec_count, stg_rec_count) values \
                ('{}','{}','{}','{}','{}','{}','{}')".format(datim_id, batch_id, file_name, staging_table, load_time,
                                                            self.count_of_df, count_of_stg)

            cur.execute(ins_counts)
            conn.commit()
            cur.close()
            self._update_log('success', file_name, self.count_of_df, 'No errors')
            self._update_flag_syncfile('success', 2 ,self.count_of_df, 'No errors')  