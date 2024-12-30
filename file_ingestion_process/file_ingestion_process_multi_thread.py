import configparser
import psycopg2
from psycopg2.extras import Json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
import threading
from file_loader_multi_thread import FileLoader
import time
from src import logger

class BatchProcessor:
    def __init__(self, db_config_path):
        """
        Initialize the BatchProcessor with database configuration.

        :param db_config_path: Path to the database configuration file.
        """
        self.db_config = self.read_db_config(db_config_path)

    def read_db_config(self, filename, section='database'):
        """
        Reads database configuration from a configuration file.

        :param filename: Path to the config file.
        :param section: Section in the config file to read.
        :return: A dictionary of configuration parameters.
        """
        parser = configparser.ConfigParser()
        parser.read(filename)
        if parser.has_section(section):
            return {param[0]: param[1] for param in parser.items(section)}
        else:
            raise Exception(f'Section {section} not found in the {filename} file')

    def connect_to_db(self, database):
        """
        Establishes a connection to a PostgreSQL database.

        :param database: Name of the database to connect to.
        :return: psycopg2 connection and SQLAlchemy engine.
        """
        db_params = {
            'host': self.db_config['stg_host'],
            'database': database,
            'user': self.db_config['stg_username'],
            'password': self.db_config['stg_password'],
            'port': self.db_config['stg_port'],
        }
        try:
            conn = psycopg2.connect(**db_params)
            engine = create_engine(
                f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}'
            )
            return conn, engine
        except Exception as e:
            logger.error(f"Failed to connect to {database} database")
            logger.exception(e)
            raise e

    def insert_batch_ingestion_log(self):
        """
        Inserts initial batch ingestion logs for unprocessed files.
        """
        query = """
            INSERT INTO batch_stg_table_logs (table_name, status, table_name_count)
            SELECT REGEXP_REPLACE(file_name, '_[0-9]+.*|\\.json', '') table_name, 'UNPROCESSED', COUNT(file_name)
            FROM sync_file
            WHERE processed=1 AND modified_date >= '2024-12-01'
            AND NOT (decrypted_file_name ILIKE ANY(ARRAY[
                'mhpss_confirmation_%', 'prep_eligibility_%', 'prep_clinic_%', 
                'pmtct_anc_%', 'dsd_devolvement_%', 'hiv_art_clinical_%'
            ]))
            GROUP BY 1, 2
        """
        conn, _ = self.connect_to_db('filedb')
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                conn.commit()
        finally:
            conn.close()

    def update_batch_ingestion_log(self, batch_id, table_name, count, new_status, old_status, start_time=None, end_time=None, error_message=None):
        """
        Updates batch ingestion log for a specific batch.

        :param batch_id: Batch ID.
        :param table_name: Name of the table.
        :param count: Count of records in the batch.
        :param new_status: New status for the batch.
        :param old_status: Current status for the batch.
        :param start_time: Batch start time.
        :param end_time: Batch end time.
        :param error_message: Error message if any.
        """
        query = """
            UPDATE batch_stg_table_logs
            SET status = %s, start_time = %s, end_time = %s, error_message = %s
            WHERE id = %s AND status = %s AND table_name = %s AND table_name_count = %s
        """
        conn, _ = self.connect_to_db('filedb')
        try:
            with conn.cursor() as cur:
                cur.execute(query, (new_status, start_time, end_time, error_message, batch_id, old_status, table_name, count))
                conn.commit()
        finally:
            conn.close()

    def process_batch(self, loader, table_info):
        """
        Processes a single batch.

        :param loader: FileLoader instance.
        :param table_info: Tuple containing batch ID, table name, and record count.
        """
        batch_id, table_name, table_name_count = table_info
        batch_start_time = datetime.now()
        self.update_batch_ingestion_log(batch_id, table_name, table_name_count, 'PROCESSING', 'UNPROCESSED', batch_start_time)
        
        try:
            # Simulate batch processing
            loader._retrieve_localdir_from_syncfile(table_name)
            batch_end_time = datetime.now()
            self.update_batch_ingestion_log(batch_id, table_name, table_name_count, 'PROCESSED', 'PROCESSING', batch_start_time, batch_end_time, 'No errors')
            logger.info(f"Batch ingestion for {table_name} completed successfully.")
        except Exception as e:
            batch_end_time = datetime.now()
            self.update_batch_ingestion_log(batch_id, table_name, table_name_count, 'FAILED', 'PROCESSING', batch_start_time, batch_end_time, str(e))
            logger.error(f"Batch ingestion for {table_name} failed with error: {e}")

    def run_batches(self):
        """
        Main method to run batch processing with threading.
        """
        logger.info("Batch processing started.")
        self.insert_batch_ingestion_log()
        loader = FileLoader()
        
        # Fetch unprocessed batches
        query = """
            SELECT id, table_name, table_name_count
            FROM batch_stg_table_logs
            WHERE status = 'UNPROCESSED'
            ORDER BY id ASC
        """
        conn, _ = self.connect_to_db('filedb')
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                table_infos = cur.fetchall()
        finally:
            conn.close()

        if not table_infos:
            logger.info("No unprocessed batches found.")
            return

        threads = []
        for table_info in table_infos:
            thread = threading.Thread(target=self.process_batch, args=(loader, table_info))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            time.sleep(5)  # Delay to avoid overloading resources

        for thread in threads:
            thread.join()

        logger.info("Batch processing completed.")

if __name__ == "__main__":
    db_config_path = r'C:\Users\5300\Documents\Palladium\database_credentials\config.ini'
    processor = BatchProcessor(db_config_path)
    processor.run_batches()
