import sys
from typing import Optional
from datetime import datetime
from loguru import logger
from code_analysis_tool.github_client import GitHubClient

def display_user_info(github_client: GitHubClient, user_id: str) -> None:
    try:
        user = github_client.get_user_by_id(user_id)
        if user:
            logger.info(f"\nUser Information:")
            logger.info(f"Name: {user.name or 'N/A'}")
            logger.info(f"Login: {user.login}")
            logger.info(f"Email: {user.email or 'N/A'}")
    except Exception as e:
        logger.error(f"Failed to fetch user information: {str(e)}")

def display_repository_info(github_client: GitHubClient, user_id: str) -> None:
    try:
        repos = github_client.get_user_repositories(user_id)
        logger.info(f"\nRepositories for {user_id}:")
        for repo in repos:
            logger.info(f"- {repo.full_name} {'(Private)' if repo.private else '(Public)'}")
            if repo.description:
                logger.info(f"  Description: {repo.description}")
    except Exception as e:
        logger.error(f"Failed to fetch repositories: {str(e)}")

def display_pull_requests(github_client: GitHubClient, repo_name: str, since_date: Optional[str]) -> None:
    try:
        merged_prs = github_client.get_merged_pull_requests(repo_name, since_date)
        logger.info(f"\nMerged PRs in {repo_name} since {since_date or 'all time'}:")
        for pr in merged_prs:
            logger.info(f"\n#{pr.number}: {pr.title}")
            logger.info(f"Merged at: {pr.merged_at}")
            logger.info(f"Author: {pr.author.login}")
            
            if pr.description:
                logger.info(f"Description: {pr.description[:100]}...")
            
            if pr.file_diffs:
                logger.info("Files changed:")
                for filename, diff in pr.file_diffs.items():
                    logger.info(f"- {filename}")
                    logger.info(f"- {diff}")
    except Exception as e:
        logger.error(f"Failed to fetch pull requests: {str(e)}")

def main() -> None:
    try:
        if len(sys.argv) < 2:
            logger.error("Need github token: python main.py <token>")
            sys.exit(1)
        
        token: str = sys.argv[1]
        github_client = GitHubClient(token)
        
        # Example user ID - replace with actual username
        user_id: str = "serinth"
        since_date: str = "2024-01-01"
        
        # Display user information
        display_user_info(github_client, user_id)
        
        # Display repositories
        display_repository_info(github_client, user_id)
        
        # Display PRs for a specific repository
        example_repo: str = "serinth/python-quart-boilerplate"
        display_pull_requests(github_client, example_repo, since_date)
        
        # Bonus: Display all PRs across all repositories for the user
        # logger.info("\nFetching all PRs across all repositories...")
        # all_user_prs = github_client.get_merged_pull_requests_for_user(user_id, since_date)
        # logger.info(f"Total PRs found across all repositories: {len(all_user_prs)}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("GitHub Repository Analysis Tool")
    main()
