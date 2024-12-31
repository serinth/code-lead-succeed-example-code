import sys
from github_tool.github_client import GitHubClient
from github_tool.pull_request_utils import get_raw_diff

def main() -> None:
    token = sys.argv[1]
    if not token:
        print("Need github token: uv run main.py <token>")
        exit(1)
    
    try:
        github_integration = GitHubClient(token)
        
        # Example: Get repositories for a user by ID
        user_id = "serinth"  # Replace with the actual user ID
        repos = github_integration.get_user_repositories(user_id)
        print(f"Repositories for {user_id}:")
        for repo in repos:
            print(f"- {repo.full_name}")
        
        # Example: Get merged PRs since a specific date
        repo_name = "serinth/python-quart-boilerplate"
        since_date = "2024-01-01"
        merged_prs = github_integration.get_merged_pull_requests(repo_name, since_date)
        print(f"\nMerged PRs in {repo_name} since {since_date}:")
        for pr in merged_prs:
            print(f"- #{pr.number}: {pr.title} (merged at: {pr.merged_at})")
            commits = pr.get_commits()
            for c in commits:
                print(f"Commit message: {c.commit.message}")
            diff = get_raw_diff(pr)
            for k, v in diff.items():
                print(f"file: {k} has diff: {v}\n")

            
            
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    print("Lists all repos, picks one then gets its a couple of PRs, shows commit messages and diffs of each file")
    main()
