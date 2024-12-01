from typing import List
import pytest
from unittest.mock import Mock
from google.cloud import bigquery
from google.api_core import exceptions
from bigquery.datatable import ensure_table_exists

@pytest.fixture
def mock_bq_client() -> Mock:
    return Mock(spec=bigquery.Client)

@pytest.fixture
def sample_schema() -> List[bigquery.SchemaField]:
    return [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]

def test_ensure_table_exists_when_table_exists(mock_bq_client: Mock, sample_schema: List[bigquery.SchemaField]) -> None:
    # Arrange
    project_id = "test-project"
    dataset_id = "test_dataset"
    table_id = "test_table"
    mock_dataset = Mock()
    mock_table_ref = Mock()
    mock_table = Mock(spec=bigquery.Table)
    
    mock_bq_client.dataset.return_value = mock_dataset
    mock_dataset.table.return_value = mock_table_ref
    mock_bq_client.get_table.return_value = mock_table

    # Act
    result = ensure_table_exists(
        client=mock_bq_client,
        project_id=project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        schema=sample_schema
    )

    # Assert
    mock_bq_client.dataset.assert_called_once_with(project=project_id, dataset_id=dataset_id)
    mock_dataset.table.assert_called_once_with(table_id)
    mock_bq_client.get_table.assert_called_once_with(mock_table_ref)
    mock_bq_client.create_table.assert_not_called()
    assert result == mock_table

def test_ensure_table_exists_creates_table_when_not_found(
    mock_bq_client: Mock, 
    sample_schema: List[bigquery.SchemaField]
) -> None:
    # Arrange
    project_id = "test-project"
    dataset_id = "test_dataset"
    table_id = "test_table"
    mock_dataset = Mock()
    mock_table_ref = Mock()
    mock_table = Mock(spec=bigquery.Table)
    
    mock_bq_client.dataset.return_value = mock_dataset
    mock_dataset.table.return_value = mock_table_ref
    mock_bq_client.get_table.side_effect = exceptions.NotFound("Table not found")
    mock_bq_client.create_table.return_value = mock_table

    # Act
    result = ensure_table_exists(
        client=mock_bq_client,
        project_id=project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        schema=sample_schema
    )

    # Assert
    mock_bq_client.dataset.assert_called_once_with(project=project_id, dataset_id=dataset_id)
    mock_dataset.table.assert_called_once_with(table_id)
    mock_bq_client.get_table.assert_called_once_with(mock_table_ref)
    mock_bq_client.create_table.assert_called_once()
    assert result == mock_table

def test_ensure_table_exists_with_partitioning_and_clustering(
    mock_bq_client: Mock, 
    sample_schema: List[bigquery.SchemaField]
) -> None:
    # Arrange
    project_id = "test-project"
    dataset_id = "test_dataset"
    table_id = "test_table"
    partition_by = "created_at"
    clustering_fields = ["id"]
    
    mock_dataset = Mock()
    mock_table_ref = Mock()
    mock_table = Mock(spec=bigquery.Table)
    
    mock_bq_client.dataset.return_value = mock_dataset
    mock_dataset.table.return_value = mock_table_ref
    mock_bq_client.get_table.side_effect = exceptions.NotFound("Table not found")
    mock_bq_client.create_table.return_value = mock_table

    # Act
    result = ensure_table_exists(
        client=mock_bq_client,
        project_id=project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        schema=sample_schema,
        partition_by=partition_by,
        clustering_fields=clustering_fields
    )

    # Assert
    mock_bq_client.dataset.assert_called_once_with(project=project_id, dataset_id=dataset_id)
    mock_dataset.table.assert_called_once_with(table_id)
    mock_bq_client.get_table.assert_called_once_with(mock_table_ref)
    mock_bq_client.create_table.assert_called_once()
    assert result == mock_table
