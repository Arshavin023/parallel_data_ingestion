from unittest.mock import patch, MagicMock, call, ANY
import pytest
from datetime import datetime
import psycopg2

from records_ingestion.multi_file_ingestion_process_v2 import (
    insert_pipeline_log,
    update_pipeline_log,
    insert_facility_uploads,
    update_facility_uploads,
    create_single_instance,
    process_facilities_in_batches,
    main
)

def test_insert_pipeline_log():
    mock_cur = MagicMock()
    log_id = "TEST_LOG_ID"
    start_time = datetime.now()
    insert_pipeline_log(mock_cur, log_id, start_time)
    mock_cur.execute.assert_called_once()

def test_update_pipeline_log():
    mock_cur = MagicMock()
    log_id = "TEST_LOG_ID"
    end_time = datetime.now()
    update_pipeline_log(mock_cur, log_id, end_time, "Job Passed", None, 10)
    mock_cur.execute.assert_called_once()

@patch("records_ingestion.multi_file_ingestion_process_v2.connect_to_db.connect")
def test_insert_facility_uploads_success(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_connect.return_value = [mock_conn]

    insert_facility_uploads()
    mock_cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

@patch("records_ingestion.multi_file_ingestion_process_v2.connect_to_db.connect")
def test_insert_facility_uploads_exception(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.execute.side_effect = psycopg2.Error("DB Error")
    mock_connect.return_value = [mock_conn]

    insert_facility_uploads()
    mock_cur.execute.assert_called_once()

@patch("records_ingestion.multi_file_ingestion_process_v2.connect_to_db.connect")
def test_update_facility_uploads(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_connect.return_value = [mock_conn]

    update_facility_uploads('PROCESSED', datetime.now(), datetime.now(), 'No errors', 'FAC1', 1, 'UNPROCESSED')
    mock_cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

@patch("records_ingestion.multi_file_ingestion_process_v2.FileLoader")
@patch("records_ingestion.multi_file_ingestion_process_v2.update_facility_uploads")
def test_create_single_instance_success(mock_update, mock_loader_cls):
    mock_loader = MagicMock()
    mock_loader_cls.return_value = mock_loader
    
    facility = (1, "EzCuaK16yja", 5)
    create_single_instance(facility)
    
    mock_loader._retrieve_localdir_from_syncfile.assert_called_once_with("EzCuaK16yja")
    mock_update.assert_called_once_with('PROCESSED', ANY, ANY, 'No errors', 'EzCuaK16yja', 1, 'UNPROCESSED')

@patch("records_ingestion.multi_file_ingestion_process_v2.FileLoader")
@patch("records_ingestion.multi_file_ingestion_process_v2.update_facility_uploads")
def test_create_single_instance_exception(mock_update, mock_loader_cls):
    mock_loader = MagicMock()
    mock_loader._retrieve_localdir_from_syncfile.side_effect = Exception("Load failure")
    mock_loader_cls.return_value = mock_loader
    
    facility = (1, "EzCuaK16yja", 5)
    create_single_instance(facility)
    
    mock_update.assert_called_once_with('FAILED', ANY, ANY, 'Load failure', 'EzCuaK16yja', 1, 'UNPROCESSED')

@patch("records_ingestion.multi_file_ingestion_process_v2.connect_to_db.connect")
@patch("records_ingestion.multi_file_ingestion_process_v2.insert_pipeline_log")
@patch("records_ingestion.multi_file_ingestion_process_v2.update_pipeline_log")
@patch("records_ingestion.multi_file_ingestion_process_v2.concurrent.futures.ThreadPoolExecutor")
def test_process_facilities_in_batches(mock_executor, mock_update_log, mock_insert_log, mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_connect.return_value = [mock_conn]
    
    mock_exec_instance = MagicMock()
    mock_executor.return_value.__enter__.return_value = mock_exec_instance
    
    facilities = [(1, "EzCuaK16yja", 5), (2, "FAC2", 3)]
    process_facilities_in_batches(facilities, batch_size=1)
    
    mock_insert_log.assert_called_once()
    assert mock_exec_instance.map.call_count == 2
    mock_update_log.assert_called_once()
    assert mock_conn.commit.call_count == 0

@patch("records_ingestion.multi_file_ingestion_process_v2.insert_facility_uploads")
@patch("records_ingestion.multi_file_ingestion_process_v2.connect_to_db.connect")
@patch("records_ingestion.multi_file_ingestion_process_v2.process_facilities_in_batches")
def test_main_with_facilities(mock_process, mock_connect, mock_insert):
    mock_conn = MagicMock()
    mock_cur = MagicMock()  # <--- FIXED TYPO HERE
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_connect.return_value = [mock_conn]
    
    mock_cur.fetchall.return_value = [(1, "FAC1", 5)]
    
    main()
    
    mock_insert.assert_called_once()
    mock_cur.execute.assert_called_once()
    mock_process.assert_called_once_with([(1, "FAC1", 5)])