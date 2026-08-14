"""
Tests for the visitor counter logic in function_app.py.

We test increment_and_get_count() directly, using a fake/mock
table client instead of a real connection to Azure. This means
these tests run instantly, don't need internet access, and don't
touch the real CosmosDB data.
"""

from unittest.mock import MagicMock
from azure.core.exceptions import ResourceNotFoundError
from function_app import increment_and_get_count


def test_increment_existing_count():
    """
    If a row already exists with count=5, calling the function
    should return 6, and should have called update_entity (not
    create_entity, since the row already existed).
    """
    mock_table_client = MagicMock()
    mock_table_client.get_entity.return_value = {
        "PartitionKey": "resume",
        "RowKey": "counter",
        "count": 5,
    }

    result = increment_and_get_count(mock_table_client)

    assert result == 6
    mock_table_client.update_entity.assert_called_once()
    mock_table_client.create_entity.assert_not_called()


def test_creates_row_when_none_exists():
    """
    If no row exists yet (first ever visitor), the function should
    catch the ResourceNotFoundError, start the count at 1, and
    create a new row instead of updating one.
    """
    mock_table_client = MagicMock()
    mock_table_client.get_entity.side_effect = ResourceNotFoundError("not found")

    result = increment_and_get_count(mock_table_client)

    assert result == 1
    mock_table_client.create_entity.assert_called_once()
    mock_table_client.update_entity.assert_not_called()


def test_increments_from_zero():
    """
    Edge case: if the count somehow exists but is 0, incrementing
    it should correctly produce 1.
    """
    mock_table_client = MagicMock()
    mock_table_client.get_entity.return_value = {
        "PartitionKey": "resume",
        "RowKey": "counter",
        "count": 0,
    }

    result = increment_and_get_count(mock_table_client)

    assert result == 1


def test_large_count_increments_correctly():
    """
    Sanity check with a larger number, to catch any off-by-one
    or type issues (e.g. if count were accidentally treated as
    a string somewhere).
    """
    mock_table_client = MagicMock()
    mock_table_client.get_entity.return_value = {
        "PartitionKey": "resume",
        "RowKey": "counter",
        "count": 999,
    }

    result = increment_and_get_count(mock_table_client)

    assert result == 1000
