from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime
from typing import Optional

class DesignDocumentFetcher(ABC):
    """Interface for fetching design documents from various sources."""
    
    @abstractmethod
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
        pass 