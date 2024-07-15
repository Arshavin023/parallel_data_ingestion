import psycopg2
from datetime import datetime
from radet_file_loader import FileLoader
import configparser
import os

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

def main():
    db_params = {'host': db_config['ods_host'], 'database': db_config['ods_database_name'], 'user': db_config['ods_username'],
                     'password': db_config['ods_password'],'port': db_config['ods_port'],}
    processed_path = r'C:\home\lamisplus\server\processed_folder'

    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cur:
                start_time = datetime.now() 
                log_id = f'IPID_{start_time.strftime("%Y%m%d_%H_%M")}' #ingestion process ID
                print(log_id)
                
                try:
                    print('Job Started')
                    loader = FileLoader()
                    # loader._process_raw_radet()
                    # loader._update_flag_syncfile('success',2,5000,'No errors')
                    loader._retrieve_localdir_from_syncfile()
                    # for processed_csv in os.listdir(processed_path):
                    #     processed_csv_filepath = os.path.join(processed_path,processed_csv)
                    #     loader._process_file_by_name(processed_csv_filepath)
                    end_time = datetime.now()
                
                except Exception as e:
                    raise e
    
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL database:", e)

if __name__ == '__main__':
    main()
