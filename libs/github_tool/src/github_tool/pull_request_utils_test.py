from typing import Any
import pytest
from unittest.mock import Mock, patch
from github.PullRequest import PullRequest
from github_tool.pull_request_utils import get_raw_diff

def create_mock_file(filename: str, patch_content: str | None) -> Mock:
    """Helper function to create a mock file object"""
    mock_file = Mock()
    mock_file.filename = filename
    mock_file.patch = patch_content
    return mock_file

@pytest.fixture
def mock_pr() -> Mock:
    """Fixture to create a mock PullRequest object"""
    pr = Mock(spec=PullRequest)
    pr.number = 123
    return pr

def test_get_raw_diff_success(mock_pr: Mock) -> None:
    """Test successful diff retrieval"""
    mock_files = [
        create_mock_file("file1.py", "diff1"),
        create_mock_file("file2.py", "diff2"),
        create_mock_file("file3.py", None),  # File without patch
    ]
    mock_pr.get_files.return_value = mock_files

    result = get_raw_diff(mock_pr)

    assert result == {
        "file1.py": "diff1",
        "file2.py": "diff2"
    }
    mock_pr.get_files.assert_called_once()

def test_get_raw_diff_empty(mock_pr: Mock) -> None:
    """Test when PR has no files"""
    mock_pr.get_files.return_value = []

    result = get_raw_diff(mock_pr)

    assert result == {}
    mock_pr.get_files.assert_called_once()

def test_get_raw_diff_error(mock_pr: Mock) -> None:
    """Test error handling"""
    mock_pr.get_files.side_effect = Exception("API error")

    with pytest.raises(Exception) as exc_info:
        get_raw_diff(mock_pr)

    assert str(exc_info.value) == "Failed to get diffs for PR #123: API error"
    mock_pr.get_files.assert_called_once()