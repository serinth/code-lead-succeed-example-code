from datetime import datetime, timezone
import pytest
from unittest.mock import Mock, patch
from typing import Generator

from github.Repository import Repository
from github.PullRequest import PullRequest
from github.NamedUser import NamedUser

from .github_client import GitHubClient

@pytest.fixture
def mock_github() -> Generator[Mock, None, None]:
    with patch('github.Github') as mock_github_class:
        mock_github_class.reset_mock()
        yield mock_github_class

@pytest.fixture
def github_client(mock_github: Mock) -> GitHubClient:
    return GitHubClient("fake_token")


def test_get_user_by_id_success(github_client: GitHubClient) -> None:
    mock_user = Mock(spec=NamedUser)
    github_client.github.get_user = Mock(return_value=mock_user)
    
    result = github_client.get_user_by_id("test_user")
    
    assert result == mock_user
    github_client.github.get_user.assert_called_once_with("test_user")

def test_get_user_by_id_failure(github_client: GitHubClient) -> None:
    github_client.github.get_user = Mock(side_effect=Exception("User not found"))
    
    with pytest.raises(Exception) as exc_info:
        github_client.get_user_by_id("test_user")
    
    assert "Failed to find user with ID test_user" in str(exc_info.value)

def test_get_user_repositories_success(github_client: GitHubClient) -> None:
    mock_user = Mock(spec=NamedUser)
    mock_repos = [Mock(spec=Repository) for _ in range(2)]
    mock_user.get_repos.return_value = mock_repos
    github_client.github.get_user = Mock(return_value=mock_user)
    
    result = github_client.get_user_repositories("test_user")
    
    assert result == mock_repos
    github_client.github.get_user.assert_called_once_with("test_user")
    mock_user.get_repos.assert_called_once()

def test_get_user_repositories_failure(github_client: GitHubClient) -> None:
    github_client.github.get_user = Mock(side_effect=Exception("User not found"))
    
    with pytest.raises(Exception) as exc_info:
        github_client.get_user_repositories("test_user")
    
    assert "Failed to fetch repositories for user ID test_user" in str(exc_info.value)

def test_get_merged_pull_requests_success(github_client: GitHubClient) -> None:
    mock_repo = Mock(spec=Repository)
    mock_pr1 = Mock(spec=PullRequest)
    mock_pr1.merged = True
    mock_pr1.merged_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
    
    mock_pr2 = Mock(spec=PullRequest)
    mock_pr2.merged = False
    
    mock_pulls = Mock()
    mock_pulls.__iter__ = lambda self: iter([mock_pr1, mock_pr2])
    
    mock_repo.get_pulls.return_value = mock_pulls
    github_client.github.get_repo = Mock(return_value=mock_repo)
    
    result = github_client.get_merged_pull_requests("owner/repo", "2024-01-01")
    
    assert len(result) == 1
    assert result[0] == mock_pr1
    github_client.github.get_repo.assert_called_once_with("owner/repo")
    mock_repo.get_pulls.assert_called_once_with(state='closed', sort='updated', direction='desc')

def test_get_merged_pull_requests_invalid_date(github_client: GitHubClient) -> None:
    mock_repo = Mock(spec=Repository)
    mock_pr = Mock(spec=PullRequest)
    mock_pr.merged = True
    mock_pulls = Mock()
    mock_pulls.__iter__ = lambda self: iter([mock_pr])
    mock_repo.get_pulls = Mock(return_value=mock_pulls)
    github_client.github.get_repo = Mock(return_value=mock_repo)
    
    with pytest.raises(ValueError) as exc_info:
        github_client.get_merged_pull_requests("owner/repo", "invalid_date")
    
    assert "Value error, potential issue in date format" in str(exc_info.value)

def test_get_merged_pull_requests_for_user_success(github_client: GitHubClient) -> None:
    # Mock repositories
    mock_repo1 = Mock(spec=Repository)
    mock_repo1.full_name = "owner/repo1"
    mock_repo2 = Mock(spec=Repository)
    mock_repo2.full_name = "owner/repo2"
    
    # Mock pull requests
    mock_pr1 = Mock(spec=PullRequest)
    mock_pr2 = Mock(spec=PullRequest)
    
    # Setup the chain of mock returns
    github_client.get_user_repositories = Mock(return_value=[mock_repo1, mock_repo2])
    github_client.get_merged_pull_requests = Mock(side_effect=[[mock_pr1], [mock_pr2]])
    
    result = github_client.get_merged_pull_requests_for_user("test_user", "2024-01-01")
    
    assert len(result) == 2
    assert result == [mock_pr1, mock_pr2]
    github_client.get_user_repositories.assert_called_once_with("test_user")
    assert github_client.get_merged_pull_requests.call_count == 2

def test_get_merged_pull_requests_for_user_failure(github_client: GitHubClient) -> None:
    github_client.get_user_repositories = Mock(side_effect=Exception("Failed to fetch repos"))
    
    with pytest.raises(Exception) as exc_info:
        github_client.get_merged_pull_requests_for_user("test_user")
    
    assert "Failed to fetch merged pull requests for user ID test_user" in str(exc_info.value) 