import pytest
from datetime import datetime, timezone
from typing import Optional, Generator
from dataclasses import dataclass
from moto import mock_aws
import boto3

from .interfaces import BaseState
from .s3 import S3StateManager

@dataclass
class TestState(BaseState):
    def __init__(self, id: str, last_updated_date: Optional[datetime] = datetime.now(timezone.utc).isoformat()):
        self.id: str = id
        super().__init__(last_updated_date)
    __test__ = False

@pytest.fixture
def s3_client() -> Generator[boto3.client, None, None]:
    with mock_aws():
        s3 = boto3.client("s3", region_name="ap-southeast-2")
        location = {'LocationConstraint': "ap-southeast-2"}
        # Create test bucket
        s3.create_bucket(Bucket="test-bucket", CreateBucketConfiguration=location)
        yield s3

@pytest.fixture
def state_manager(s3_client) -> S3StateManager:
    return S3StateManager("test-bucket", "test-key", TestState)

def test_save_and_get_state(state_manager: S3StateManager) -> None:
    """Test saving and retrieving state"""
    test_state = TestState(id="test-id")
    
    # Save state
    state_manager.save_state(test_state)
    
    # Retrieve state
    retrieved_state = state_manager.get_state()
    
    assert retrieved_state is not None
    assert isinstance(retrieved_state, TestState)
    assert retrieved_state.id == "test-id"
    assert isinstance(retrieved_state.last_updated_date, datetime)
    assert retrieved_state.last_updated_date.tzinfo == timezone.utc


def test_get_nonexistent_state(state_manager: S3StateManager) -> None:
    """Test retrieving state that doesn't exist"""
    state = state_manager.get_state()
    assert state is None

def test_clear_state(state_manager: S3StateManager) -> None:
    """Test clearing state"""
    test_state = TestState(id="test-id")
    # Save and then clear state
    state_manager.save_state(test_state)
    state_manager.clear_state()
    
    # Verify state is cleared
    state = state_manager.get_state()
    assert state is None

def test_get_last_updated(state_manager: S3StateManager) -> None:
    """Test getting last updated timestamp"""
    test_state = TestState(id="test-id")

    # Test with no state
    last_updated = state_manager.get_last_updated()
    assert last_updated is None
    
    # Test with state
    state_manager.save_state(test_state)
    last_updated = state_manager.get_last_updated()
    
    assert isinstance(last_updated, datetime)
    assert last_updated.tzinfo == timezone.utc

def test_error_handling(state_manager: S3StateManager) -> None:
    """Test error handling for invalid bucket"""
    # Change to invalid bucket
    state_manager.bucket = "nonexistent-bucket"
    test_state = TestState(id="test-id")
    
    with pytest.raises(RuntimeError):
        state_manager.save_state(test_state)
    
    with pytest.raises(RuntimeError):
        state_manager.get_state()
    
    with pytest.raises(RuntimeError):
        state_manager.clear_state()
