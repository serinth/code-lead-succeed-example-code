from datetime import datetime, timezone
import pytest
from unittest.mock import Mock, patch
from typing import Generator

from github.Repository import Repository as GithubRepository
from github.PullRequest import PullRequest as GithubPullRequest
from github.NamedUser import NamedUser
from github.File import File

from code_analysis_tool.github_client import GitHubClient
from code_analysis_tool.models.repository import Repository
from code_analysis_tool.models.pull_request import PullRequest
from code_analysis_tool.models.user import User

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
    mock_user.id = 123
    mock_user.login = "test_user"
    mock_user.name = "Test User"
    mock_user.email = "test@example.com"
    github_client.github.get_user = Mock(return_value=mock_user)
    
    result = github_client.get_user_by_id("test_user")
    
    assert isinstance(result, User)
    assert result.id == "123"
    assert result.login == "test_user"
    assert result.name == "Test User"
    assert result.email == "test@example.com"
    github_client.github.get_user.assert_called_once_with("test_user")

def test_get_user_by_id_failure(github_client: GitHubClient) -> None:
    github_client.github.get_user = Mock(side_effect=Exception("User not found"))
    
    with pytest.raises(Exception) as exc_info:
        github_client.get_user_by_id("test_user")
    
    assert "Failed to find user with ID test_user" in str(exc_info.value)

def test_get_user_repositories_success(github_client: GitHubClient) -> None:
    mock_user = Mock(spec=NamedUser)
    mock_user.id = 123
    mock_user.login = "test_user"
    mock_user.name = "Test User"
    mock_user.email = "test@example.com"
    
    mock_repo_owner = Mock(spec=NamedUser)
    mock_repo_owner.id = 456
    mock_repo_owner.login = "owner"
    mock_repo_owner.name = "Owner"
    mock_repo_owner.email = "owner@example.com"
    
    mock_repos = []
    for i in range(2):
        mock_repo = Mock(spec=GithubRepository)
        mock_repo.id = i
        mock_repo.name = f"repo{i}"
        mock_repo.full_name = f"owner/repo{i}"
        mock_repo.owner = mock_repo_owner
        mock_repo.description = f"Description {i}"
        mock_repo.private = False
        mock_repos.append(mock_repo)
    
    mock_user.get_repos.return_value = mock_repos
    github_client.github.get_user = Mock(return_value=mock_user)
    
    result = github_client.get_user_repositories("test_user")
    
    assert len(result) == 2
    assert all(isinstance(repo, Repository) for repo in result)
    assert result[0].name == "repo0"
    assert result[1].name == "repo1"
    github_client.github.get_user.assert_called_once_with("test_user")
    mock_user.get_repos.assert_called_once()

def test_get_merged_pull_requests_success(github_client: GitHubClient) -> None:
    mock_repo = Mock(spec=GithubRepository)
    mock_user = Mock(spec=NamedUser)
    mock_user.id = 123
    mock_user.login = "test_user"
    mock_user.name = "Test User"
    mock_user.email = "test@example.com"
    
    # Create mock PRs
    mock_pr1 = Mock(spec=GithubPullRequest)
    mock_pr1.id = 1
    mock_pr1.number = 1
    mock_pr1.title = "PR 1"
    mock_pr1.user = mock_user
    mock_pr1.base.repo = mock_repo
    mock_pr1.created_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
    mock_pr1.merged_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
    mock_pr1.merged = True
    mock_pr1.body = "PR 1 description"
    
    # Mock file diffs
    mock_file = Mock(spec=File)
    mock_file.filename = "test.py"
    mock_file.patch = "diff content"
    mock_pr1.get_files = Mock(return_value=[mock_file])
    
    mock_pr2 = Mock(spec=GithubPullRequest)
    mock_pr2.merged = False
    
    mock_pulls = Mock()
    mock_pulls.__iter__ = lambda self: iter([mock_pr1, mock_pr2])
    
    mock_repo.get_pulls.return_value = mock_pulls
    github_client.github.get_repo = Mock(return_value=mock_repo)
    
    result = github_client.get_merged_pull_requests("owner/repo", "2024-01-01")
    
    assert len(result) == 1
    assert isinstance(result[0], PullRequest)
    assert result[0].number == 1
    
    # Test that diffs haven't been loaded yet
    assert result[0]._file_diffs is None
    
    # Now access file_diffs to trigger lazy loading
    diffs = result[0].file_diffs
    assert diffs == {"test.py": "diff content"}
    
    github_client.github.get_repo.assert_called_once_with("owner/repo")
    mock_repo.get_pulls.assert_called_once_with(state='closed', sort='updated', direction='desc')

def test_get_merged_pull_requests_invalid_date(github_client: GitHubClient) -> None:
    mock_repo = Mock(spec=GithubRepository)
    mock_pr = Mock(spec=GithubPullRequest)
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
    mock_repo1 = Mock(spec=GithubRepository)
    mock_repo1.full_name = "owner/repo1"
    mock_repo2 = Mock(spec=GithubRepository)
    mock_repo2.full_name = "owner/repo2"
    
    # Mock pull requests
    mock_pr1 = Mock(spec=GithubPullRequest)
    mock_pr2 = Mock(spec=GithubPullRequest)
    
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