import psycopg2
import os
from datetime import datetime

def _db_connect_filedb():
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
        print("inserted successfully")
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
                print(f"Error decoding JSON file {os.path.basename(file_path)}: {str(e)}")
                return 0

    except Exception as e:
        print(f"No such file or directory {os.path.basename(file_path)}: {str(e)}")
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

        cur.execute(update_query,(deletion_end_time, deletion_status_check, tab_count, error_msg, id))
        conn.commit()
        cur.close()
        print(f'{file_name} log updated successfully')

def _process_derive_tablename(file_path):
        print("processing file")
        filename = os.path.basename(file_path)
        parts = filename.split('_')
        non_digit_parts = [part for part in parts if not part.isdigit() and part != 'decrypted.json']
        result=[]
        result.append('_'.join(non_digit_parts))
        check_path = result[0]
        print(check_path)
        return check_path

#_process_derive_tablename(' /home/lamisplus/server/temp/kEoPeO75AG2/base_organisation_unit_0_20240129190716_decrypted.json')

def delete_files_from_table():

    try:
        conn = _db_connect_filedb()
        
        cur = conn.cursor()

        retrieve_query = """select facility_id,decrypted_file_name 
        from sync_file where processed in (2, -2) 
		and ingest_status_check = 'success' and ingest_error_message = 'No errors' and decrypted_file_name not in (select 
		replace(file_name, '_decrypted.json', '.json') 
        from file_deletion_log where deletion_status_check = 'success' or error_message = 'file not found')
		--and facility_id = 'sMllNyKolZf'
        ORDER BY create_date asc
        LIMIT 2000
        """
        cur.execute(retrieve_query)

        # Fetch all file associated data from sync_file
        files = cur.fetchall()
        #print(files)
        demo_path = '/home/lamisplus/server/temp'
        for file in files:
            print(file)
            facility_id = file[0]
            decryptedjson_file_name = file[1].replace('.json', '_decrypted.json')
            
            local_dir = os.path.join(demo_path,facility_id,decryptedjson_file_name)

            filelog_id = _insert_into_log(_process_derive_tablename(local_dir), decryptedjson_file_name, facility_id)

            file_count = count_rows_in_json_file(local_dir)
            print(file_count)

            try:
                # Check if the file exists before attempting to delete
                if os.path.exists(local_dir):
                    print(f"{local_dir} file exists, deleting files...........\n\n")

                    os.remove(local_dir)
                    print(f"File deleted: {local_dir}")
                    # update deletion log
                    _update_log(filelog_id, 'success', decryptedjson_file_name,file_count, 'no errors')

                else:
                    print(f"File not found: {local_dir}")
                    _update_log(filelog_id, 'failed', decryptedjson_file_name,file_count, 'file not found')

            except Exception as e:
                print(f"Error deleting file {local_dir}: {str(e)}")
                _update_log(filelog_id, 'failed', decryptedjson_file_name,file_count, str(e))

        # Commit the changes and close the connection
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {str(e)}")
    
