from typing import List, Optional
from loguru import logger

from github import Github, Auth
from github.PaginatedList import PaginatedList
from github.Repository import Repository as GithubRepository
from github.PullRequest import PullRequest as GithubPullRequest
from github.NamedUser import NamedUser
from dateutil.parser import parse

from code_analysis_tool.interfaces import SourceControlFetcher
from code_analysis_tool.models.repository import Repository
from code_analysis_tool.models.pull_request import PullRequest
from code_analysis_tool.models.user import User
from .pull_request_utils import get_raw_diff

class GitHubClient(SourceControlFetcher):
    def __init__(self, access_token: str) -> None:
        auth = Auth.Token(access_token)
        self.github = Github(auth=auth)

    def _convert_user(self, github_user: NamedUser) -> User:
        """Convert GitHub user to platform-agnostic User model."""
        return User(
            id=str(github_user.id),
            login=github_user.login,
            name=github_user.name,
            email=github_user.email
        )

    def _convert_repository(self, github_repo: GithubRepository) -> Repository:
        """Convert GitHub repository to platform-agnostic Repository model."""
        return Repository(
            id=str(github_repo.id),
            name=github_repo.name,
            full_name=github_repo.full_name,
            owner=self._convert_user(github_repo.owner),
            description=github_repo.description,
            private=github_repo.private
        )

    def _convert_pull_request(self, github_pr: GithubPullRequest) -> PullRequest:
        """Convert GitHub pull request to platform-agnostic PullRequest model."""
        try:
            file_diffs = get_raw_diff(github_pr)
        except Exception as e:
            # If we fail to get diffs, log the error but continue with empty diffs
            logger.warn(f"Warning: Failed to get diffs for PR #{github_pr.number}: {str(e)}")
            file_diffs = {}

        return PullRequest(
            id=str(github_pr.id),
            number=github_pr.number,
            title=github_pr.title,
            author=self._convert_user(github_pr.user),
            repository=self._convert_repository(github_pr.base.repo),
            created_at=github_pr.created_at,
            merged_at=github_pr.merged_at,
            merged=github_pr.merged,
            description=github_pr.body,
            file_diffs=file_diffs
        )

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            github_user = self.github.get_user(user_id)
            return self._convert_user(github_user)
        except Exception as e:
            raise Exception(f"Failed to find user with ID {user_id}: {str(e)}")

    def get_user_repositories(self, user_id: str) -> List[Repository]:
        try:
            user = self.github.get_user(user_id)
            if not user:
                raise Exception(f"No GitHub user found with ID: {user_id}")
            
            return [self._convert_repository(repo) for repo in user.get_repos()]
        except Exception as e:
            raise Exception(f"Failed to fetch repositories for user ID {user_id}: {str(e)}")

    def get_merged_pull_requests(
        self, 
        repo_name: str, 
        since_date: Optional[str] = None
    ) -> List[PullRequest]:
        try:
            repo = self.github.get_repo(repo_name)
            pulls: PaginatedList[GithubPullRequest] = repo.get_pulls(state="closed", sort="updated", direction="desc")
            
            merged_pulls = []
            for pr in pulls:
                if not pr.merged:
                    continue
                if since_date:
                    since_datetime = parse(since_date).astimezone()
                    if pr.merged_at < since_datetime.astimezone(pr.merged_at.tzinfo):
                        break
                
                merged_pulls.append(self._convert_pull_request(pr))
            
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
        try:
            repositories = self.get_user_repositories(user_id)
            all_merged_pulls = []
            
            for repo in repositories:
                merged_pulls = self.get_merged_pull_requests(repo.full_name, since_date)
                all_merged_pulls.extend(merged_pulls)
            
            return all_merged_pulls
        except Exception as e:
            raise Exception(f"Failed to fetch merged pull requests for user ID {user_id}: {str(e)}")
