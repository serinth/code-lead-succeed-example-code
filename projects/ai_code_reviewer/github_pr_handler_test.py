import pytest
from unittest.mock import Mock, AsyncMock, patch
from github_pr_handler import GitHubPRHandler
import hmac
import hashlib
import asyncio

@pytest.fixture
def github_handler() -> GitHubPRHandler:
    return GitHubPRHandler(
        github_token="dummy_token",
        webhook_secret="test_secret"
    )

def test_verify_signature_valid(github_handler: GitHubPRHandler) -> None:
    payload = b"test_payload"
    secret = b"test_secret"
    signature = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
    
    assert github_handler.verify_signature(payload, signature) is True

def test_verify_signature_invalid(github_handler: GitHubPRHandler) -> None:
    payload = b"test_payload"
    signature = "sha256=invalid_signature"
    
    assert github_handler.verify_signature(payload, signature) is False

@pytest.mark.asyncio
async def test_process_pr_success(github_handler: GitHubPRHandler) -> None:
    # Mock payload
    payload = {
        "pull_request": {"number": 1},
        "repository": {"full_name": "test/repo"}
    }
    
    # Mock GitHub objects
    mock_file = Mock()
    mock_file.filename = "test.py"
    mock_file.patch = "test patch"
    
    mock_pr = Mock()
    mock_pr.get_files.return_value = [mock_file]
    mock_pr.create_issue_comment = AsyncMock()
    
    mock_repo = Mock()
    mock_repo.get_pull.return_value = mock_pr
    
    github_handler.github.get_repo = Mock(return_value=mock_repo)
    github_handler.code_reviewer.review_code = Mock(
        return_value={
            "readability": ["test feedback"],
            "testability": [],
            "security": []
        }
    )
    
    resp = await github_handler.process_pr(payload)
    
    # Verify interactions
    mock_pr.create_issue_comment.assert_called()
    github_handler.code_reviewer.review_code.assert_called_once()

@pytest.mark.asyncio
async def test_handle_pr_cancels_existing_task(github_handler: GitHubPRHandler) -> None:
    payload = {
        "pull_request": {"number": 1},
        "repository": {"full_name": "test/repo"}
    }
    
    # Create a dummy coroutine for our mock task
    async def dummy_coroutine():
        pass
    
    # Create a real asyncio task with the dummy coroutine
    existing_task = asyncio.create_task(dummy_coroutine())
    github_handler.running_tasks[1] = existing_task
    
    # Mock the process_pr method
    github_handler.process_pr = AsyncMock()
    new_task = AsyncMock()
    
    # Mock asyncio.create_task to return our new mock task
    with patch('asyncio.create_task', return_value=new_task):
        resp = await github_handler.handle_pr(payload)
    
    # Verify the existing task was cancelled
    assert existing_task.cancelled()
    assert github_handler.running_tasks[1] == new_task

@pytest.mark.asyncio
async def test_handle_pr_with_completed_existing_task(github_handler: GitHubPRHandler) -> None:
    payload = {
        "pull_request": {"number": 1},
        "repository": {"full_name": "test/repo"}
    }
    
    # Create a mock task that's already done
    mock_task = AsyncMock()
    mock_task.done.return_value = True
    mock_task.cancel = Mock()
    
    # Set up the existing task
    github_handler.running_tasks[1] = mock_task
    
    # Mock the process_pr method
    github_handler.process_pr = AsyncMock()
    
    resp = await github_handler.handle_pr(payload)
    
    # Verify the existing task was not cancelled
    mock_task.cancel.assert_not_called()
    # Verify a new task was created
    assert 1 in github_handler.running_tasks

@pytest.mark.asyncio
async def test_handle_pr_with_invalid_payload(github_handler: GitHubPRHandler) -> None:
    payload = {}  # Invalid payload missing required fields
    
    with pytest.raises(KeyError):
        resp = await github_handler.handle_pr(payload)