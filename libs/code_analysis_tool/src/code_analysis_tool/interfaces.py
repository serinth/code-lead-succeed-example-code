from abc import ABC, abstractmethod
from typing import List, Optional
from code_analysis_tool.models.repository import Repository
from code_analysis_tool.models.pull_request import PullRequest
from code_analysis_tool.models.user import User

class SourceControlFetcher(ABC):
    """Interface for source control operations."""
    
    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by their ID."""
        pass
    
    @abstractmethod
    def get_user_repositories(self, user_id: str) -> List[Repository]:
        """Get all repositories that a user contributes to."""
        pass
    
    @abstractmethod
    def get_merged_pull_requests(
        self, 
        repo_name: str, 
        since_date: Optional[str] = None
    ) -> List[PullRequest]:
        """Get merged pull requests from a repository."""
        pass
    
    @abstractmethod
    def get_merged_pull_requests_for_user(
        self, 
        user_id: str, 
        since_date: Optional[str] = None
    ) -> List[PullRequest]:
        """Get merged pull requests from all repositories of a user."""
        pass 