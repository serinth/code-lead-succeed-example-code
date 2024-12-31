from typing import List, Optional

from github import Github, Auth
from github.PaginatedList import PaginatedList
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.NamedUser import NamedUser
from dateutil.parser import parse


class GitHubClient:
    def __init__(self, access_token: str) -> None:
        auth = Auth.Token(access_token)
        self.github = Github(auth=auth)

    def get_user_by_id(self, user_id: str) -> Optional[NamedUser]:
        """
        Get GitHub user by user ID.
        
        Args:
            user_id: User's GitHub ID
        
        Returns:
            NamedUser object if found, None otherwise
        """
        try:
            return self.github.get_user(user_id)
        except Exception as e:
            raise Exception(f"Failed to find user with ID {user_id}: {str(e)}")

    def get_user_repositories(self, user_id: str) -> List[Repository]:
        """
        Get all repositories that a user contributes to based on their user ID.
        
        Args:
            user_id: User's GitHub ID
        
        Returns:
            List of Repository objects
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise Exception(f"No GitHub user found with ID: {user_id}")
        
            return list(user.get_repos())
        except Exception as e:
            raise Exception(f"Failed to fetch repositories for user ID {user_id}: {str(e)}")

    def get_merged_pull_requests(
        self, 
        repo_name: str, 
        since_date: Optional[str] = None
    ) -> List[PullRequest]:
        """
        Get merged pull requests from a repository, optionally filtered by date.
        
        Args:
            repo_name: Full repository name (e.g., "owner/repo")
            since_date: Optional date string in any standard format (e.g., "2024-01-01")
        
        Returns:
            List of PullRequest objects
        """
        try:
            repo = self.github.get_repo(repo_name)
            pulls: PaginatedList[PullRequest] = repo.get_pulls(state="closed", sort="updated", direction="desc")
            
            merged_pulls = []
            for pr in pulls:
                if not pr.merged:
                    continue
                if since_date:
                    since_datetime = parse(since_date).astimezone()
                    if pr.merged_at < since_datetime.astimezone(pr.merged_at.tzinfo):
                        break
                
                merged_pulls.append(pr)
            
            return merged_pulls
        except ValueError as e:
            raise ValueError(f"Value error, potential issue in date format: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to fetch pull requests for repository {repo_name}: {str(e)}")

    def get_merged_pull_requests_for_user(
        self, 
        user_id: str, 
        since_date: Optional[str] = None
    ) -> List[PullRequest]:
        """
        Get merged pull requests from all repositories of a user, optionally filtered by date.
        
        Args:
            user_id: User's GitHub ID
            since_date: Optional date string in any standard format (e.g., "2024-01-01")
        
        Returns:
            List of PullRequest objects from all repositories
        """
        try:
            repositories = self.get_user_repositories(user_id)
            all_merged_pulls = []
            
            for repo in repositories:
                merged_pulls = self.get_merged_pull_requests(repo.full_name, since_date)
                all_merged_pulls.extend(merged_pulls)
            
            return all_merged_pulls
        except Exception as e:
            raise Exception(f"Failed to fetch merged pull requests for user ID {user_id}: {str(e)}")
