from unittest.mock import patch, MagicMock, call
import pytest
from datetime import datetime

from file_deletion.multi_file_deletion_process_v2 import (
    _fetch_datim_ids,
    _process_single_facility,
    main
)


@patch("file_deletion.multi_file_deletion_process_v2.connect_to_db.connect")
def test_fetch_datim_ids(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_cur.fetchall.return_value = [
        ("VUQpWeYseot",),
        ("Pjak5oARJBf",),
    ]

    # Handle the array extraction context manager pattern: [0] as conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_connect.return_value = [mock_conn]

    result = _fetch_datim_ids("ACE-1")

    assert result == ["VUQpWeYseot", "Pjak5oARJBf"]
    mock_cur.execute.assert_called_once_with(
        "SELECT datim_id FROM central_partner_mapping WHERE ip_name = %s",
        ("ACE-1",),
    )


@patch("file_deletion.multi_file_deletion_process_v2.FileDelete")
def test_process_single_facility_success(mock_file_delete):
    mock_instance = MagicMock()
    mock_file_delete.return_value = mock_instance

    _process_single_facility("EzCuaK16yja")

    mock_instance.delete_encrypted_files.assert_called_once_with("EzCuaK16yja")


@patch("file_deletion.multi_file_deletion_process_v2.FileDelete")
def test_process_single_facility_exception(mock_file_delete):
    mock_instance = MagicMock()
    mock_instance.delete_encrypted_files.side_effect = Exception("DB error")
    mock_file_delete.return_value = mock_instance

    # Should handle internal exception inside a try-except block without exploding
    try:
        _process_single_facility("EzCuaK16yja")
    except Exception as e:
        pytest.fail(f"_process_single_facility raised an unhandled exception: {e}")


@patch("file_deletion.multi_file_deletion_process_v2._fetch_datim_ids")
@patch("file_deletion.multi_file_deletion_process_v2._process_single_facility")
@patch("file_deletion.multi_file_deletion_process_v2.connect_to_db.connect")
@patch("file_deletion.multi_file_deletion_process_v2.concurrent.futures.ThreadPoolExecutor")
def test_main_pipeline_success(mock_executor, mock_connect, mock_process, mock_fetch):
    # Setup configurations
    mock_fetch.side_effect = [["EzCuaK16yja"], ["FAC-2"], [], [], [], [], []] # Mocking 7 IP passes
    
    mock_dwh_conn = MagicMock()
    mock_dwh_cur = MagicMock()
    mock_dwh_conn.__enter__.return_value = mock_dwh_conn
    mock_dwh_conn.cursor.return_value.__enter__.return_value = mock_dwh_cur
    
    mock_filedb_conn = MagicMock()
    mock_filedb_cur = MagicMock()
    mock_filedb_conn.__enter__.return_value = mock_filedb_conn
    mock_filedb_conn.cursor.return_value.__enter__.return_value = mock_filedb_cur
    
    # Order of connection executions: 1st for pipeline logging, 2nd for counting rows
    mock_connect.side_effect = [[mock_dwh_conn], [mock_filedb_conn]]
    
    mock_filedb_cur.fetchone.return_value = [15] # 15 records deleted
    
    # Mocking Threadpool context manager behavior
    mock_exec_instance = MagicMock()
    mock_executor.return_value.__enter__.return_value = mock_exec_instance

    main()

    # Asserting pipeline lifecycle queries were executed
    assert mock_dwh_cur.execute.call_count == 2  # Insert log entry & Update log entry
    assert mock_filedb_cur.execute.call_count == 1  # Record counter SELECT query
    mock_exec_instance.map.assert_called_once()
    assert mock_dwh_conn.commit.call_count == 2