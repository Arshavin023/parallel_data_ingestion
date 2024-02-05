import psycopg2

def _retrieve_localdir_from_syncfile():
    cur = _db_connect_filedb().cursor()
    retrieve_query = """
    select id, facility_id,decrypted_file_name 
    from sync_file where processed = 1
    ORDER BY create_date asc
    LIMIT 1000
    """
    cur.execute(retrieve_query)

    files = cur.fetchall()

    update_list = [i[0] for i in files] 


    print(len(update_list))

    

    # Fetch all file associated data from sync_file
    files = cur.fetchall()

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


_retrieve_localdir_from_syncfile()