import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime
import psycopg2

# Adjust this import to match the actual name of your script file
from records_ingestion.multi_file_ingestion_process_v2 import (
    insert_pipeline_log,
    update_pipeline_log,
    insert_facility_uploads,
    update_facility_uploads,
    create_single_instance,
    process_facilities_in_batches,
    main
)

@pytest.fixture
def mock_cursor():
    return MagicMock()


# ---------------------------------------------------
# 1. TEST LOGGING FUNCTIONS
# ---------------------------------------------------
def test_insert_pipeline_log(mock_cursor):
    log_id = "IPID_20260523_10_29"
    start_time = datetime.now()

    insert_pipeline_log(mock_cursor, log_id, start_time)

    assert mock_cursor.execute.called
    query_args = mock_cursor.execute.call_args[0]
    assert "INSERT INTO file_ingestion_pipeline_log" in query_args[0]
    assert query_args[1][0] == log_id
    assert query_args[1][2] == 'Job Started'


def test_update_pipeline_log(mock_cursor):
    log_id = "IPID_20260523_10_29"
    end_time = datetime.now()
    
    update_pipeline_log(mock_cursor, log_id, end_time, "Job Passed", "No Errors", 18)

    assert mock_cursor.execute.called
    query_args = mock_cursor.execute.call_args[0]
    assert "UPDATE file_ingestion_pipeline_log" in query_args[0]
    assert query_args[1][1] == "Job Passed"
    assert query_args[1][4] == log_id


# ---------------------------------------------------
# 2. TEST DB OPERATIONS WITH CONTEXT MANAGERS
# ---------------------------------------------------
@patch("records_ingestion.multi_file_ingestion_process_v2.connect_to_db.connect")
def test_insert_facility_uploads_success(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    
    # Mocking the nested context managers: with connect()[0] as conn -> with conn.cursor() as cur
    mock_connect.return_value = [mock_conn]
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    insert_facility_uploads()

    assert mock_cur.execute.called
    assert "INSERT INTO batch_facility_processing" in mock_cur.execute.call_args[0][0]
    assert mock_conn.commit.called


@patch("records_ingestion.multi_file_ingestion_process_v2.connect_to_db.connect")
def test_update_facility_uploads_success(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    
    mock_connect.return_value = [mock_conn]
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    update_facility_uploads(
        'PROCESSED', datetime.now(), datetime.now(), 'No errors', 
        'MviB6BlDITF', 1, 'UNPROCESSED'
    )

    assert mock_cur.execute.called
    assert "UPDATE batch_facility_processing" in mock_cur.execute.call_args[0][0]
    assert mock_conn.commit.called


# ---------------------------------------------------
# 3. TEST INSTANCE CREATION & LOADING
# ---------------------------------------------------
@patch("records_ingestion.multi_file_ingestion_process_v2.update_facility_uploads")
@patch("records_ingestion.multi_file_ingestion_process_v2.FileLoader")
def test_create_single_instance_success(mock_file_loader, mock_update_uploads):
    facility_tuple = (1, "MviB6BlDITF", 18)  # (batch_id, facility_id, file_count)
    
    mock_loader_instance = MagicMock()
    mock_file_loader.return_value = mock_loader_instance

    create_single_instance(facility_tuple)

    # Verify that it instantiated the FileLoader and called the correct method
    mock_file_loader.assert_called_once()
    mock_loader_instance._retrieve_localdir_from_syncfile.assert_called_once_with("MviB6BlDITF")
    
    # Verify it updated the status table to PROCESSED
    mock_update_uploads.assert_called_once()
    args = mock_update_uploads.call_args[0]
    assert args[0] == 'PROCESSED'
    assert args[3] == 'No errors'
    assert args[4] == 'MviB6BlDITF'
    assert args[5] == 1


@patch("records_ingestion.multi_file_ingestion_process_v2.update_facility_uploads")
@patch("records_ingestion.multi_file_ingestion_process_v2.FileLoader")
def test_create_single_instance_failure(mock_file_loader, mock_update_uploads):
    facility_tuple = (1, "MviB6BlDITF", 18)
    
    mock_loader_instance = MagicMock()
    # Force the loader to raise the exact type of crash you had earlier
    mock_loader_instance._retrieve_localdir_from_syncfile.side_effect = TypeError("expected str, bytes or os.PathLike object, not NoneType")
    mock_file_loader.return_value = mock_loader_instance

    create_single_instance(facility_tuple)

    # Verify it updated the status table to FAILED and captured the exception message
    mock_update_uploads.assert_called_once()
    args = mock_update_uploads.call_args[0]
    assert args[0] == 'FAILED'
    assert "TypeError" in args[3] or "NoneType" in args[3]
    assert args[4] == 'MviB6BlDITF'


# ---------------------------------------------------
# 4. TEST BATCH THREAD POOL EXECUTION
# ---------------------------------------------------
@patch("records_ingestion.multi_file_ingestion_process_v2.create_single_instance")
@patch("records_ingestion.multi_file_ingestion_process_v2.update_pipeline_log")
@patch("records_ingestion.multi_file_ingestion_process_v2.insert_pipeline_log")
@patch("records_ingestion.multi_file_ingestion_process_v2.connect_to_db.connect")
def test_process_facilities_in_batches(mock_connect, mock_insert_log, mock_update_log, mock_create_instance):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    
    mock_connect.return_value = [mock_conn]
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    facilities_list = [
        (1, "Facility_A", 5),
        (2, "Facility_B", 3)
    ]

    process_facilities_in_batches(facilities_list, batch_size=2)

    # Verify orchestration calls
    assert mock_insert_log.called
    assert mock_update_log.called
    
    # Ensure ThreadPoolExecutor mapped create_single_instance over all items
    assert mock_create_instance.call_count == 2
    mock_create_instance.assert_has_calls([call((1, "Facility_A", 5)), call((2, "Facility_B", 3))])


# ---------------------------------------------------
# 5. TEST MAIN COORDINATOR FUNCTION
# ---------------------------------------------------
@patch("records_ingestion.multi_file_ingestion_process_v2.process_facilities_in_batches")
@patch("records_ingestion.multi_file_ingestion_process_v2.insert_facility_uploads")
@patch("records_ingestion.multi_file_ingestion_process_v2.connect_to_db.connect")
def test_main_with_unprocessed_facilities(mock_connect, mock_insert_uploads, mock_process_batches):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    
    # Mock data returned by the raw SQL query inside main
    mock_cur.fetchall.return_value = [(1, "MviB6BlDITF", 18)]
    
    mock_connect.return_value = [mock_conn]
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    main()

    assert mock_insert_uploads.called
    assert mock_cur.execute.called
    mock_process_batches.assert_called_once_with([(1, "MviB6BlDITF", 18)])


@patch("records_ingestion.multi_file_ingestion_process_v2.process_facilities_in_batches")
@patch("records_ingestion.multi_file_ingestion_process_v2.insert_facility_uploads")
@patch("records_ingestion.multi_file_ingestion_process_v2.connect_to_db.connect")
def test_main_with_no_facilities(mock_connect, mock_insert_uploads, mock_process_batches):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    
    # Empty queue
    mock_cur.fetchall.return_value = []
    
    mock_connect.return_value = [mock_conn]
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    main()

    assert mock_insert_uploads.called
    # If queue is empty, process_facilities_in_batches shouldn't be executed
    mock_process_batches.assert_not_called()