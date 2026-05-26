import os
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime

from records_ingestion.multithread_file_loader_v3 import FileLoader


@pytest.fixture
def file_loader_instance():
    with patch('records_ingestion.multithread_file_loader_v3.file_directory', '/tmp/test_dir'):
        fl = FileLoader()
        fl.facility_id = "EzCuaK16yja"
        fl.syncfile_entryID = 101
        fl.demo_path = '/tmp/test_dir'
        return fl


def test_get_and_map_cols(file_loader_instance):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = [('id', 'integer'), ('name', 'character varying')]

    mapping, col_list = file_loader_instance._get_and_map_cols(mock_conn, "test_table")

    assert mapping == {'id': 'integer', 'name': 'character varying'}
    assert col_list == ['id', 'name']
    mock_cur.execute.assert_called_once()
    mock_cur.close.assert_called_once()


def test_insert_into_log(file_loader_instance):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    file_loader_instance._insert_into_log(mock_conn, "/path/to/stg_patient.json", "patient")

    mock_cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()


def test_fakeupsert_synclog(file_loader_instance):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    file_loader_instance._fakeupsert_synclog(mock_conn, "file_decrypted.json", "stg_patient")

    mock_cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()


def test_update_log(file_loader_instance):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    file_loader_instance._update_log(mock_conn, "success", "file.json", 10, "No errors")

    mock_cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()


def test_update_flag_syncfile(file_loader_instance):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    file_loader_instance._update_flag_syncfile(mock_conn, "success", 2, 10, "No errors")

    mock_cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()


def test_update_centralpartnermapper(file_loader_instance):
    mock_filedb_conn = MagicMock()
    mock_staging_conn = MagicMock()
    mock_filedb_cur = MagicMock()
    mock_staging_cur = MagicMock()
    
    mock_filedb_conn.cursor.return_value = mock_filedb_cur
    mock_staging_conn.cursor.return_value = mock_staging_cur
    mock_staging_cur.fetchone.return_value = [150]

    file_loader_instance._update_centralpartnermapper(mock_filedb_conn, mock_staging_conn)

    mock_staging_cur.execute.assert_called_once()
    mock_filedb_cur.execute.assert_called_once_with(
        ANY, (150, "EzCuaK16yja")
    )
    mock_filedb_conn.commit.assert_called_once()


def test_process_derive_tablename(file_loader_instance):
    file_path = "/tmp/test_dir/EzCuaK16yja/ACE-1_patient_person_20260526_decrypted.json"
    table_name = file_loader_instance._process_derive_tablename(file_path)
    assert table_name == "ACE-1_patient_person"


def test_check_if_previouslyloaded(file_loader_instance):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = [1]

    res = file_loader_instance._check_if_previouslyloaded(mock_conn, "file.json", "EzCuaK16yja")
    assert res is True


def test_check_if_faillogged(file_loader_instance):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = [0]

    res = file_loader_instance._check_if_faillogged(mock_conn, "file.json", "EzCuaK16yja")
    assert res is False


def test_format_programming_error(file_loader_instance):
    ex = Exception("psycopg2.errors.UndefinedColumn: column \"age\" does not exist\nLINE 2: stg_patient")
    ex.args = ("psycopg2.errors.UndefinedColumn: column \"age\" does not exist\nLINE 2: stg_patient",)
    res = file_loader_instance.format_programming_error(ex)
    assert "Exception" in res
    assert "column \"age\" does not exist" in res


def test_replace_empty_strings_with_null(file_loader_instance):
    df = pd.DataFrame({'col1': ['abc', '', ' ', 'null', None]})
    file_loader_instance._replace_empty_strings_with_null(df)
    assert pd.isna(df.at[1, 'col1'])
    assert pd.isna(df.at[2, 'col1'])
    assert pd.isna(df.at[3, 'col1'])


def test_date_validation_valid(file_loader_instance):
    df = pd.DataFrame({'date_visit': ['2026-01-01', '2026-02-02']})
    prob, bad_idx = file_loader_instance._date_validation(df)
    assert prob == {}
    assert bad_idx == []


def test_date_validation_invalid(file_loader_instance):
    df = pd.DataFrame({'id': [1, 2], 'date_visit': ['2026-01-01', 'not-a-date']})
    prob, bad_idx = file_loader_instance._date_validation(df)
    assert 'date_visit' in prob
    assert len(bad_idx) > 0


def test_mask_pii(file_loader_instance):
    json_str = '{"surname": "John", "first_name": "Doe", "phone_number": "12345"}'
    masked = file_loader_instance.mask_pii(json_str)
    assert '"surname": "******"' in masked
    assert '"first_name": "******"' in masked


def test_sanitise_value(file_loader_instance):
    assert file_loader_instance._sanitise_value(pd.NaT) is None
    assert file_loader_instance._sanitise_value(np.int64(42)) == 42
    assert file_loader_instance._sanitise_value({"key": "val"}).adapted == {"key": "val"}


@patch("records_ingestion.multithread_file_loader_v3.execute_values")
def test_execute_vectorized_batch_insert(mock_execute_values, file_loader_instance):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    df = pd.DataFrame({'col1': [1, 2]})
    file_loader_instance._execute_vectorized_batch_insert(mock_conn, "stg_table", df)
    
    mock_execute_values.assert_called_once()


@patch("records_ingestion.multithread_file_loader_v3.connect_to_db.connect")
@patch("records_ingestion.multithread_file_loader_v3.os.path.exists")
def test_retrieve_localdir_from_syncfile(mock_exists, mock_connect, file_loader_instance):
    mock_filedb_conn = MagicMock()
    mock_staging_conn = MagicMock()
    mock_filedb_cur = MagicMock()
    
    mock_filedb_conn.__enter__.return_value = mock_filedb_conn
    mock_staging_conn.__enter__.return_value = mock_staging_conn
    mock_filedb_conn.cursor.return_value.__enter__.return_value = mock_filedb_cur
    
    mock_connect.side_effect = [[mock_filedb_conn], [mock_staging_conn]]
    mock_filedb_cur.fetchall.return_value = [(101, "EzCuaK16yja", "patient.json")]
    mock_exists.return_value = True

    with patch.object(file_loader_instance, '_fakeupsert_synclog') as mock_fake, \
         patch.object(file_loader_instance, '_process_file_by_name') as mock_process:
        
        file_loader_instance._retrieve_localdir_from_syncfile("EzCuaK16yja")
        
        mock_fake.assert_called_once()
        mock_process.assert_called_once()


@patch("records_ingestion.multithread_file_loader_v3.pd.read_json")
@patch.object(FileLoader, '_execute_vectorized_batch_insert')
def test_ingest_json_data_success(mock_insert, mock_read_json, file_loader_instance):
    mock_filedb_conn = MagicMock()
    mock_staging_conn = MagicMock()
    mock_staging_cur = MagicMock()
    mock_staging_conn.cursor.return_value.__enter__.return_value = mock_staging_cur
    
    df = pd.DataFrame({'id': [1], 'col1': ['val']})
    mock_read_json.return_value = df
    
    file_loader_instance._ingest_json_data(
        mock_filedb_conn, mock_staging_conn, "EzCuaK16yja_patient_person_20260101_decrypted.json", "stg_patient"
    )
    
    mock_insert.assert_called_once()
    # Matches the exact number of internal tracking commits made during ingestion
    assert mock_staging_conn.commit.call_count == 3