from typing import Any
import pytest
from unittest.mock import Mock, MagicMock
from google.cloud import bigquery
from google.api_core import exceptions
from bigquery.dataset import ensure_dataset_exists

@pytest.fixture
def mock_client() -> Mock:
    return Mock(spec=bigquery.Client)

def test_ensure_dataset_exists_when_exists(mock_client: Mock) -> None:
    """Test when dataset already exists"""
    # Setup
    project_id: str = "test_project"
    dataset_id: str = "test_dataset"
    mock_dataset: Mock = Mock(spec=bigquery.Dataset)
    mock_client.dataset.return_value = Mock()
    mock_client.get_dataset.return_value = mock_dataset

    # Execute
    result: Any = ensure_dataset_exists(mock_client, project_id, dataset_id)

    # Assert
    mock_client.dataset.assert_called_once_with(project=project_id, dataset_id=dataset_id)
    mock_client.get_dataset.assert_called_once_with(mock_client.dataset.return_value)
    mock_client.create_dataset.assert_not_called()
    assert result == mock_dataset

def test_ensure_dataset_exists_when_not_exists(mock_client: Mock) -> None:
    """Test when dataset needs to be created"""
    # Setup
    project_id: str = "test_project"
    dataset_id: str = "test_dataset"
    mock_dataset: Mock = Mock(spec=bigquery.Dataset)
    
    
    mock_client.dataset.return_value = MagicMock()
    mock_client.get_dataset.side_effect = exceptions.NotFound("Dataset not found")
    mock_client.create_dataset.return_value = mock_dataset

    # Execute
    result: Any = ensure_dataset_exists(mock_client, project_id, dataset_id)

    # Assert
    mock_client.dataset.assert_called_once_with(project=project_id, dataset_id=dataset_id)
    mock_client.get_dataset.assert_called_once_with(mock_client.dataset.return_value)
    mock_client.create_dataset.assert_called_once()
    assert result == mock_dataset
