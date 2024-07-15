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
import configparser 
from sqlalchemy import MetaData, Table

# Read column mappings from JSON file
with open('C:\home\lamisplus\json_files\column_mappings.json', 'r') as f:
    column_mappings = json.load(f)

# Read column list from JSON file
with open('C:\home\lamisplus\json_files\column_list.json', 'r') as f:
    columns_to_keep = json.load(f)

def read_db_config(filename='C:\home\lamisplus\database_credentials\config.ini', section='database'):
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

pd.set_option('display.max_columns', None)

class FileLoader:
    def __init__(self):
        self.facility_id = None
        self.syncfile_entryID = None
        self.processed_path = r'C:\home\lamisplus\server\processed_folder'
        self.raw_path = r'C:\home\lamisplus\server\raw_folder'
        self.datim_path = r'C:\home\lamisplus\csv_files\datim_id.csv'
        self.count_of_df = 0
        self.load_end_time = None
        self.load_start_time = None
	
    def _insert_synclog(self, file_name):
        try:
            conn = self._db_connect('filedb')[0]
            cur = conn.cursor()
            ingest_status_check = 'processing'
            created_date = datetime.now()
            insert_query = """INSERT INTO sync_file(file_name, created_date, processed, ingest_status_check, csv_rec_count)
                            VALUES(%s, %s, %s, %s, %s)"""
            cur.execute(insert_query, (file_name, created_date, 1, ingest_status_check, 0))
            conn.commit()
            cur.close()
            logger.info('Successfully logged into sync_file table in filedb database')
        except Exception as e:
            raise e
	
    def _process_raw_radet(self):
        # Get a list of all files in raw and processed folders
        raw_files = [file for file in os.listdir(self.raw_path) if file.endswith('.csv')]
        processed_files = [os.path.splitext(file)[0] for file in os.listdir(self.processed_path) if file.endswith('.csv')]
        
        # Read each CSV file into a DataFrame and add it to the dictionary
        for csv_file in raw_files:
            if (os.path.splitext(csv_file)[0] + '_processed') not in processed_files:
                file_path = os.path.join(self.raw_path, csv_file)
                try:
                     # Read the CSV file where condition meets
                    df = pd.read_csv(file_path, encoding='latin1')
                    datimid = pd.read_csv(self.datim_path,encoding='latin1')
                    df = df.rename(columns=column_mappings)
					# Create new columns
                    # df['datim_id']='ulunZz6L3UM'
                    df['period'] = '2024W25'
                    df['treatmentmethoddate'] = df['tbtreatmentstartdate']
                    df['tbstatusoutcome']=df['tbstatus']
					# Select desired columns for radet
                    final_output = pd.merge(df,datimid,on='facilityname',how='inner')
                    final_output = df[columns_to_keep]
                    name = os.path.splitext(csv_file)[0]
					
                    if not os.path.exists(self.processed_path):
                        os.makedirs(self.processed_path)
                        final_output.to_csv(f'{self.processed_path}/{name}_processed.csv',index=False)
                    else:
                        final_output.to_csv(f'{self.processed_path}/{name}_processed.csv',index=False)
                    self._insert_synclog(csv_file)
					
                except pd.errors.EmptyDataError:
                    # Handle the case where the Excel file is empty
                    print(f"Warning: {csv_file} is empty.")
                except Exception as e:
                    raise e
            else:
                pass

        return
		
    def _db_connect(self, database:str,schema:str):
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
        db_params = {'host': db_config['ods_host'], 'database': database, 'user': db_config['ods_username'],
                     'password': db_config['ods_password'],'port': db_config['ods_port'],}
        try:
            conn = psycopg2.connect(**db_params)
            engine_url = f'postgresql+psycopg2://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}'
            engine = create_engine(engine_url, connect_args={'options': f'-c search_path={schema}'})
        
            # engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}')
            return [conn, engine]
        
        except Exception as e:
            logger.exception(e)
            raise e

    def _get_and_map_cols(self):
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
            conn = self._db_connect('lamisplus_ods_dwh','expanded_radet')[0]
            cur = conn.cursor()

            retrieve_query = f"""SELECT column_name, data_type
                                FROM information_schema.columns
                                WHERE table_catalog = 'lamisplus_ods_dwh'
                                AND table_schema = 'expanded_radet'
                                AND table_name = 'expanded_radet_weekly'
                                """

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

    def _update_flag_syncfile(self, proc_status, proc_val, tab_count, error_msg):  
        '''
        Updates the synchronization file log with processing status and details.
        This method updates the sync_file table with the processing status, end time of ingestion, 
        number of CSV records ingested, and any error message encountered during processing.
        Parameters:
        - proc_status (str): The processing status ('success' or 'failed').
        - proc_val (int): The processing value.
        - tab_count (int): The number of JSON records ingested.
        - error_msg (str): Any error message encountered during processing.
        Raises:
        - Exception: If an error occurs while updating the synchronization file log.
        '''  
        try: 
            conn = self._db_connect('filedb','public')[0]
            cur = conn.cursor()
            ingest_status_check = proc_status
            update_query = """UPDATE sync_file SET processed = %s,ingest_start_time=%s, ingest_end_time = %s, ingest_status_check = %s,
                                                    csv_rec_count = %s,  ingest_error_message = %s  WHERE id = %s"""
            cur.execute(update_query, (proc_val,self.load_start_time, self.load_end_time, ingest_status_check, 
                                    tab_count, error_msg, self.syncfile_entryID))
                                    # self.syncfile_entryID
                                    # ))
            conn.commit()
            cur.close()

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
            conn = self._db_connect('filedb','public')[0]
            cur = conn.cursor()
            retrieve_query = """
            SELECT id, file_name 
            FROM sync_file WHERE processed = 1 and id=10
			--AND created_date >= '2024-03-21' 
            --ORDER BY created_date desc
            LIMIT 1"""
            cur.execute(retrieve_query)

            files = cur.fetchall()

            for file in files:
                self.syncfile_entryID = file[0]
                # self.facility_id = file[1]
                processed_file_name = file[1].replace('.csv', '_processed.csv')
                local_dir = os.path.join(self.processed_path, processed_file_name)

                if os.path.exists(local_dir):
                    logger.info('-----------------------------------------------------------------------------')
                    logger.info(f"The file '{local_dir}' exists.")
                    self._process_file_by_name(local_dir)
                else:
                    logger.info(f"The file '{local_dir}' does not exist. Skipping to next file")
                    pass
            cur.close()
            logger.info('csv files successfully processed')

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
        conn, engine = self._db_connect('lamisplus_ods_dwh','expanded_radet')[0], self._db_connect('lamisplus_ods_dwh','expanded_radet')[1]
        try:
            staging_table = 'expanded_radet_weekly'
            parse_dates = ['date_of_birth']

            self._ingest_json_data(file_path, staging_table, dtype=self._get_and_map_cols()[0], parse_dates=parse_dates)
        except Exception as e:
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
            self._update_flag_syncfile('failed', -2, self.count_of_df, error_msg)

                
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
	
    def _date_validation(self, df):
        date_columns = [col for col in df.columns if col.startswith('date') or col.endswith('date')]
        
        if date_columns:
            df_dates = df[date_columns].fillna('2024-01-01')
            validity_results = {}
            
            for col in date_columns:
                try:
                    pd.to_datetime(df_dates[col])
                    validity_results[col] = True  # Date is valid
                except ValueError:
                    validity_results[col] = False  # Date is invalid or column contains non-date data
            failed_keys = [key for key, value in validity_results.items() if value is False]
            if failed_keys != []:
                return failed_keys
            else:
                return []
        else:
            return []  # No date columns found, consider validation as passed	
	
    def _ingest_json_data(self, file_path, staging_table, dtype=None, parse_dates=None):
        '''
        Ingests JSON data into a specified staging table in the database.
        Args:
            file_path (str): The path to the CSV file.
            staging_table (str): The name of the staging table in the database.
            dtype (dict, optional): A dictionary mapping column names to PostgreSQL data types. Defaults to None.
            parse_dates (list, optional): A list of column names to parse as dates. Defaults to None.
        Returns:
            None
        Raises:
            Exception: If an error occurs during the ingestion process.
        '''
        try:
            conn, engine = self._db_connect('lamisplus_ods_dwh','expanded_radet')[0], self._db_connect('lamisplus_ods_dwh','expanded_radet')[1]
            # batch_id = file_path.split('_')[-2]
            # datim_id = self.facility_id
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
            
            dtype_mapping = {col: convert_postgresql_to_sqlalchemy(dtype[col]) for col in dtype}
            df = pd.read_csv(file_path,
                            #  low_memory=False,
                             encoding='latin1')
            if df.empty:
                logger.info(f"The JSON file is empty: {file_path}")
                # self._update_flag_syncfile('failed', -2, 0, 'JSON file is empty')
                return
			
			# Validate dates
            validation_result = self._date_validation(df)
            if validation_result != []:
                logger.info(f"The JSON file: {file_path} has invalid dates, please reupload")
                print(validation_result)
                self._update_flag_syncfile('failed', -2, 0, f'{file_name} has invalid dates in {validation_result} columns, please review, fix and reupload')
                return
            else:
				# Clean DataFrame and prepare for insertion
                df = df.dropna(how='all')
                # df['load_time'] = load_time
                # df['file_name'] = file_name
                # df['datim_id'] = datim_id
                self._replace_empty_strings_with_null(df)
                self.load_start_time = datetime.now()
                df.to_sql(name=staging_table, con=engine, index=False, if_exists='append',dtype=dtype_mapping)
                conn.commit()        
                self.count_of_df = len(df)
                self.load_end_time = datetime.now()
                self._update_flag_syncfile('success', 2, self.count_of_df, 'No errors')
                logger.info(f'{file_name} successfully ingested into {staging_table} table')
		
            cur = conn.cursor()
            conn.commit()
            cur.close()
        except Exception as e:
            logger.exception(e)
            raise e
