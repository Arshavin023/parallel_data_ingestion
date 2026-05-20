from unittest.mock import patch, MagicMock

from file_deletion.multi_file_deletion_process import (
    fetch_datim_ids,
    create_single_instance,
    main
)


@patch("file_deletion.multi_file_deletion_process.connect_to_db.connect")
def test_fetch_datim_ids(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_cur.fetchall.return_value = [
        ("VUQpWeYseot",),
        ("Pjak5oARJBf",),
    ]

    # Correct nested context manager mocking
    mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

    mock_connect.return_value = [mock_conn]

    result = fetch_datim_ids("ACE-1")

    assert result == ["VUQpWeYseot", "Pjak5oARJBf"]


@patch("file_deletion.multi_file_deletion_process.FileDelete")
def test_create_single_instance(mock_delete):
    deleter = MagicMock()

    mock_delete.return_value = deleter

    create_single_instance("Pjak5oARJBf")

    deleter.delete_encrypted_files.assert_called_once_with(
        "Pjak5oARJBf"
    )


@patch("file_deletion.multi_file_deletion_process.fetch_datim_ids")
@patch("file_deletion.multi_file_deletion_process.create_single_instance")
@patch("file_deletion.multi_file_deletion_process.connect_to_db.connect")
def test_main(
    mock_connect,
    mock_create,
    mock_fetch
):
    mock_fetch.return_value = [
        "Pjak5oARJBf",
        "VUQpWeYseot",
    ]

    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_conn.cursor.return_value = mock_cur

    mock_connect.return_value = [mock_conn]

    main()

    assert mock_fetch.called
    assert mock_create.called