import pytest
import jsonpickle
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Generator
from unittest.mock import Mock, patch
from .interfaces import BaseState

from google.api_core import exceptions as gcs_exceptions

from .gcs import GCSStateManager

@dataclass
class TestState(BaseState):
    def __init__(self, id:str, last_updated_date: Optional[datetime]=None):
        self. id: str = id
        if last_updated_date:
            super().__init__(last_updated_date)
        else:
            super().__init__()
    __test__ = False


@pytest.fixture
def mock_storage_client() -> Generator[Mock, None, None]:
    with patch("google.cloud.storage.Client") as mock_client:
        yield mock_client

@pytest.fixture
def state_manager(mock_storage_client: Mock) -> GCSStateManager:
    return GCSStateManager("test-bucket", "test/state.json", TestState)

def test_save_state_success(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test successful state save operation"""
    mock_blob = Mock()
    state_manager.bucket.blob.return_value = mock_blob
    
    state = TestState(id="id")
    state_manager.save_state(state)
    
    mock_blob.upload_from_string.assert_called_once()

def test_save_state_failure(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test state save operation failure"""
    mock_blob = Mock()
    mock_blob.upload_from_string.side_effect = gcs_exceptions.GoogleAPIError("Upload failed")
    state_manager.bucket.blob.return_value = mock_blob
    
    with pytest.raises(RuntimeError, match="Failed to save state to GCS"):
        state_manager.save_state(TestState(id="test_value"))

def test_save_state_failure_type_error(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test state save operation failure due to TypeError"""
    mock_blob = Mock()
    mock_blob.upload_from_string.side_effect = TypeError("Invalid type")
    state_manager.bucket.blob.return_value = mock_blob
    
    with pytest.raises(RuntimeError, match="Failed to save state to GCS"):
        state_manager.save_state(TestState(id="test_value"))

def test_save_state_failure_attribute_error(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test state save operation failure due to AttributeError"""
    mock_blob = Mock()
    mock_blob.upload_from_string.side_effect = AttributeError("Missing attribute")
    state_manager.bucket.blob.return_value = mock_blob
    
    with pytest.raises(RuntimeError, match="Failed to save state to GCS"):
        state_manager.save_state(TestState(id="test_value"))

def test_get_state_success(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test successful state retrieval"""
    mock_blob = Mock()
    mock_blob.exists.return_value = True
    mock_blob.download_as_string.return_value = jsonpickle.encode(TestState(id="id"))
    state_manager.bucket.blob.return_value = mock_blob
    
    state = state_manager.get_state()
    
    assert isinstance(state, TestState)
    assert state.id == "id"

def test_get_state_not_exists(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test state retrieval when blob doesn't exist"""
    mock_blob = Mock()
    mock_blob.exists.return_value = False
    state_manager.bucket.blob.return_value = mock_blob
    
    state = state_manager.get_state()
    assert state is None


def test_get_state_download_failure(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test state retrieval failure due to download error"""
    mock_blob = Mock()
    mock_blob.exists.return_value = True
    mock_blob.download_as_string.side_effect = gcs_exceptions.GoogleAPIError("Download failed")
    state_manager.bucket.blob.return_value = mock_blob
    
    with pytest.raises(RuntimeError, match="Failed to retrieve state from GCS"):
        state_manager.get_state()

def test_get_last_updated_success(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test successful last updated timestamp retrieval"""
    mock_blob = Mock()
    mock_blob.exists.return_value = True
    test_date = datetime.now(timezone.utc)
    mock_blob.updated = test_date
    state_manager.bucket.blob.return_value = mock_blob
    
    last_updated = state_manager.get_last_updated()
    assert last_updated == test_date

def test_get_last_updated_not_exists(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test last updated timestamp when blob doesn't exist"""
    mock_blob = Mock()
    mock_blob.exists.return_value = False
    state_manager.bucket.blob.return_value = mock_blob
    
    last_updated = state_manager.get_last_updated()
    assert last_updated is None

def test_get_last_updated_failure(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test last updated timestamp retrieval failure"""
    mock_blob = Mock()
    mock_blob.exists.side_effect = gcs_exceptions.GoogleAPIError("API error")
    state_manager.bucket.blob.return_value = mock_blob
    
    with pytest.raises(RuntimeError, match="Failed to get last updated timestamp"):
        state_manager.get_last_updated()

def test_clear_state_success(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test successful state clearing"""
    mock_blob = Mock()
    mock_blob.exists.return_value = True
    state_manager.bucket.blob.return_value = mock_blob
    
    state_manager.clear_state()
    mock_blob.delete.assert_called_once()

def test_clear_state_not_exists(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test clearing state when blob doesn't exist"""
    mock_blob = Mock()
    mock_blob.exists.return_value = False
    state_manager.bucket.blob.return_value = mock_blob
    
    state_manager.clear_state()
    mock_blob.delete.assert_not_called()

def test_clear_state_failure(state_manager: GCSStateManager, mock_storage_client: Mock) -> None:
    """Test state clearing failure"""
    mock_blob = Mock()
    mock_blob.exists.return_value = True
    mock_blob.delete.side_effect = gcs_exceptions.GoogleAPIError("Delete failed")
    state_manager.bucket.blob.return_value = mock_blob
    
    with pytest.raises(RuntimeError, match="Failed to clear state"):
        state_manager.clear_state()
