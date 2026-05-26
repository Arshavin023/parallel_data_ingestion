import os
from unittest.mock import patch, MagicMock, mock_open
import pytest
from datetime import datetime

from file_deletion.multi_automate_file_delete_v2 import FileDelete


@pytest.fixture
def file_delete_instance():
    with patch('file_deletion.multi_automate_file_delete_v2.file_directory', '/tmp/test_dir'):
        fd = FileDelete()
        fd.demo_path = '/tmp/test_dir'
        return fd


def test_derive_tablename(file_delete_instance):
    file_path = "/tmp/test_dir/facility123/ACE-1_data_20260526_decrypted.json"
    table_name = file_delete_instance._derive_tablename(file_path)
    assert table_name == "ACE-1_data"


def test_insert_into_log(file_delete_instance):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Mocking the context manager for connection.cursor()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = [42]  # Mocking RETURNING id

    file_delete_instance.delete_start_time = datetime.now()
    log_id = file_delete_instance._insert_into_log(mock_conn, "test_table", "test.json", "FAC-1")

    assert log_id == 42
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


def test_update_log(file_delete_instance):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    file_delete_instance.delete_end_time = datetime.now()
    file_delete_instance._update_log(mock_conn, 42, "success", "test.json", "no errors", "FAC-1")

    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("file_deletion.multi_automate_file_delete_v2.os.path.exists")
@patch("file_deletion.multi_automate_file_delete_v2.os.remove")
def test_delete_single_file_success(mock_remove, mock_exists, file_delete_instance):
    mock_exists.return_value = True
    mock_conn = MagicMock()
    
    with patch.object(file_delete_instance, '_update_log') as mock_update:
        file_delete_instance.facility_id = "FAC-1"
        file_delete_instance._delete_single_file(mock_conn, 42, "/path/file.json", "file.json")
        
        mock_remove.assert_called_once_with("/path/file.json")
        mock_update.assert_called_once_with(mock_conn, 42, 'success', 'file.json', 'no errors', 'FAC-1')


@patch("file_deletion.multi_automate_file_delete_v2.os.path.exists")
def test_delete_single_file_not_found(mock_exists, file_delete_instance):
    mock_exists.return_value = False
    mock_conn = MagicMock()
    
    with patch.object(file_delete_instance, '_update_log') as mock_update:
        file_delete_instance.facility_id = "FAC-1"
        file_delete_instance._delete_single_file(mock_conn, 42, "/path/file.json", "file.json")
        
        mock_update.assert_called_once_with(mock_conn, 42, 'failed', 'file.json', 'file not found', 'FAC-1')


@patch("file_deletion.multi_automate_file_delete_v2.connect_to_db.connect")
@patch("file_deletion.multi_automate_file_delete_v2.os.path.exists")
@patch("file_deletion.multi_automate_file_delete_v2.os.remove")
def test_delete_encrypted_files_processing(mock_remove, mock_exists, mock_connect, file_delete_instance):
    mock_exists.return_value = True
    
    # Mocking DB Connections
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Setup connection as a list wrapping the context manager
    mock_connect.return_value = [mock_conn]
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    # Mock retrieved files: (facility_id, file_name, ingest_file_name)
    mock_cursor.fetchall.return_value = [("FAC-1", "enc.json", "dec.json")]
    
    # Mock internal log methods to avoid deep nesting testing
    with patch.object(file_delete_instance, '_insert_into_log', return_value=100), \
         patch.object(file_delete_instance, '_delete_single_file') as mock_delete:
         
        file_delete_instance.delete_encrypted_files("FAC-1")
        
        assert mock_delete.call_count == 2  # Once for encrypted, once for decrypted
        mock_cursor.execute.assert_called_once()  # Asserts SELECT query ran