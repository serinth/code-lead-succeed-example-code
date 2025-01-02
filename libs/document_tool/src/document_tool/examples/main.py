import sys
from datetime import datetime, timedelta
from typing import List
from document_tool.models.document import Document
from document_tool.confluence_document_fetcher import ConfluenceDocumentFetcher


def main() -> None:
    try:
        # Get credentials from environment variables
        confluence_url = sys.argv[1]
        confluence_username = sys.argv[2]
        confluence_token = sys.argv[3]

        if not all([confluence_url, confluence_username, confluence_token]):
            raise ValueError("Missing required environment variables for Confluence connection")

        # Initialize the document fetcher
        fetcher = ConfluenceDocumentFetcher(
            url=confluence_url,
            username=confluence_username,
            api_token=confluence_token,
        )

        # Get documents from the last 7 days
        start_date = datetime.now() - timedelta(days=7)
        documents: List[Document] = fetcher.get_user_documents(
            username="serinth",
            start_date=start_date,
            #space_key="~557058832cb5f7489444eca286d01aa86127f5"
        )

        # Print document information
        print(f"Found {len(documents)} documents:")
        for doc in documents:
            print(f"\nTitle: {doc.title}")
            print(f"Space: {doc.space}")
            print(f"Last Modified: {doc.last_modified}")
            print(f"URL: {doc.url}")
            print("First 100 chars of content:")
            print(f"{doc.content[:100]}...")

    except Exception as e:
        print(f"Error running example: {str(e)}")

if __name__ == "__main__":
    main()
