from typing import List, Dict, Optional
from datetime import datetime
from atlassian import Confluence
from urllib3.exceptions import HTTPError
from loguru import logging
from document_tool.interfaces import DesignDocumentFetcher

class ConfluenceDocumentFetcher(DesignDocumentFetcher):
    def __init__(self, url: str, username: str, api_token: str) -> None:
        """Initialize the Confluence client.

        Args:
            url: Base URL of the Confluence instance
            username: Confluence username
            api_token: Confluence API token
        """
        try:
            self.confluence = Confluence(
                url=url,
                username=username,
                password=api_token,
                cloud=True  # Set to False if using Server/Data Center
            )
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Confluence client: {str(e)}")

    def get_user_documents(
        self, 
        user_email: str, 
        start_date: datetime,
        space_key: Optional[str] = None
    ) -> List[Dict]:
        """Fetch pages created by a specific user after a given date.

        Args:
            user_email: Email address of the user
            start_date: Datetime object representing the start date
            space_key: Optional space key to limit the search to a specific space

        Returns:
            List of dictionaries containing page information
        """
        try:
            cql = f'creator = "{user_email}" and created >= "{start_date.strftime("%Y-%m-%d")}"'
            if space_key:
                cql += f' and space = "{space_key}"'

            search_results = self.confluence.cql(cql, limit=100)
        except HTTPError as e:
            raise ConnectionError(f"HTTP error occurred while fetching pages: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error fetching pages: {str(e)}")    
        
        if not isinstance(search_results, dict):
            logging.warn(f"Search results didn't return a dict as expected. Got: {search_results}")
            return []

        pages = []
        for result in search_results.get("results", []):
            page_info = {
                "id": result.get("content", {}).get("id"),
                "title": result.get("content", {}).get("title"),
                "space": result.get("content", {}).get("space", {}).get("key"),
                "created": result.get("content", {}).get("created"),
                "url": result.get("content", {}).get("_links", {}).get("webui")
            }
            pages.append(page_info)

        return pages


