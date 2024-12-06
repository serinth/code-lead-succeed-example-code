from datetime import datetime, timezone
import pytest
from unittest.mock import patch, Mock
from typing import List, Dict, Any

from models.build import Build
from main import get_github_workflow_build_times

@pytest.fixture
def mock_successful_response() -> Dict[str, Any]:
    """Fixture that returns a mock GitHub API response"""
    return {
        "workflow_runs": [
            {
                "id": 123,
                "status": "completed",
                "conclusion": "success",
                "run_started_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:05:00Z",
                "head_sha": "abc123",
                "head_branch": "main"
            },
            {
                "id": 124,
                "status": "completed",
                "conclusion": "success",
                "run_started_at": "2024-01-01T11:00:00Z",
                "updated_at": "2024-01-01T11:10:00Z",
                "head_sha": "def456",
                "head_branch": "feature"
            }
        ]
    }

@pytest.fixture
def mock_empty_response() -> Dict[str, Any]:
    """Fixture that returns an empty GitHub API response"""
    return {"workflow_runs": []}

def test_get_github_workflow_build_times_successful(mock_successful_response: Dict[str, Any]) -> None:
    """Test successful workflow builds retrieval"""
    with patch('requests.get') as mock_get:
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_successful_response
        mock_get.return_value = mock_response

        # Call function
        builds: List[Build] = get_github_workflow_build_times(
            repo_owner="test-owner",
            repo_name="test-repo",
            workflow_id="123",
            access_token="fake-token",
            since_date=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )

        # Assertions
        assert len(builds) == 2
        assert builds[0].id == "123"
        assert builds[0].repo == "test-owner/test-repo"
        assert builds[0].commit == "abc123"
        assert builds[0].branch == "main"
        assert builds[0].status == "completed"
        assert builds[0].duration_secs == 300  # 5 minutes
        
        assert builds[1].id == "124"
        assert builds[1].duration_secs == 600  # 10 minutes

def test_get_github_workflow_build_times_empty(mock_empty_response: Dict[str, Any]) -> None:
    """Test empty workflow builds response"""
    with patch('requests.get') as mock_get:
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_empty_response
        mock_get.return_value = mock_response

        # Call function
        builds: List[Build] = get_github_workflow_build_times(
            repo_owner="test-owner",
            repo_name="test-repo",
            workflow_id="123",
            access_token="fake-token",
            since_date=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )

        # Assertions
        assert len(builds) == 0

def test_get_github_workflow_build_times_api_error() -> None:
    """Test handling of API errors"""
    with pytest.raises(Exception, match="API Error"):
        with patch('requests.get') as mock_get:
            # Setup mock response to raise an exception
            mock_get.side_effect = Exception("API Error")

            # Call function
            builds: List[Build] = get_github_workflow_build_times(
                repo_owner="test-owner",
                repo_name="test-repo",
                workflow_id="123",
                access_token="fake-token",
                since_date=datetime(2024, 1, 1, tzinfo=timezone.utc)
            )
        assert len(builds) == 0

def test_get_github_workflow_build_times_malformed_data(mock_successful_response: Dict[str, Any]) -> None:
    """Test handling of malformed workflow run data"""
    # Modify the response to remove required fields
    malformed_response = mock_successful_response.copy()
    malformed_response["workflow_runs"][0].pop("run_started_at")

    with patch('requests.get') as mock_get:
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = malformed_response
        mock_get.return_value = mock_response

        # Call function
        builds: List[Build] = get_github_workflow_build_times(
            repo_owner="test-owner",
            repo_name="test-repo",
            workflow_id="123",
            access_token="fake-token",
            since_date=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )

        # Assertions
        assert len(builds) == 1  # Only the second build should be processed successfully
        assert builds[0].id == "124"
