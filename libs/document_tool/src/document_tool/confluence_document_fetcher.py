from typing import List, Optional
from datetime import datetime
from atlassian import Confluence
from urllib3.exceptions import HTTPError
from loguru import logger
from document_tool.interfaces import DesignDocumentFetcher
from document_tool.models.document import Document

class ConfluenceDocumentFetcher(DesignDocumentFetcher):
    def __init__(self, url: str, username: str, api_token: str) -> None:
        """Initialize the Confluence client.

        Args:
            url: Base URL of the Confluence instance
            username: Confluence username
            api_token: Confluence API token
        """
        
        self.confluence = Confluence(
            url=url,
            username=username,
            password=api_token,
            cloud=True  # Set to False if using Server/Data Center
        )

    def get_user_documents(
        self, 
        username: str, 
        start_date: datetime,
        space_key: Optional[str] = None
    ) -> List[Document]:
        """Fetch pages created by a specific user after a given date.

        Args:
            username: Confluence username for the user (not email)
            start_date: Datetime object representing the start date
            space_key: Optional space key to limit the search to a specific space

        Returns:
            List of Document objects containing page information
        """
        try:
            #cql = f'created >= "{start_date.strftime("%Y-%m-%d")}" and type=page'
            cql = f'contributor = {username} and created >= "{start_date.strftime("%Y-%m-%d")}" and type=page'
            if space_key:
                cql += f' and space = "{space_key}"'

            search_results = self.confluence.cql(cql, limit=100)
            logger.debug(search_results)
        except HTTPError as e:
            raise ConnectionError(f"HTTP error occurred while fetching pages: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error fetching pages: {str(e)}")    
        
        if not isinstance(search_results, dict):
            logger.warning(f"Search results didn't return a dict as expected. Got: {search_results}")
            return []

        documents = []
        for result in search_results.get("results", []):
            logger.debug(result)
            content_data = result.get("content", {})
            def create_content_loader(page_id: str):
                def load_content() -> str:
                    try:
                        page = self.confluence.get_page_by_id(page_id, expand='body.storage')
                        return page.get('body', {}).get('storage', {}).get('value', '')
                    except Exception as e:
                        raise RuntimeError(f"Failed to load page content: {str(e)}")
                return load_content

            document = Document(
                id=content_data.get("id", ""),
                title=content_data.get("title", ""),
                space=content_data.get("space", {}).get("key", ""),
                last_modified=datetime.strptime(result.get("lastModified", "2025-01-01T05:22:33.000Z"), "%Y-%m-%dT%H:%M:%S.%fZ"),
                url=content_data.get("_links", {}).get("webui", ""),
                _content_loader=create_content_loader(content_data.get("id", ""))
            )
            documents.append(document)

        return documents


