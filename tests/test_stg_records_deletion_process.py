from unittest.mock import patch, MagicMock

from records_deletion.stg_records_deletion_process import (
    create_single_instance,
    main
)


@patch("records_deletion.stg_records_deletion_process.connect_to_db.connect")
def test_create_single_instance_success(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_conn.cursor.return_value = mock_cur

    mock_connect.return_value = [mock_conn]

    create_single_instance(("stg_hiv_observation",))

    mock_cur.execute.assert_called_once()

    args = mock_cur.execute.call_args[0]

    assert "CALL proc_delete_stg_records_v2" in args[0]

    mock_conn.commit.assert_called_once()


@patch("records_deletion.stg_records_deletion_process.connect_to_db.connect")
def test_create_single_instance_failure(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_cur.execute.side_effect = Exception("DB Error")

    mock_conn.cursor.return_value = mock_cur

    mock_connect.return_value = [mock_conn]

    create_single_instance(("stg_hiv_observation",))

    mock_conn.rollback.assert_called_once()


@patch("records_deletion.stg_records_deletion_process.create_single_instance")
@patch("records_deletion.stg_records_deletion_process.connect_to_db.connect")
def test_main(mock_connect, mock_create):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_cur.fetchall.return_value = [
        ("stg_hiv_observation",),
        ("stg_patient_visit",),
    ]

    mock_conn.cursor.return_value = mock_cur

    mock_connect.return_value = [mock_conn]

    main()

    assert mock_create.called