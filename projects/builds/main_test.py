from datetime import datetime, timezone
import pytest
from unittest.mock import patch, Mock
from typing import List, Dict, Any, Optional
import requests

from models.build import Build
from main import (
    get_github_workflow_build_times,
    fetch_workflow_page,
    parse_workflow_run,
)

@pytest.fixture
def mock_workflow_run() -> Dict[str, Any]:
    """Fixture that returns a single workflow run"""
    return {
        "id": 123,
        "status": "completed",
        "conclusion": "success",
        "run_started_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:05:00Z",
        "head_sha": "abc123",
        "head_branch": "main"
    }

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

def test_parse_workflow_run_successful(mock_workflow_run: Dict[str, Any]) -> None:
    """Test successful parsing of a workflow run"""
    build: Optional[Build] = parse_workflow_run(
        run=mock_workflow_run,
        repo_owner="test-owner",
        repo_name="test-repo"
    )
    
    assert build is not None
    assert build.id == "123"
    assert build.repo == "test-owner/test-repo"
    assert build.commit == "abc123"
    assert build.branch == "main"
    assert build.status == "completed"
    assert build.duration_secs == 300  # 5 minutes

def test_parse_workflow_run_invalid_status(mock_workflow_run: Dict[str, Any]) -> None:
    """Test parsing of a workflow run with invalid status"""
    mock_workflow_run["status"] = "in_progress"
    build = parse_workflow_run(
        run=mock_workflow_run,
        repo_owner="test-owner",
        repo_name="test-repo"
    )
    assert build is None

def test_parse_workflow_run_missing_data(mock_workflow_run: Dict[str, Any]) -> None:
    """Test parsing of a workflow run with missing data"""
    del mock_workflow_run["run_started_at"]
    build = parse_workflow_run(
        run=mock_workflow_run,
        repo_owner="test-owner",
        repo_name="test-repo"
    )
    assert build is None

def test_fetch_workflow_page_successful(mock_successful_response: Dict[str, Any]) -> None:
    """Test successful fetching of workflow page"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_successful_response
        mock_get.return_value = mock_response

        workflow_runs = fetch_workflow_page(
            url="https://api.test.com",
            headers={"Authorization": "token"},
            params={"page": "1"}
        )

        assert workflow_runs is not None
        assert len(workflow_runs) == 2
        assert workflow_runs[0]["id"] == 123

def test_fetch_workflow_page_request_error() -> None:
    """Test handling of request error in fetch_workflow_page"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        workflow_runs = fetch_workflow_page(
            url="https://api.test.com",
            headers={"Authorization": "token"},
            params={"page": "1"}
        )

        assert workflow_runs is None

def test_get_github_workflow_build_times_successful(mock_successful_response: Dict[str, Any]) -> None:
    """Test successful workflow builds retrieval"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_successful_response
        mock_get.return_value = mock_response

        builds: List[Build] = get_github_workflow_build_times(
            repo_owner="test-owner",
            repo_name="test-repo",
            workflow_id="123",
            access_token="fake-token",
            since_date=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )

        assert len(builds) == 2
        assert builds[0].id == "123"
        assert builds[0].duration_secs == 300
        assert builds[1].id == "124"
        assert builds[1].duration_secs == 600

def test_get_github_workflow_build_times_empty(mock_empty_response: Dict[str, Any]) -> None:
    """Test empty workflow builds response"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_empty_response
        mock_get.return_value = mock_response

        builds: List[Build] = get_github_workflow_build_times(
            repo_owner="test-owner",
            repo_name="test-repo",
            workflow_id="123",
            access_token="fake-token",
            since_date=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )

        assert len(builds) == 0
