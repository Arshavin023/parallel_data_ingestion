import psycopg2
import os

def delete_files_from_table(conn_params):

    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        retrieve_query = """select facility_id,decrypted_file_name 
        from sync_file where processed = 2 
		and ingest_status_check = 'success' and ingest_error_message = 'No errors'
        ORDER BY create_date asc
        LIMIT 500
        """
        cur.execute(retrieve_query)

        # Fetch all file associated data from sync_file
        files = cur.fetchall()
        demo_path = '/home/lamisplus/server/temp'
        for file in files:
            facility_id = file[0]
            decryptedjson_file_name = file[1].replace('.json', '_decrypted.json')
            local_dir = os.path.join(demo_path,facility_id,decryptedjson_file_name)

            try:
                # Check if the file exists before attempting to delete
                if os.path.exists(local_dir):
                    #os.remove(file_path)
                    print(f"File deleted: {local_dir}")
                else:
                    print(f"File not found: {local_dir}")

            except Exception as e:
                print(f"Error deleting file {local_dir}: {str(e)}")

        # Commit the changes and close the connection
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Update with your database connection parameters
    db_params = {
        'host': 'localhost',
        'database': 'filedb',
        'user': 'oluwaloseyi',
        'password': 'VgLYVEqNzJxMmSX',
        'port': '5432',
    }

    delete_files_from_table(db_params)
