from unittest.mock import patch, MagicMock
from datetime import datetime

from records_ingestion.old.multi_dsd_ingestion_process import (
    insert_pipeline_log,
    update_pipeline_log,
    create_single_instance,
    process_facilities_in_batches,
    main
)


def test_insert_pipeline_log(mock_cursor):
    log_id = "TEST_001"
    start_time = datetime.now()

    insert_pipeline_log(mock_cursor, log_id, start_time)

    assert mock_cursor.execute.called

    query_args = mock_cursor.execute.call_args[0]

    assert "INSERT INTO file_ingestion_pipeline_log" in query_args[0]
    assert query_args[1][0] == log_id


def test_update_pipeline_log(mock_cursor):
    update_pipeline_log(
        mock_cursor,
        "TEST_001",
        datetime.now(),
        "SUCCESS",
        "No Errors",
        10
    )

    assert mock_cursor.execute.called

    query_args = mock_cursor.execute.call_args[0]

    assert "UPDATE file_ingestion_pipeline_log" in query_args[0]


@patch("records_ingestion.multi_dsd_ingestion_process.update_facility_uploads")
@patch("records_ingestion.multi_dsd_ingestion_process.FileLoader")
def test_create_single_instance_success(
    mock_loader,
    mock_update
):
    facility = (1, "VUQpWeYseot", 5)

    loader_instance = MagicMock()

    mock_loader.return_value = loader_instance

    create_single_instance(facility)

    loader_instance._retrieve_localdir_from_syncfile.assert_called_once_with(
        "VUQpWeYseot"
    )

    mock_update.assert_called_once()

    args = mock_update.call_args[0]

    assert args[0] == "PROCESSED"


@patch("records_ingestion.multi_dsd_ingestion_process.update_facility_uploads")
@patch("records_ingestion.multi_dsd_ingestion_process.FileLoader")
def test_create_single_instance_failure(
    mock_loader,
    mock_update
):
    facility = (1, "VUQpWeYseot", 5)

    loader_instance = MagicMock()

    loader_instance._retrieve_localdir_from_syncfile.side_effect = Exception(
        "Loader failed"
    )

    mock_loader.return_value = loader_instance

    create_single_instance(facility)

    mock_update.assert_called_once()

    args = mock_update.call_args[0]

    assert args[0] == "FAILED"


@patch("records_ingestion.multi_dsd_ingestion_process.create_single_instance")
@patch("records_ingestion.multi_dsd_ingestion_process.insert_pipeline_log")
@patch("records_ingestion.multi_dsd_ingestion_process.update_pipeline_log")
@patch("records_ingestion.multi_dsd_ingestion_process.connect_to_db.connect")
def test_process_facilities_in_batches(
    mock_connect,
    mock_update,
    mock_insert,
    mock_create
):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    # Correct nested context manager mocking
    mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

    mock_connect.return_value = [mock_conn]

    facilities = [
        (1, "VUQpWeYseot", 5),
        (2, "Pjak5oARJBf", 3),
    ]

    process_facilities_in_batches(facilities, batch_size=1)

    assert mock_insert.called
    assert mock_update.called
    assert mock_create.called


@patch("records_ingestion.multi_dsd_ingestion_process.process_facilities_in_batches")
@patch("records_ingestion.multi_dsd_ingestion_process.insert_facility_uploads")
@patch("records_ingestion.multi_dsd_ingestion_process.connect_to_db.connect")
def test_main_with_facilities(
    mock_connect,
    mock_insert_uploads,
    mock_process
):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_cur.fetchall.return_value = [
        (1, "VUQpWeYseot", 5)
    ]

    # Correct nested context manager mocking
    mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

    mock_connect.return_value = [mock_conn]

    main()

    assert mock_insert_uploads.called

    mock_process.assert_called_once()


@patch("records_ingestion.multi_dsd_ingestion_process.process_facilities_in_batches")
@patch("records_ingestion.multi_dsd_ingestion_process.insert_facility_uploads")
@patch("records_ingestion.multi_dsd_ingestion_process.connect_to_db.connect")
def test_main_without_facilities(
    mock_connect,
    mock_insert_uploads,
    mock_process
):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_cur.fetchall.return_value = []

    # Correct nested context manager mocking
    mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

    mock_connect.return_value = [mock_conn]

    main()

    assert mock_insert_uploads.called

    mock_process.assert_not_called()