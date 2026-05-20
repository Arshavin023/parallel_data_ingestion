from unittest.mock import MagicMock
import pytest


@pytest.fixture
def mock_cursor():
    cursor = MagicMock()
    return cursor


@pytest.fixture
def mock_connection(mock_cursor):
    conn = MagicMock()

    conn.cursor.return_value.__enter__.return_value = mock_cursor
    conn.cursor.return_value.__exit__.return_value = None

    return conn