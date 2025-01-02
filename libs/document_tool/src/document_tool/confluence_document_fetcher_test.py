from datetime import datetime
from typing import Dict, Any, Generator
import pytest
from unittest.mock import Mock, patch
from urllib3.exceptions import HTTPError

from document_tool.confluence_document_fetcher import ConfluenceDocumentFetcher
from document_tool.models.document import Document

@pytest.fixture
def mock_confluence() ->  Generator[Mock, None, None]:
    with patch('document_tool.confluence_document_fetcher.Confluence') as mock:
        yield mock.return_value

@pytest.fixture
def fetcher(mock_confluence: Mock) -> ConfluenceDocumentFetcher:
    return ConfluenceDocumentFetcher(
        url="https://example.atlassian.net",
        username="test_user",
        api_token="test_token"
    )


def test_get_user_documents_success(fetcher: ConfluenceDocumentFetcher, mock_confluence: Mock) -> None:
    """Test successful retrieval of user documents."""
    mock_response: Dict[str, Any] = {
        "results": [{
            "content": {
                "id": "123",
                "title": "Test Page",
                "space": {"key": "TEST"},
                "_links": {"webui": "/test-page"}
            },
            "lastModified": "2024-03-20T10:00:00.000Z"
        }]
    }
    mock_confluence.cql.return_value = mock_response
    
    # Mock the page content retrieval
    mock_confluence.get_page_by_id.return_value = {
        "body": {
            "storage": {
                "value": "Test content"
            }
        }
    }

    documents = fetcher.get_user_documents(
        username="test_user",
        start_date=datetime(2024, 1, 1),
        space_key="TEST"
    )

    assert len(documents) == 1
    assert isinstance(documents[0], Document)
    assert documents[0].id == "123"
    assert documents[0].title == "Test Page"
    assert documents[0].space == "TEST"
    
    # Test content loading
    assert documents[0].content == "Test content"

def test_get_user_documents_http_error(fetcher: ConfluenceDocumentFetcher, mock_confluence: Mock) -> None:
    """Test HTTP error handling in get_user_documents."""
    mock_confluence.cql.side_effect = HTTPError("HTTP Error")

    with pytest.raises(ConnectionError) as exc_info:
        fetcher.get_user_documents(
            username="test_user",
            start_date=datetime(2024, 1, 1)
        )
    assert "HTTP error occurred while fetching pages" in str(exc_info.value)

def test_get_user_documents_invalid_response(fetcher: ConfluenceDocumentFetcher, mock_confluence: Mock) -> None:
    """Test handling of invalid response format."""
    mock_confluence.cql.return_value = None  # Invalid response

    documents = fetcher.get_user_documents(
        username="test_user",
        start_date=datetime(2024, 1, 1)
    )
    
    assert documents == []

def test_content_loader_error(fetcher: ConfluenceDocumentFetcher, mock_confluence: Mock) -> None:
    """Test error handling in content loader."""
    mock_response: Dict[str, Any] = {
        "results": [{
            "content": {
                "id": "123",
                "title": "Test Page",
                "space": {"key": "TEST"},
                "_links": {"webui": "/test-page"}
            },
            "lastModified": "2024-03-20T10:00:00.000Z"
        }]
    }
    mock_confluence.cql.return_value = mock_response
    mock_confluence.get_page_by_id.side_effect = Exception("Failed to load content")

    documents = fetcher.get_user_documents(
        username="test_user",
        start_date=datetime(2024, 1, 1)
    )

    with pytest.raises(RuntimeError) as exc_info:
        documents[0].content
    assert "Failed to load page content" in str(exc_info.value)